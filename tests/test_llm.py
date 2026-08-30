"""Tests for Google Gemini LLM integration: intent resolution, narrative synthesis,
and numeric firewall guarantees.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from vantage.intent import resolve_intent
from vantage.narrative import render_narrative, verify_narrative, numeric_firewall
from vantage.pipeline import build_scenario1_bundle
from vantage.registries import get_persona_registry


def test_gemini_intent_resolution_clear_query():
    kpi_id, abstention = resolve_intent("Why did our net revenue drop in Europe last week?")
    assert kpi_id == "net_revenue"
    assert abstention is None


def test_gemini_intent_resolution_ambiguous_query():
    kpi_id, abstention = resolve_intent("How is our overall business performance?")
    assert kpi_id is None
    assert abstention is not None
    assert abstention.mode == "A_clarify"
    assert len(abstention.clarifying_question) > 0


def test_gemini_narrative_generation_passes_firewall():
    bundle, _ = build_scenario1_bundle()
    persona = get_persona_registry().get("cfo")
    scoped = bundle.scoped_to(
        entitled_regions=persona.metric_scope.regions,
        masked_columns=persona.column_masks,
        persona_id=persona.persona_id,
        row_policy="region_in(user.regions)",
    )
    narrative = render_narrative(scoped, persona, use_llm=True)
    verdict = verify_narrative(narrative, scoped)
    assert verdict.passed, f"Firewall failed with orphans: {verdict.orphan_numerals}"
    assert len(narrative.headline) > 0
    assert len(narrative.what_changed) > 0


def test_narrative_fallback_to_template_if_disabled():
    bundle, _ = build_scenario1_bundle()
    persona = get_persona_registry().get("cfo")
    scoped = bundle.scoped_to(
        entitled_regions=persona.metric_scope.regions,
        masked_columns=persona.column_masks,
        persona_id=persona.persona_id,
        row_policy="region_in(user.regions)",
    )
    narrative = render_narrative(scoped, persona, use_llm=False)
    assert narrative.tier == "T0_template"
    verdict = verify_narrative(narrative, scoped)
    assert verdict.passed
