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
from vantage.pipeline import build_scenario1_bundle, build_scenario2_bundle, build_scenario3_bundle, build_scenario4_bundle
from vantage.reconciliation import load_sources, naive_vs_governed_margin
from vantage.registries import get_lever_registry, get_persona_registry
from vantage.scorecard import recovery_scorecard
from vantage.alerts import evaluate_alerts, deliver_alerts
from vantage.drift import detect_data_drift, detect_driver_rank_drift
from vantage.causal import estimate_promo_ate

app = FastAPI(title="VANTAGE — KPI Intelligence-to-Action Engine")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_bundle_cache: dict[str, tuple[EvidenceBundle, object]] = {}
_telemetry_history: dict[str, dict] = {}

def _get_scenario_raw(scenario_id: str):
    if scenario_id in _bundle_cache:
        return _bundle_cache[scenario_id]
    if scenario_id == "1":
        result = build_scenario1_bundle()
    elif scenario_id == "2":
        result = build_scenario2_bundle()
    elif scenario_id == "3":
        result = build_scenario3_bundle()
    elif scenario_id == "4":
        result = build_scenario4_bundle()
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
    abstention: Optional[AbstentionResult] = raw[1] if scenario_id in ("2", "4") else None
    debug = raw[-1] if scenario_id not in ("2",) else raw[2]

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
            "llm_meta": narrative.llm_meta,
        }
        if narrative.llm_meta and scoped.telemetry:
            scoped.telemetry.model_calls = 1
            scoped.telemetry.input_tokens = narrative.llm_meta.get("input_tokens", 0)
            scoped.telemetry.output_tokens = narrative.llm_meta.get("output_tokens", 0)
            scoped.telemetry.cost_usd = narrative.llm_meta.get("cost_usd", 0.0)
            scoped.telemetry.tier = narrative.tier
        plan = compose_actions(scoped, persona, levers)
        actions_payload = {
            "actions": [a.__dict__ for a in plan.actions],
            "escalations": [e.__dict__ for e in plan.escalations],
        }
        firewall = {"passed": verdict.passed, "orphan_numerals": verdict.orphan_numerals, "causal_overreach": verdict.causal_overreach}

    wall_ms = round((time.perf_counter() - t0) * 1000, 1)
    llm_meta = narrative_payload.get("llm_meta") or {}
    _telemetry_history[scenario_id] = {
        "scenario": scenario_id,
        "kpi_id": scoped.kpi_id,
        "analyzers_run": scoped.telemetry.analyzers_run if scoped.telemetry else [],
        "wall_ms": wall_ms,
        "model_calls": 1 if llm_meta.get("input_tokens") else 0,
        "input_tokens": llm_meta.get("input_tokens", 0),
        "output_tokens": llm_meta.get("output_tokens", 0),
        "cost_usd": llm_meta.get("cost_usd", 0.0),
        "tier": narrative_payload.get("tier", "T0_template"),
        "model": llm_meta.get("model", "none"),
    }
    audit.append_entry(
        event_id=scoped.event_id,
        bundle_hash=scoped.bundle_hash,
        persona_id=persona_id,
        methods_run=scoped.telemetry.analyzers_run if scoped.telemetry else [],
        model_version=narrative_payload.get("tier", "template_t0") if abstention is None else "abstention_template",
        narrative_summary=narrative_payload.get("headline") or narrative_payload["full_text"][:120],
        row_policy=scoped.entitlement_scope.applied_row_policy if scoped.entitlement_scope else "none",
        actions_taken=[],
    )

    alerts_triggered = evaluate_alerts(bundle)
    deliver_alerts(alerts_triggered)

    return {
        "bundle": scoped.model_dump(),
        "abstention": abstention.__dict__ if abstention else None,
        "narrative": narrative_payload,
        "actions": actions_payload,
        "firewall": firewall,
        "alerts": [a.__dict__ for a in alerts_triggered],
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
    total_calls = 0
    total_in_tokens = 0
    total_out_tokens = 0
    total_cost = 0.0
    tier_counts: dict[str, int] = {}

    for sid in ["1", "2", "3", "4"]:
        if sid in _telemetry_history:
            item = _telemetry_history[sid]
        else:
            raw = _get_scenario_raw(sid)
            bundle: EvidenceBundle = raw[0]
            t = bundle.telemetry
            active_tier = route_tier(bundle)
            item = {
                "scenario": sid,
                "kpi_id": bundle.kpi_id,
                "analyzers_run": t.analyzers_run if t else [],
                "wall_ms": t.wall_ms if t else 0.0,
                "model_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "tier": active_tier,
                "model": "none",
            }

        total_ms += item.get("wall_ms", 0.0)
        total_calls += item.get("model_calls", 0)
        total_in_tokens += item.get("input_tokens", 0)
        total_out_tokens += item.get("output_tokens", 0)
        total_cost += item.get("cost_usd", 0.0)
        active_tier = item.get("tier", "T0_template")
        tier_counts[active_tier] = tier_counts.get(active_tier, 0) + 1
        summary.append(item)

    n_scenarios = len(summary)
    deterministic_share = round(1.0 - (total_calls / max(n_scenarios, 1)), 4)

    return {
        "per_scenario": summary,
        "totals": {
            "total_wall_ms": round(total_ms, 1),
            "total_model_calls": total_calls,
            "total_input_tokens": total_in_tokens,
            "total_output_tokens": total_out_tokens,
            "total_cost_usd": round(total_cost, 6),
            "deterministic_share": deterministic_share,
            "tier_distribution": tier_counts,
            "note": "VANTAGE uses a hybrid architecture: 100% deterministic numeric truth + Google Gemini LLM for persona narrative synthesis and conversational intent under strict numeric firewall verification.",
        },
    }

@app.get("/api/feedback/weights")
def feedback_weights(limit: int = 20):
    """Return current Beta-Bernoulli driver weights and the last N feedback entries."""
    weights = feedback_mod.read_weights()
    log = feedback_mod.read_feedback_log(limit)
    return {"weights": weights, "recent_log": log}

@app.get("/api/alerts")
def alerts_endpoint():
    """Evaluate alert rules against all currently loaded scenario bundles."""
    all_alerts = []
    for sid in ["1", "2", "3", "4"]:
        try:
            raw = _get_scenario_raw(sid)
            bundle = raw[0]
            triggered = evaluate_alerts(bundle)
            all_alerts.extend([a.__dict__ for a in triggered])
        except Exception:
            pass
    return {"alerts": all_alerts, "count": len(all_alerts)}

@app.get("/api/drift")
def drift_endpoint():
    """Run data drift (PSI) on Scenario 1 net revenue weekly series, and driver-rank
    drift if feedback weights exist across multiple snapshots."""
    src = load_sources()
    orders = src["orders"]
    weekly = orders.groupby("week_idx")["net_revenue"].sum().sort_index()
    values = weekly.tolist()
    mid = len(values) // 2
    window_a = values[:mid]
    window_b = values[mid:]
    data_drift = detect_data_drift(
        window_a, window_b,
        metric="net_revenue_weekly",
        label_a=f"weeks_1_to_{mid}",
        label_b=f"weeks_{mid+1}_to_{len(values)}",
    )

    weights = feedback_mod.read_weights()
    w_flat = {k: v.get("posterior_weight", 0.5) for k, v in weights.items()}
    driver_drift = detect_driver_rank_drift(
        [w_flat, w_flat] if w_flat else [{}, {}],
        label_a="snapshot_baseline",
        label_b="snapshot_current",
    )
    return {
        "data_drift": data_drift.__dict__,
        "driver_rank_drift": driver_drift.__dict__,
    }

@app.get("/api/causal")
def causal_endpoint():
    """Run DiD causal inference to estimate the Average Treatment Effect of the
    AMER promo ending on SKU-level net revenue."""
    src = load_sources()
    orders = src["orders"]
    estimate = estimate_promo_ate(orders)
    return estimate.__dict__

static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
