"""Action Composer. Actions are drawn from the Lever Registry — never invented — and
filtered by the persona's decision rights. Expected impact is copied verbatim from
the registry's elasticity-derived estimate, never computed by whatever generated the
narrative. A material driver the persona cannot act on becomes an escalation, not a
fabricated sense of agency.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from vantage.evidence import EvidenceBundle, EvidenceFact
from vantage.registries import Lever, LeverRegistry, Persona


@dataclass
class Action:
    driver: str
    lever: str
    action: str
    expected_impact: dict
    owner: str
    lead_time_days: int
    confidence: str
    monitoring_plan: dict
    evidence_ids: list[str]


@dataclass
class Escalation:
    to_role: str
    reason: str
    driver: str


@dataclass
class ActionPlan:
    actions: list[Action] = field(default_factory=list)
    escalations: list[Escalation] = field(default_factory=list)


def _confidence_label(share: float) -> str:
    if abs(share) >= 0.4:
        return "high"
    if abs(share) >= 0.15:
        return "medium"
    return "low"


def compose_actions(bundle: EvidenceBundle, persona: Persona, lever_registry: LeverRegistry, max_actions: int = 3) -> ActionPlan:
    driver_facts = [
        f for f in bundle.facts
        if f.statement_type == "driver_attribution" and f.driver_id and f.driver_id not in ("residual", "unit_cost_change")
    ]
    ranked = sorted(driver_facts, key=lambda f: abs(f.contribution_share or 0.0), reverse=True)

    plan = ActionPlan()
    for f in ranked:
        lever = lever_registry.for_driver(f.driver_id) if f.driver_type == "controllable" else None
        if lever is None:
            if f.driver_type == "controllable":
                plan.escalations.append(
                    Escalation(to_role="platform-owner", reason=f"No registered lever for driver '{f.driver_id}' yet.", driver=f.driver_id)
                )
            continue
        if lever.lever_id not in persona.lever_rights:
            plan.escalations.append(
                Escalation(to_role=lever.owner_role, reason=f"'{f.label}' is material but the lever ({lever.lever_id}) is outside your decision rights.", driver=f.driver_id)
            )
            continue
        plan.actions.append(
            Action(
                driver=f.driver_id,
                lever=lever.lever_id,
                action=_action_text(lever, f),
                expected_impact={
                    "point": lever.expected_impact.point,
                    "ci": [lever.expected_impact.ci_low, lever.expected_impact.ci_high],
                    "unit": lever.expected_impact.unit,
                    "source": lever.expected_impact.source,
                },
                owner=lever.owner_role,
                lead_time_days=lever.lead_time_days,
                confidence=_confidence_label(f.contribution_share or 0.0),
                monitoring_plan=lever.default_monitoring_plan.model_dump(),
                evidence_ids=[f.evidence_id],
            )
        )
        if len(plan.actions) >= max_actions:
            break
    return plan


def _action_text(lever: Lever, fact: EvidenceFact) -> str:
    verbs = {
        "promo_depth": "Restart a bounded promo on the affected SKU/region to recover lost volume",
        "safety_stock": "Raise safety stock / expedite replenishment for the stocked-out SKU/warehouse",
        "channel_incentive": "Fund a direct-channel incentive to rebalance mix away from the marketplace channel",
        "marketing_budget": "Reallocate marketing spend to lift new-customer volume and dilute CAC",
    }
    base = verbs.get(lever.lever_id, f"Pull the '{lever.lever_id}' lever")
    return f"{base} (constraints: {'; '.join(lever.constraints)})"
