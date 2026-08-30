"""Drift Detection — two flavours of drift monitoring that address the most common
failure modes in production BI pipelines.

1. Data Drift (PSI): Population Stability Index between two windows of a KPI series.
   PSI < 0.10 → stable, 0.10-0.25 → slight drift, > 0.25 → significant shift.

2. Driver Rank Drift: Spearman rank correlation across the last N snapshots of
   learned driver acceptance weights. If the top-ranked drivers are flipping, the
   model's implicit world-view is drifting even if raw numbers look stable.

Both return DriftReport objects with a human-readable alert_level so the caller
(API layer) doesn't need to interpret PSI thresholds.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DriftReport:
    metric: str
    method: Literal["psi", "rank_correlation"]
    window_a_label: str
    window_b_label: str
    score: float
    alert_level: Literal["stable", "slight", "significant"]
    interpretation: str
    recommendation: str
    component_scores: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# PSI helpers
# ---------------------------------------------------------------------------

PSI_THRESHOLDS = [
    ("significant", 0.25),
    ("slight", 0.10),
    ("stable", 0.0),
]


def _psi_alert(psi: float) -> str:
    for label, threshold in PSI_THRESHOLDS:
        if psi >= threshold:
            return label
    return "stable"


def _psi_interpretation(psi: float, metric: str) -> str:
    level = _psi_alert(psi)
    if level == "stable":
        return f"{metric} distribution is stable across the two windows (PSI={psi:.3f} < 0.10)."
    if level == "slight":
        return f"{metric} shows slight distribution shift (PSI={psi:.3f}). Monitor for continuation."
    return (
        f"{metric} has drifted significantly (PSI={psi:.3f} > 0.25). "
        "Root cause investigation recommended before trusting seasonal baselines."
    )


def _bucket_psi(vals_a: list[float], vals_b: list[float], n_buckets: int = 10) -> tuple[float, dict]:
    """Compute PSI between two distributions using equal-width buckets across combined range."""
    all_vals = vals_a + vals_b
    if not all_vals or len(vals_a) < 2 or len(vals_b) < 2:
        return 0.0, {}

    mn, mx = min(all_vals), max(all_vals)
    if mn == mx:
        return 0.0, {}

    width = (mx - mn) / n_buckets
    buckets = [mn + i * width for i in range(n_buckets + 1)]

    def bin_counts(vals: list[float]) -> list[float]:
        counts = [0.0] * n_buckets
        for v in vals:
            idx = min(int((v - mn) / width), n_buckets - 1)
            counts[idx] += 1
        total = sum(counts)
        return [max(c / total, 1e-6) for c in counts]  # avoid log(0)

    pcts_a = bin_counts(vals_a)
    pcts_b = bin_counts(vals_b)
    psi = sum((b - a) * math.log(b / a) for a, b in zip(pcts_a, pcts_b))
    component = {f"bucket_{i}": round(psi_i, 4) for i, psi_i in
                 enumerate((b - a) * math.log(b / a) for a, b in zip(pcts_a, pcts_b))}
    return round(psi, 4), component


# ---------------------------------------------------------------------------
# Public: Data Drift
# ---------------------------------------------------------------------------


def detect_data_drift(
    series_a: list[float],
    series_b: list[float],
    metric: str = "kpi_value",
    label_a: str = "window_A",
    label_b: str = "window_B",
) -> DriftReport:
    """PSI-based data drift between two windows of a numeric KPI series."""
    psi, components = _bucket_psi(series_a, series_b)
    level = _psi_alert(psi)
    return DriftReport(
        metric=metric,
        method="psi",
        window_a_label=label_a,
        window_b_label=label_b,
        score=psi,
        alert_level=level,
        interpretation=_psi_interpretation(psi, metric),
        recommendation=(
            "No action required." if level == "stable"
            else "Recalibrate seasonal baseline and re-check materiality thresholds."
            if level == "slight"
            else "Pause auto-recommendations; conduct root-cause analysis on distribution shift."
        ),
        component_scores=components,
    )


# ---------------------------------------------------------------------------
# Spearman helpers
# ---------------------------------------------------------------------------


def _spearman(ranks_a: list[int], ranks_b: list[int]) -> float:
    n = len(ranks_a)
    if n < 2:
        return 1.0
    d_sq = sum((a - b) ** 2 for a, b in zip(ranks_a, ranks_b))
    return round(1 - (6 * d_sq) / (n * (n ** 2 - 1)), 4)


def _weight_dict_to_ranks(weights: dict[str, float], all_keys: list[str]) -> list[int]:
    ordered = sorted(all_keys, key=lambda k: weights.get(k, 0.5), reverse=True)
    return [ordered.index(k) + 1 for k in all_keys]


# ---------------------------------------------------------------------------
# Public: Driver Rank Drift
# ---------------------------------------------------------------------------


def detect_driver_rank_drift(
    weight_snapshots: list[dict[str, float]],
    label_a: str = "snapshot_T-1",
    label_b: str = "snapshot_T",
) -> DriftReport:
    """Spearman rank correlation between first and last weight snapshots.
    weight_snapshots: list of {driver_id -> posterior_weight} dicts, oldest first.
    """
    if len(weight_snapshots) < 2:
        return DriftReport(
            metric="driver_ranking",
            method="rank_correlation",
            window_a_label=label_a,
            window_b_label=label_b,
            score=1.0,
            alert_level="stable",
            interpretation="Only one snapshot available — no drift computable yet.",
            recommendation="Collect at least 2 feedback snapshots to enable drift detection.",
        )
    snap_a = weight_snapshots[0]
    snap_b = weight_snapshots[-1]
    all_keys = sorted(set(snap_a) | set(snap_b))
    ranks_a = _weight_dict_to_ranks(snap_a, all_keys)
    ranks_b = _weight_dict_to_ranks(snap_b, all_keys)
    rho = _spearman(ranks_a, ranks_b)

    # Interpret: rho < 0.7 = significant rank drift
    if rho >= 0.9:
        level, interp = "stable", f"Driver ranking is stable (ρ={rho:.3f})."
    elif rho >= 0.7:
        level, interp = "slight", f"Minor driver ranking shift (ρ={rho:.3f}). Review recent feedback signals."
    else:
        level, interp = "significant", (
            f"Driver ranking has drifted significantly (ρ={rho:.3f}). "
            "Top-ranked drivers have changed. Analyst review of feedback weights is recommended."
        )

    return DriftReport(
        metric="driver_ranking",
        method="rank_correlation",
        window_a_label=label_a,
        window_b_label=label_b,
        score=rho,
        alert_level=level,
        interpretation=interp,
        recommendation=(
            "No action required." if level == "stable"
            else "Run discriminating test to confirm rank stability."
            if level == "slight"
            else "Freeze auto-recommendations and trigger an analyst review loop."
        ),
        component_scores={"drivers": all_keys, "ranks_a": ranks_a, "ranks_b": ranks_b},
    )
