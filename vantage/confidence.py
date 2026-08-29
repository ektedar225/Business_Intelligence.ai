"""L6 — Confidence & Abstention Gate. Five named components combine into one banded
composite score; three distinct abstention behaviours ship real value instead of a
bare refusal. Abstaining is a feature, not a failure mode — every abstention states
what is missing and what would resolve it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from vantage.evidence import ConfidenceBreakdown, EvidenceFact

WEIGHTS = {"data": 0.25, "method": 0.20, "coverage": 0.25, "consistency": 0.15, "history": 0.15}

BAND_THRESHOLDS = [("high", 0.85), ("medium", 0.65), ("low", 0.40)]


def band_for(composite: float, hard_abstain: bool) -> str:
    if hard_abstain:
        return "abstain"
    for name, threshold in BAND_THRESHOLDS:
        if composite >= threshold:
            return name
    return "abstain"


CAP_CEILINGS = {"low": 0.649, "medium": 0.849}


def compute_confidence(
    facts: list[EvidenceFact],
    residual_share: float,
    history_periods: int,
    min_history_periods: int,
    data_quality_flags: list[str],
    contradictions: int = 0,
    hard_abstain: bool = False,
    confidence_cap: Optional[str] = None,
) -> ConfidenceBreakdown:
    data_conf = 1.0 - min(1.0, 0.5 * len(data_quality_flags))
    method_conf = (
        sum(f.method_confidence * abs(f.value) for f in facts) / sum(abs(f.value) for f in facts)
        if facts
        else 0.5
    )
    coverage_conf = max(0.0, 1.0 - min(1.0, abs(residual_share)))
    consistency_conf = max(0.0, 1.0 - 0.3 * contradictions)
    history_conf = min(1.0, history_periods / min_history_periods) if min_history_periods else 1.0

    composite = (
        WEIGHTS["data"] * data_conf
        + WEIGHTS["method"] * method_conf
        + WEIGHTS["coverage"] * coverage_conf
        + WEIGHTS["consistency"] * consistency_conf
        + WEIGHTS["history"] * history_conf
    )
    if confidence_cap and confidence_cap in CAP_CEILINGS:
        composite = min(composite, CAP_CEILINGS[confidence_cap])
    if hard_abstain:
        composite = min(composite, 0.30)
    composite = round(composite, 3)
    band = band_for(composite, hard_abstain)
    return ConfidenceBreakdown(
        data=round(data_conf, 3),
        method=round(method_conf, 3),
        coverage=round(coverage_conf, 3),
        consistency=round(consistency_conf, 3),
        history=round(history_conf, 3),
        composite=composite,
        band=band,
    )


@dataclass
class AbstentionResult:
    mode: Literal["A_clarify", "B_competing_hypotheses", "C_hard_abstain"]
    reliable_findings: str
    blocker: str
    why_it_matters: str
    resolution_path: str
    eta_or_owner: str
    what_you_can_still_do: str
    competing_hypotheses: list[dict] = field(default_factory=list)
    clarifying_question: Optional[str] = None


def clarify_ambiguous_kpi(term: str, candidates: list[str]) -> AbstentionResult:
    return AbstentionResult(
        mode="A_clarify",
        reliable_findings="No analysis run yet — the KPI reference needs to be resolved first.",
        blocker=f"'{term}' maps to more than one registered KPI: {', '.join(candidates)}.",
        why_it_matters="Answering against the wrong KPI definition would be confidently wrong, not just imprecise.",
        resolution_path="Pick one of the candidate KPIs, or rename one in the contract registry if the ambiguity is a naming collision.",
        eta_or_owner="immediate — resolved by your next reply",
        what_you_can_still_do="You can also ask to see both KPIs' definitions side by side before choosing.",
        clarifying_question=f"'{term}' could mean {' or '.join(candidates)} — which one did you mean?",
    )


def hard_abstain_stale_source(
    kpi_id: str,
    source: str,
    lag_hours: float,
    sla_hours: float,
    owner: str,
    reliable_findings: str,
) -> AbstentionResult:
    return AbstentionResult(
        mode="C_hard_abstain",
        reliable_findings=reliable_findings,
        blocker=f"{source} feed for {kpi_id} is {lag_hours:.0f}h stale against a {sla_hours:.0f}h freshness SLA.",
        why_it_matters="Computing this KPI on stale cost data would silently corrupt the answer rather than degrade it visibly.",
        resolution_path=f"Refresh the {source} feed; the affected driver will automatically re-verify once the SLA is met.",
        eta_or_owner=owner,
        what_you_can_still_do="The revenue-side facts (not dependent on this feed) are still reliable and shown above.",
    )


def competing_hypotheses(hypotheses: list[dict]) -> AbstentionResult:
    return AbstentionResult(
        mode="B_competing_hypotheses",
        reliable_findings="The movement is material and confirmed, but two methods disagree on the dominant driver.",
        blocker="Contribution analysis and event-join evidence point to different top drivers with comparable support.",
        why_it_matters="Picking one narrative arbitrarily would look authoritative while being a coin flip.",
        resolution_path="Run the discriminating test named in each hypothesis to break the tie.",
        eta_or_owner="analyst review",
        what_you_can_still_do="Both hypotheses are shown below with equal prominence — neither is pre-ranked.",
        competing_hypotheses=hypotheses,
    )
