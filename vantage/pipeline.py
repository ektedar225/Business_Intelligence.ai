"""Runtime orchestration (the L3->L6 flow) for the three demo scenarios. Each
scenario builds one EvidenceBundle by running the method ladder cheapest/most-certain
first, doing residual accounting along the way, then scoring confidence. This module
is the only place that knows the *order* analyzers run in; every analyzer itself
stays a pure, stateless function.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pandas as pd

from vantage.contract_schema import get_registry
from vantage.diagnosis.arithmetic_bridge import price_volume_mix_bridge
from vantage.diagnosis.contribution import beam_search_slices, mix_variance_effect
from vantage.diagnosis.event_join import find_promo_end_events, find_stockout_events, scope_dollar_impact
from vantage.diagnosis.residual import residual_accounting
from vantage.confidence import compute_confidence, hard_abstain_stale_source, AbstentionResult
from vantage.evidence import EvidenceBundle, EvidenceFact, MovementFact, Telemetry
from vantage.materiality import detect_movement, hierarchy_collapse
from vantage.reconciliation import entity_resolve, freshness_report, load_sources


def _timed(analyzers_run: list[str], name: str):
    analyzers_run.append(name)


def build_scenario1_bundle(seed_note: str = "scenario1") -> tuple[EvidenceBundle, dict]:
    t0 = time.perf_counter()
    analyzers_run: list[str] = []
    src = load_sources()
    orders, marketing, supply, dim_sku = src["orders"], src["marketing"], src["supply"], src["dim_sku"]
    contract = get_registry().get("net_revenue")

    orders_resolved, recon_residual = entity_resolve(orders, dim_sku)
    _timed(analyzers_run, "entity_resolution")

    weekly = orders.groupby("week_idx")["net_revenue"].sum()
    movement = detect_movement(weekly, target_week_idx=30, kpi_id="net_revenue")
    _timed(analyzers_run, "materiality_baseline")

    region_weekly = orders.groupby(["region", "week_idx"])["net_revenue"].sum().unstack("region")
    child_deltas = {r: float(region_weekly.loc[30, r] - region_weekly.loc[29, r]) for r in region_weekly.columns}
    collapse = hierarchy_collapse(movement, child_deltas)
    _timed(analyzers_run, "hierarchy_collapse")

    prior_week, current_week = 29, 30
    prior_df = orders[orders.week_idx == prior_week]
    current_df = orders[orders.week_idx == current_week]
    pool_prior, pool_current = prior_df, current_df
    attributed: dict[str, float] = {}
    facts: list[EvidenceFact] = []
    fact_seq = 1

    def next_id() -> str:
        nonlocal fact_seq
        fid = f"E-{fact_seq:02d}"
        fact_seq += 1
        return fid

    promo_events = find_promo_end_events(marketing, prior_week, current_week)
    _timed(analyzers_run, "business_event_join_promo")
    for ev in promo_events:
        scope = {"product_family": ev["product_family"], "region": ev["region"]}
        delta, pv, cv, pidx, cidx = scope_dollar_impact(pool_prior, pool_current, scope)
        attributed["promo_calendar"] = attributed.get("promo_calendar", 0.0) + delta
        pool_prior = pool_prior.drop(pidx)
        pool_current = pool_current.drop(cidx)
        facts.append(
            EvidenceFact(
                evidence_id=next_id(),
                statement_type="driver_attribution",
                label=f"Promo campaign {ev['campaign_id']} ended ({ev['region']})",
                value=round(delta, 2),
                unit="usd",
                method="business_event_join",
                method_params={"region": ev["region"], "product_family": ev["product_family"], "campaign_id": ev["campaign_id"], "event": ev["window"]},
                source_tables=["raw.marketing", "raw.orders"],
                driver_id="promo_calendar",
                driver_type="controllable",
                contribution_share=round(delta / movement.wow_delta_abs, 4) if movement.wow_delta_abs else 0.0,
            )
        )

    as_of = datetime.fromisoformat(_meta_as_of())
    week_start_ts = pd.Timestamp(f"{2026}-07-27", tz="UTC")
    week_end_ts = pd.Timestamp("2026-08-02 23:59:59", tz="UTC")
    stockout_events = find_stockout_events(supply, week_start_ts, week_end_ts)
    _timed(analyzers_run, "business_event_join_stockout")
    for ev in stockout_events:
        scope = {"sku": ev["sku"], "region": ev["region"]}
        delta, pv, cv, pidx, cidx = scope_dollar_impact(pool_prior, pool_current, scope)
        attributed["stockout_rate"] = attributed.get("stockout_rate", 0.0) + delta
        pool_prior = pool_prior.drop(pidx, errors="ignore")
        pool_current = pool_current.drop(cidx, errors="ignore")
        facts.append(
            EvidenceFact(
                evidence_id=next_id(),
                statement_type="driver_attribution",
                label=f"{ev['sku']} stockout in {ev['warehouse']} warehouse ({ev['region']})",
                value=round(delta, 2),
                unit="usd",
                method="business_event_join",
                method_params={"region": ev["region"], "sku": ev["sku"], "warehouse": ev["warehouse"], "hours_flagged": ev["hours_flagged"]},
                source_tables=["raw.supply", "raw.orders"],
                driver_id="stockout_rate",
                driver_type="controllable",
                contribution_share=round(delta / movement.wow_delta_abs, 4) if movement.wow_delta_abs else 0.0,
            )
        )

    mix = mix_variance_effect(pool_prior, pool_current, "channel")
    attributed["channel_mix"] = mix["mix_effect"]
    _timed(analyzers_run, "dimensional_contribution_mix")
    facts.append(
        EvidenceFact(
            evidence_id=next_id(),
            statement_type="driver_attribution",
            label="Mix shift toward lower-ASP marketplace channel",
            value=round(mix["mix_effect"], 2),
            unit="usd",
            method="dimensional_contribution_mix",
            method_params={"dimension": "channel", "share_prior": mix["share_prior"], "share_current": mix["share_current"]},
            source_tables=["raw.orders"],
            driver_id="channel_mix",
            driver_type="controllable",
            contribution_share=round(mix["mix_effect"] / movement.wow_delta_abs, 4) if movement.wow_delta_abs else 0.0,
        )
    )

    resid = residual_accounting(movement.wow_delta_abs, attributed)
    _timed(analyzers_run, "residual_accounting")
    facts.append(
        EvidenceFact(
            evidence_id=next_id(),
            statement_type="driver_attribution",
            label="Unexplained residual (noise)",
            value=round(resid["residual_amount"], 2),
            unit="usd",
            method="residual_accounting",
            method_params={},
            source_tables=["raw.orders"],
            driver_id="residual",
            driver_type="uncontrollable",
            contribution_share=round(resid["residual_share"], 4),
        )
    )

    bridge = price_volume_mix_bridge(prior_df, current_df, segment_dims=["region", "channel", "sku"])
    _timed(analyzers_run, "arithmetic_bridge")
    for label, key in [("Company-wide volume effect", "volume_effect"), ("Company-wide mix effect", "mix_effect"), ("Company-wide price effect", "price_effect")]:
        facts.append(
            EvidenceFact(
                evidence_id=next_id(),
                statement_type="structural_decomposition",
                label=label,
                value=round(bridge[key], 2),
                unit="usd",
                method="arithmetic_bridge",
                method_params={"segment_dims": bridge["segment_dims"]},
                source_tables=["raw.orders"],
            )
        )

    exploratory = beam_search_slices(prior_df, current_df, dims=["region", "channel", "category", "sku", "customer_segment"], top_k=3, depth=2)
    _timed(analyzers_run, "dimensional_contribution_beam_search")
    for slice_ in exploratory[:5]:
        facts.append(
            EvidenceFact(
                evidence_id=next_id(),
                statement_type="structural_decomposition",
                label=f"Exploratory slice {dict(zip(slice_['dims'], slice_['values']))}",
                value=round(slice_["delta"], 2),
                unit="usd",
                method="dimensional_contribution_slice",
                method_params={"dims": slice_["dims"], "values": [str(v) for v in slice_["values"]]},
                source_tables=["raw.orders"],
            )
        )

    facts.append(
        EvidenceFact(
            evidence_id=next_id(),
            statement_type="reconciliation",
            label="Entity resolution residual (unmapped SKUs)",
            value=recon_residual["unmapped_revenue_usd"],
            unit="usd",
            method="entity_resolution",
            method_params=recon_residual,
            source_tables=["raw.orders", "dim.sku"],
        )
    )

    data_quality_flags: list[str] = []
    driver_facts = [f for f in facts if f.statement_type == "driver_attribution"]
    confidence = compute_confidence(
        facts=driver_facts,
        residual_share=resid["residual_share"],
        history_periods=movement.history_periods,
        min_history_periods=contract.materiality.min_history_periods,
        data_quality_flags=data_quality_flags,
    )

    wall_ms = (time.perf_counter() - t0) * 1000
    telemetry = Telemetry(analyzers_run=analyzers_run, wall_ms=round(wall_ms, 1))

    bundle = EvidenceBundle(
        event_id=f"evt-net_revenue-w{current_week}",
        kpi_id="net_revenue",
        period=f"week_{current_week}",
        as_of_watermark=_meta_as_of(),
        movement=MovementFact(
            kpi_id="net_revenue",
            period=f"week_{current_week}",
            comparison_period=movement.comparison_period,
            actual=round(movement.actual, 2),
            baseline_forecast=round(movement.baseline, 2),
            comparison_actual=round(movement.comparison_actual, 2),
            wow_delta_abs=round(movement.wow_delta_abs, 2),
            wow_delta_pct=round(movement.wow_delta_pct, 4),
            impact_usd=round(movement.impact_usd, 2),
            surprise_z=round(movement.surprise_z, 2),
            history_periods=movement.history_periods,
        ),
        facts=facts,
        residual=resid,
        confidence=confidence,
        telemetry=telemetry,
        data_quality_flags=data_quality_flags,
    ).finalize()

    debug = {
        "hierarchy_collapse": collapse,
        "reconciliation_residual": recon_residual,
        "attributed": attributed,
    }
    return bundle, debug


def _meta_as_of() -> str:
    import json
    from pathlib import Path

    meta = json.loads((Path(__file__).parent.parent / "data" / "ground_truth.json").read_text())["meta"]
    return meta["as_of"]


def _governed_margin_series(orders: pd.DataFrame, supply: pd.DataFrame) -> pd.Series:
    """Grain-safe: margin % recomputed per week from summed revenue and summed COGS,
    never averaged across regions/SKUs (see reconciliation.naive_vs_governed_margin)."""
    cost_by_sku_region_week = (
        supply.assign(week_idx=((supply.timestamp - pd.Timestamp(supply.timestamp.min())).dt.days // 7) + 1)
        .groupby(["sku", "region", "week_idx"])["unit_cost"]
        .mean()
    )
    merged = orders.merge(
        cost_by_sku_region_week.rename("unit_cost"), on=["sku", "region", "week_idx"], how="left"
    )
    merged["cogs"] = merged["units"] * merged["unit_cost"]
    weekly = merged.groupby("week_idx").apply(
        lambda g: (g["net_revenue"].sum() - g["cogs"].sum()) / g["net_revenue"].sum(), include_groups=False
    )
    return weekly


def build_scenario2_bundle() -> tuple[EvidenceBundle, AbstentionResult, dict]:
    """Gross Margin % movement where the S3 cost feed has breached its freshness SLA —
    demonstrates abstention mode C (hard abstain), not a bare refusal: revenue-side
    facts (which don't depend on S3) are still surfaced as reliable."""
    import json
    from pathlib import Path

    t0 = time.perf_counter()
    analyzers_run: list[str] = []
    src = load_sources()
    orders, supply = src["orders"], src["supply"]
    contract = get_registry().get("gross_margin_pct")
    meta = json.loads((Path(__file__).parent.parent / "data" / "ground_truth.json").read_text())["meta"]
    as_of = datetime.fromisoformat(meta["as_of"])

    fresh = freshness_report("supply", supply["timestamp"], as_of, sla_hours=contract.freshness_sla_hours)
    _timed(analyzers_run, "freshness_watermark_check")

    margin_series = _governed_margin_series(orders, supply)
    _timed(analyzers_run, "grain_safe_margin_recompute")
    current_week, prior_week = 30, 29
    current_margin = float(margin_series.loc[current_week])
    prior_margin = float(margin_series.loc[prior_week])
    current_rev = float(orders[orders.week_idx == current_week]["net_revenue"].sum())
    delta_pp = current_margin - prior_margin
    impact_usd = abs(delta_pp) * current_rev

    facts = [
        EvidenceFact(
            evidence_id="E-01",
            statement_type="data_quality",
            label=f"S3 supply/cost feed freshness check ({'BREACHED' if fresh.breached else 'OK'})",
            value=round(fresh.lag_hours, 1),
            unit="hours_stale",
            method="freshness_watermark",
            method_params={"sla_hours": fresh.sla_hours, "quality_tier": fresh.quality_tier},
            source_tables=["raw.supply"],
            freshness_ts=fresh.latest_ts.isoformat(),
            quality_tier=fresh.quality_tier,
        ),
        EvidenceFact(
            evidence_id="E-02",
            statement_type="reconciliation",
            label="Net Revenue for the same week (not dependent on the stale feed)",
            value=round(current_rev, 2),
            unit="usd",
            method="arithmetic_bridge",
            method_params={},
            source_tables=["raw.orders"],
            quality_tier="gold",
        ),
        EvidenceFact(
            evidence_id="E-03",
            statement_type="driver_attribution",
            label="Gross margin % WoW movement (UNVERIFIABLE — computed on partial-week cost data)",
            value=round(delta_pp * 100, 2),
            unit="pct_points",
            method="dimensional_contribution_mix",
            method_params={"current_margin_pct": round(current_margin * 100, 2), "prior_margin_pct": round(prior_margin * 100, 2)},
            source_tables=["raw.orders", "raw.supply"],
            quality_tier=fresh.quality_tier,
            driver_id="unit_cost_change",
            driver_type="uncontrollable",
        ),
    ]
    data_quality_flags = ["supply_feed_stale_breach"] if fresh.breached else []
    confidence = compute_confidence(
        facts=[f for f in facts if f.statement_type == "driver_attribution"],
        residual_share=0.0,
        history_periods=30,
        min_history_periods=contract.materiality.min_history_periods,
        data_quality_flags=data_quality_flags,
        hard_abstain=fresh.breached,
    )
    wall_ms = (time.perf_counter() - t0) * 1000
    bundle = EvidenceBundle(
        event_id=f"evt-gross_margin_pct-w{current_week}",
        kpi_id="gross_margin_pct",
        period=f"week_{current_week}",
        as_of_watermark=meta["as_of"],
        movement=MovementFact(
            kpi_id="gross_margin_pct",
            period=f"week_{current_week}",
            comparison_period=f"week_{prior_week}",
            actual=round(current_margin * 100, 2),
            baseline_forecast=round(prior_margin * 100, 2),
            comparison_actual=round(prior_margin * 100, 2),
            wow_delta_abs=round(delta_pp * 100, 2),
            wow_delta_pct=round(delta_pp / prior_margin, 4) if prior_margin else 0.0,
            impact_usd=round(impact_usd, 2),
            surprise_z=0.0,
            history_periods=30,
        ),
        facts=facts,
        residual={"note": "not computed — analysis blocked by data-quality abstention"},
        confidence=confidence,
        telemetry=Telemetry(analyzers_run=analyzers_run, wall_ms=round(wall_ms, 1)),
        data_quality_flags=data_quality_flags,
    ).finalize()

    abstention = hard_abstain_stale_source(
        kpi_id="gross_margin_pct",
        source="S3 supply/cost",
        lag_hours=fresh.lag_hours,
        sla_hours=fresh.sla_hours,
        owner="data-ops (supply feed pipeline)",
        reliable_findings=(
            f"Net Revenue for week {current_week} is ${current_rev:,.0f}, fully verified and unaffected "
            "by the supply feed — only the cost side of the margin calculation is blocked."
        ),
    )
    return bundle, abstention, {"freshness": fresh}


def build_scenario3_bundle() -> tuple[EvidenceBundle, dict]:
    """CAC for a newly launched product line with only 3 weeks of history — too little
    for the seasonal baseline. Falls back to plan-vs-actual, with confidence hard-capped
    at Low and the limitation stated explicitly, rather than a false-precision forecast."""
    t0 = time.perf_counter()
    analyzers_run: list[str] = []
    src = load_sources()
    cac_df = src["cac_new_family"]
    contract = get_registry().get("cac")
    _timed(analyzers_run, "history_sufficiency_check")

    history_periods = len(cac_df)
    current = cac_df.iloc[-1]
    prior = cac_df.iloc[-2]
    plan_cac = 150.0  # stated assumption: launch-quarter plan target, not derived from data

    delta_abs = float(current["cac"] - prior["cac"])
    delta_pct = delta_abs / prior["cac"]
    vs_plan_pct = (current["cac"] - plan_cac) / plan_cac
    _timed(analyzers_run, "plan_vs_actual_fallback")

    facts = [
        EvidenceFact(
            evidence_id="E-01",
            statement_type="data_quality",
            label=f"History sufficiency check: {history_periods} periods available (needs {contract.materiality.min_history_periods})",
            value=history_periods,
            unit="periods",
            method="history_sufficiency_check",
            method_params={"min_required": contract.materiality.min_history_periods},
            source_tables=["raw.marketing", "raw.orders"],
        ),
        EvidenceFact(
            evidence_id="E-02",
            statement_type="driver_attribution",
            label="CAC vs prior week (WoW)",
            value=round(delta_abs, 2),
            unit="usd_per_customer",
            method="arithmetic_bridge",
            method_params={"current_cac": round(float(current["cac"]), 2), "prior_cac": round(float(prior["cac"]), 2)},
            source_tables=["raw.marketing", "raw.orders"],
            driver_id="campaign_spend_change",
            driver_type="controllable",
            contribution_share=1.0,
        ),
        EvidenceFact(
            evidence_id="E-03",
            statement_type="driver_attribution",
            label="CAC vs launch-quarter plan (stated assumption, not a statistical baseline)",
            value=round(current["cac"] - plan_cac, 2),
            unit="usd_per_customer",
            method="plan_vs_actual",
            method_params={"plan_cac": plan_cac},
            source_tables=["raw.marketing", "raw.orders"],
        ),
    ]
    confidence = compute_confidence(
        facts=[f for f in facts if f.statement_type == "driver_attribution"],
        residual_share=0.0,
        history_periods=history_periods,
        min_history_periods=contract.materiality.min_history_periods,
        data_quality_flags=["sparse_history"],
        confidence_cap=contract.sparse_history_mode.confidence_cap if contract.sparse_history_mode else None,
    )
    wall_ms = (time.perf_counter() - t0) * 1000
    bundle = EvidenceBundle(
        event_id="evt-cac-family_e-w30",
        kpi_id="cac",
        period="week_30",
        as_of_watermark=_meta_as_of(),
        movement=MovementFact(
            kpi_id="cac",
            period="week_30",
            comparison_period="week_29",
            actual=round(float(current["cac"]), 2),
            baseline_forecast=None,
            comparison_actual=round(float(prior["cac"]), 2),
            wow_delta_abs=round(delta_abs, 2),
            wow_delta_pct=round(delta_pct, 4),
            impact_usd=round(abs(delta_abs) * float(current["new_customers"]), 2),
            surprise_z=0.0,
            history_periods=history_periods,
        ),
        facts=facts,
        residual={"note": "statistical baseline disabled — insufficient history for a seasonal decomposition"},
        confidence=confidence,
        telemetry=Telemetry(analyzers_run=analyzers_run, wall_ms=round(wall_ms, 1)),
        data_quality_flags=["sparse_history"],
    ).finalize()
    return bundle, {"vs_plan_pct": vs_plan_pct, "plan_cac": plan_cac}
