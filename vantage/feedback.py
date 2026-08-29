"""L8 feedback loop, driver-ranking arm. An analyst's accept/reject on a specific
driver is routed and persisted, then folded into a per-driver acceptance weight via a
Beta-Bernoulli posterior mean — a simplified, honestly-labeled stand-in for the
learn-to-rank model the full design calls for, but a real, working update rule rather
than a mocked one: reject a driver enough times and it actually ranks lower next run.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from vantage.evidence import EvidenceFact

DATA_DIR = Path(__file__).parent.parent / "data"
FEEDBACK_LOG = DATA_DIR / "feedback_log.jsonl"
WEIGHTS_PATH = DATA_DIR / "driver_weights.json"

REGISTERED_DRIVER_IDS = {
    "promo_calendar", "stockout_rate", "channel_mix", "competitor_price", "seasonality",
    "unit_cost_change", "campaign_spend_change", "new_sku_launch", "residual",
}


def structure_feedback(event_id: str, driver_id: str, polarity: Literal["accept", "reject", "adjust"], analyst: str, comment: str = "") -> dict:
    """P7-style routing: an unregistered driver becomes a contract-change request, not
    a silent acceptance of a made-up driver."""
    target = "driver_ranking" if driver_id in REGISTERED_DRIVER_IDS else "contract_change_request"
    return {
        "target": target,
        "event_id": event_id,
        "driver_id": driver_id,
        "polarity": polarity,
        "analyst": analyst,
        "comment": comment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _load_weights() -> dict:
    if WEIGHTS_PATH.exists():
        return json.loads(WEIGHTS_PATH.read_text())
    return {}


def _save_weights(weights: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    WEIGHTS_PATH.write_text(json.dumps(weights, indent=2))


def submit_feedback(event_id: str, driver_id: str, polarity: Literal["accept", "reject", "adjust"], analyst: str, comment: str = "") -> dict:
    structured = structure_feedback(event_id, driver_id, polarity, analyst, comment)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_LOG, "a") as fh:
        fh.write(json.dumps(structured) + "\n")

    if structured["target"] == "driver_ranking" and polarity in ("accept", "reject"):
        weights = _load_weights()
        w = weights.get(driver_id, {"accepted": 0, "rejected": 0})
        if polarity == "accept":
            w["accepted"] += 1
        else:
            w["rejected"] += 1
        w["posterior_weight"] = round((w["accepted"] + 1) / (w["accepted"] + w["rejected"] + 2), 4)
        weights[driver_id] = w
        _save_weights(weights)
    return structured


def driver_weight(driver_id: str) -> float:
    weights = _load_weights()
    return weights.get(driver_id, {}).get("posterior_weight", 0.5)


def apply_learned_ranking(facts: list[EvidenceFact]) -> list[EvidenceFact]:
    """Re-ranks driver facts by (contribution_share magnitude x learned acceptance
    weight) instead of raw magnitude alone — a driver the analyst keeps rejecting
    drifts down the ranking even if its dollar share stays the same."""
    return sorted(
        facts,
        key=lambda f: abs(f.contribution_share or 0.0) * driver_weight(f.driver_id or ""),
        reverse=True,
    )


def read_feedback_log(limit: int = 100) -> list[dict]:
    if not FEEDBACK_LOG.exists():
        return []
    lines = FEEDBACK_LOG.read_text().strip().splitlines()
    return [json.loads(line) for line in lines[-limit:]]


def read_weights() -> dict:
    return _load_weights()
