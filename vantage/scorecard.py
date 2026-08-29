"""Recovery Scorecard. Scenario 1's data was generated with known, injected drivers;
this measures whether the diagnosis engine actually finds what was put in, rather
than merely sounding plausible. These are real numbers computed from the actual
pipeline output against the actual generation parameters — not asserted.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from vantage.evidence import EvidenceBundle

DATA_DIR = Path(__file__).parent.parent / "data"

NAMED_DRIVERS = ["promo_calendar", "stockout_rate", "channel_mix"]


def _spearman(x: list[float], y: list[float]) -> float:
    if len(x) < 2:
        return float("nan")
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def recovery_scorecard(bundle: EvidenceBundle) -> dict:
    ground_truth = json.loads((DATA_DIR / "ground_truth.json").read_text())["ground_truth"]
    true_by_driver = {d["driver_id"]: d for d in ground_truth["drivers"]}

    diagnosed = {
        f.driver_id: f
        for f in bundle.facts
        if f.statement_type == "driver_attribution" and f.driver_id in NAMED_DRIVERS
    }

    ranked_true = sorted(NAMED_DRIVERS, key=lambda d: abs(true_by_driver[d]["true_share"]), reverse=True)
    ranked_diagnosed = sorted(diagnosed.keys(), key=lambda d: abs(diagnosed[d].contribution_share or 0), reverse=True)

    top3_found = sum(1 for d in NAMED_DRIVERS if d in diagnosed)
    recall_at_3 = top3_found / len(NAMED_DRIVERS)

    true_shares = [true_by_driver[d]["true_share"] for d in NAMED_DRIVERS]
    diag_shares = [diagnosed[d].contribution_share if d in diagnosed else 0.0 for d in NAMED_DRIVERS]
    rank_corr = _spearman(true_shares, diag_shares)

    abs_errors_pp = [abs(t - d) * 100 for t, d in zip(true_shares, diag_shares)]
    mae_pp = float(np.mean(abs_errors_pp))

    true_noise_share = true_by_driver.get("noise", {}).get("true_share", 0.0)
    residual_fact = next((f for f in bundle.facts if f.driver_id == "residual"), None)
    diagnosed_residual_share = residual_fact.contribution_share if residual_fact else bundle.residual.get("residual_share", 0.0)
    residual_error_pp = abs(true_noise_share - diagnosed_residual_share) * 100

    return {
        "driver_recall_at_3": recall_at_3,
        "driver_recall_at_3_label": f"{top3_found}/{len(NAMED_DRIVERS)}",
        "rank_correlation_spearman": round(rank_corr, 3) if rank_corr == rank_corr else None,
        "attribution_mae_pp": round(mae_pp, 2),
        "attribution_mae_target_pp": 5.0,
        "residual_error_pp": round(residual_error_pp, 2),
        "residual_error_target_pp": 3.0,
        "ranked_true": ranked_true,
        "ranked_diagnosed": ranked_diagnosed,
        "per_driver": [
            {
                "driver_id": d,
                "true_share_pct": round(true_by_driver[d]["true_share"] * 100, 1),
                "diagnosed_share_pct": round((diagnosed[d].contribution_share or 0.0) * 100, 1) if d in diagnosed else None,
                "true_dollar": round(true_by_driver[d]["true_dollar_impact"], 0),
                "diagnosed_dollar": round(diagnosed[d].value, 0) if d in diagnosed else None,
            }
            for d in NAMED_DRIVERS
        ],
        "noise": {
            "true_share_pct": round(true_noise_share * 100, 1),
            "diagnosed_residual_share_pct": round(diagnosed_residual_share * 100, 1),
        },
    }


def firewall_violation_count(results: list) -> dict:
    total = len(results)
    violations = sum(1 for v in results if not v.passed)
    return {"narratives_checked": total, "firewall_violations": violations, "target": 0}
