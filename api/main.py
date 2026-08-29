"""FastAPI surface for the VANTAGE prototype. This is intentionally a thin layer: all
the substantive logic (materiality, diagnosis, confidence, narrative, actions) lives
in vantage/*.py as plain, testable Python — the API just orchestrates calls and
applies entitlements before anything is returned.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from vantage import audit, feedback as feedback_mod
from vantage.actions import compose_actions
from vantage.confidence import AbstentionResult
from vantage.contract_schema import get_registry
from vantage.evidence import EvidenceBundle
from vantage.intent import resolve_intent
from vantage.narrative import (
    inject_violation_demo,
    render_abstention_narrative,
    render_narrative,
    route_tier,
    verify_narrative,
)
from vantage.pipeline import build_scenario1_bundle, build_scenario2_bundle, build_scenario3_bundle
from vantage.reconciliation import load_sources, naive_vs_governed_margin
from vantage.registries import get_lever_registry, get_persona_registry
from vantage.scorecard import recovery_scorecard

app = FastAPI(title="VANTAGE — KPI Intelligence-to-Action Engine")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_bundle_cache: dict[str, tuple[EvidenceBundle, object]] = {}


def _get_scenario_raw(scenario_id: str):
    if scenario_id in _bundle_cache:
        return _bundle_cache[scenario_id]
    if scenario_id == "1":
        result = build_scenario1_bundle()
    elif scenario_id == "2":
        result = build_scenario2_bundle()
    elif scenario_id == "3":
        result = build_scenario3_bundle()
    else:
        raise HTTPException(404, f"unknown scenario '{scenario_id}'")
    _bundle_cache[scenario_id] = result
    return result


def _scope_bundle(bundle: EvidenceBundle, persona_id: str) -> EvidenceBundle:
    personas = get_persona_registry()
    persona = personas.get(persona_id)
    contract = get_registry().get(bundle.kpi_id)
    return bundle.scoped_to(
        entitled_regions=persona.metric_scope.regions,
        masked_columns=persona.column_masks,
        persona_id=persona_id,
        row_policy=contract.entitlements.row_policy,
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/contracts")
def contracts():
    reg = get_registry()
    return [c.model_dump() for c in reg.contracts.values()]


@app.get("/api/personas")
def personas():
    return [p.model_dump() for p in get_persona_registry().all()]


@app.get("/api/scenario/{scenario_id}")
def scenario(scenario_id: str, persona_id: str = "cfo"):
    t0 = time.perf_counter()
    personas = get_persona_registry()
    if persona_id not in personas.personas:
        raise HTTPException(400, f"unknown persona '{persona_id}'")
    persona = personas.get(persona_id)
    levers = get_lever_registry()

    raw = _get_scenario_raw(scenario_id)
    bundle: EvidenceBundle = raw[0]
    abstention: Optional[AbstentionResult] = raw[1] if scenario_id == "2" else None
    debug = raw[-1] if scenario_id != "2" else raw[2]

    scoped = _scope_bundle(bundle, persona_id)

    if abstention is not None:
        narrative_text = render_abstention_narrative(abstention)
        narrative_payload = {"full_text": narrative_text, "tier": "T0_template", "mode": abstention.mode}
        actions_payload = {"actions": [], "escalations": []}
        firewall = None
    else:
        narrative = render_narrative(scoped, persona)
        verdict = verify_narrative(narrative, scoped)
        narrative_payload = {
            "headline": narrative.headline,
            "what_changed": narrative.what_changed,
            "why": narrative.why,
            "what_we_dont_know": narrative.what_we_dont_know,
            "confidence_statement": narrative.confidence_statement,
            "evidence_ids_used": narrative.evidence_ids_used,
            "full_text": narrative.full_text,
            "tier": narrative.tier,
        }
        plan = compose_actions(scoped, persona, levers)
        actions_payload = {
            "actions": [a.__dict__ for a in plan.actions],
            "escalations": [e.__dict__ for e in plan.escalations],
        }
        firewall = {"passed": verdict.passed, "orphan_numerals": verdict.orphan_numerals, "causal_overreach": verdict.causal_overreach}

    wall_ms = round((time.perf_counter() - t0) * 1000, 1)
    audit.append_entry(
        event_id=scoped.event_id,
        bundle_hash=scoped.bundle_hash,
        persona_id=persona_id,
        methods_run=scoped.telemetry.analyzers_run if scoped.telemetry else [],
        model_version="template_t0" if abstention is None else "abstention_template",
        narrative_summary=narrative_payload.get("headline") or narrative_payload["full_text"][:120],
        row_policy=scoped.entitlement_scope.applied_row_policy if scoped.entitlement_scope else "none",
        actions_taken=[],
    )

    return {
        "bundle": scoped.model_dump(),
        "abstention": abstention.__dict__ if abstention else None,
        "narrative": narrative_payload,
        "actions": actions_payload,
        "firewall": firewall,
        "debug": debug if isinstance(debug, dict) else None,
        "api_wall_ms": wall_ms,
    }


@app.get("/api/scenario/1/scorecard")
def scorecard():
    bundle, _ = _get_scenario_raw("1")
    return recovery_scorecard(bundle)


@app.get("/api/naive-vs-governed")
def naive_vs_governed():
    src = load_sources()
    return naive_vs_governed_margin(src["orders"], src["supply"], src["dim_sku"])


@app.get("/api/firewall-demo")
def firewall_demo(persona_id: str = "cfo"):
    bundle, _ = _get_scenario_raw("1")
    persona = get_persona_registry().get(persona_id)
    scoped = _scope_bundle(bundle, persona_id)
    narrative = render_narrative(scoped, persona)
    clean_verdict = verify_narrative(narrative, scoped)
    corrupted = inject_violation_demo(narrative)
    corrupted_verdict = verify_narrative(corrupted, scoped)
    return {
        "clean_text": narrative.full_text,
        "clean_verdict": clean_verdict.__dict__,
        "corrupted_text": corrupted.full_text,
        "corrupted_verdict": corrupted_verdict.__dict__,
    }


class FeedbackIn(BaseModel):
    event_id: str
    driver_id: str
    polarity: str
    analyst: str = "demo_analyst"
    comment: str = ""


@app.post("/api/feedback")
def submit_feedback(body: FeedbackIn):
    structured = feedback_mod.submit_feedback(body.event_id, body.driver_id, body.polarity, body.analyst, body.comment)
    audit.append_entry(
        event_id=body.event_id,
        bundle_hash="n/a",
        persona_id=body.analyst,
        methods_run=["feedback_structurer"],
        model_version="rule_based",
        narrative_summary=f"feedback: {body.polarity} on {body.driver_id}",
        row_policy="n/a",
        feedback=structured,
    )
    return {"structured": structured, "weights": feedback_mod.read_weights()}


@app.get("/api/audit")
def get_audit(limit: int = 50):
    return {"entries": audit.read_ledger(limit), "chain_valid": audit.verify_chain()}


class AskIn(BaseModel):
    text: str


@app.post("/api/ask")
def ask(body: AskIn):
    kpi_id, abstention = resolve_intent(body.text)
    if abstention:
        return {"resolved_kpi": None, "abstention": abstention.__dict__}
    if kpi_id is None:
        return {"resolved_kpi": None, "abstention": None, "message": "No registered KPI matched that question."}
    return {"resolved_kpi": kpi_id, "abstention": None}


@app.get("/api/telemetry")
def telemetry():
    summary = []
    total_ms = 0.0
    tier_counts: dict[str, int] = {}
    for sid in ["1", "2", "3"]:
        raw = _get_scenario_raw(sid)
        bundle: EvidenceBundle = raw[0]
        t = bundle.telemetry
        if t:
            total_ms += t.wall_ms
        tier = route_tier(bundle)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        summary.append(
            {
                "scenario": sid,
                "kpi_id": bundle.kpi_id,
                "analyzers_run": t.analyzers_run if t else [],
                "wall_ms": t.wall_ms if t else None,
                "model_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "would_route_tier": tier,
            }
        )
    return {
        "per_scenario": summary,
        "totals": {
            "total_wall_ms": round(total_ms, 1),
            "total_model_calls": 0,
            "total_cost_usd": 0.0,
            "tier_distribution": tier_counts,
            "deterministic_share": 1.0,
            "note": "All narrative generation in this prototype runs on the T0 template tier (0 model calls, $0 cost). route_tier() shows what the complexity-based router would select if a model tier were exercised.",
        },
    }


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
