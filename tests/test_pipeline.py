"""Smoke tests over the deterministic core. These pin down the behaviors the whole
pitch rests on: the recovery scorecard hits its stated targets, the numeric firewall
passes real narratives and catches a fabricated one, entitlements actually remove
rows, and abstention fires when it should. If any of these regress, the demo's
central claims are no longer true.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from vantage.pipeline import build_scenario1_bundle, build_scenario2_bundle, build_scenario3_bundle
from vantage.scorecard import recovery_scorecard
from vantage.narrative import render_narrative, verify_narrative, inject_violation_demo
from vantage.registries import get_persona_registry
from vantage.actions import compose_actions
from vantage.registries import get_lever_registry


def test_scenario1_recovers_all_three_injected_drivers():
    bundle, _ = build_scenario1_bundle()
    sc = recovery_scorecard(bundle)
    assert sc["driver_recall_at_3"] == 1.0
    assert sc["rank_correlation_spearman"] == 1.0
    assert sc["attribution_mae_pp"] < sc["attribution_mae_target_pp"]
    assert sc["residual_error_pp"] < sc["residual_error_target_pp"]


def test_clean_narrative_passes_firewall_for_every_persona():
    bundle, _ = build_scenario1_bundle()
    personas = get_persona_registry()
    for persona in personas.all():
        narrative = render_narrative(bundle, persona)
        verdict = verify_narrative(narrative, bundle)
        assert verdict.passed, f"{persona.persona_id}: {verdict.orphan_numerals} {verdict.causal_overreach}"


def test_firewall_catches_injected_fabrication():
    bundle, _ = build_scenario1_bundle()
    persona = get_persona_registry().get("cfo")
    narrative = render_narrative(bundle, persona)
    corrupted = inject_violation_demo(narrative)
    verdict = verify_narrative(corrupted, bundle)
    assert not verdict.passed
    assert "0.034" in verdict.orphan_numerals


def test_regional_director_never_sees_amer_only_facts():
    bundle, _ = build_scenario1_bundle()
    persona = get_persona_registry().get("regional_director_emea")
    scoped = bundle.scoped_to(
        entitled_regions=persona.metric_scope.regions,
        masked_columns=persona.column_masks,
        persona_id=persona.persona_id,
        row_policy="region_in(user.regions)",
    )
    assert all(f.method_params.get("region") != "AMER" for f in scoped.facts)
    assert "AMER" in scoped.entitlement_scope.excluded_regions


def test_scenario2_hard_abstains_on_stale_feed():
    bundle, abstention, _ = build_scenario2_bundle()
    assert bundle.confidence.band == "abstain"
    assert abstention.mode == "C_hard_abstain"
    assert "supply_feed_stale_breach" in bundle.data_quality_flags


def test_scenario3_confidence_capped_low():
    bundle, _ = build_scenario3_bundle()
    assert bundle.confidence.band == "low"
    assert bundle.confidence.composite <= 0.649


def test_actions_respect_decision_rights():
    bundle, _ = build_scenario1_bundle()
    levers = get_lever_registry()
    personas = get_persona_registry()
    cfo_plan = compose_actions(bundle, personas.get("cfo"), levers)
    assert len(cfo_plan.actions) == 0  # CFO owns no operational levers in this registry
    assert len(cfo_plan.escalations) > 0
    category_plan = compose_actions(bundle, personas.get("category_manager"), levers)
    assert any(a.lever == "promo_depth" for a in category_plan.actions)
