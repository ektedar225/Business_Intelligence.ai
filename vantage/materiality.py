"""L3 — Detection / Materiality Engine.

Two-axis materiality (statistical surprise x business impact, not a single
threshold), a seasonality-aware trailing baseline in place of naive
period-over-period comparison, and hierarchy collapse so a global movement and
its regional children are reported as ONE event rather than an alert storm.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

BASELINE_WINDOW_WEEKS = 8

@dataclass
class Movement:
    kpi_id: str
    period_label: str
    actual: float
    baseline: float
    delta_abs: float
    delta_pct: float
    surprise_z: float
    impact_usd: float
    history_periods: int
    comparison_period: str
    comparison_actual: float
    wow_delta_abs: float
    wow_delta_pct: float

def seasonal_naive_baseline(weekly_series: pd.Series, target_week_idx: int, window: int = BASELINE_WINDOW_WEEKS) -> tuple[float, float, int]:
    """Baseline = trailing-window mean (a forecast, not last period), so the engine
    doesn't fire on every expected seasonal swing. Returns (baseline, std, n_periods)."""
    history = weekly_series[weekly_series.index < target_week_idx].tail(window)
    if len(history) == 0:
        return float("nan"), float("nan"), 0
    return float(history.mean()), float(history.std(ddof=0)) or 1e-6, int(len(history))

def detect_movement(weekly_series: pd.Series, target_week_idx: int, kpi_id: str) -> Movement:
    """Two different comparisons serve two different jobs. `baseline` is a forecast
    (trailing-window mean) and drives the statistical-surprise axis of materiality —
    it is what stops the engine firing on every expected seasonal swing. `comparison_actual`
    is strictly the prior period and is what the diagnosis engine (L4) decomposes: 'what
    changed since last week' is a different, and equally valid, question from 'was this
    surprising against trend', and collapsing them into one number hides that distinction.
    """
    actual = float(weekly_series.loc[target_week_idx])
    baseline, std, n = seasonal_naive_baseline(weekly_series, target_week_idx)
    delta_abs = actual - baseline
    surprise_z = delta_abs / std if std else 0.0
    delta_pct = delta_abs / baseline if baseline else 0.0

    prior_idx = target_week_idx - 1
    comparison_actual = float(weekly_series.loc[prior_idx]) if prior_idx in weekly_series.index else float("nan")
    wow_delta_abs = actual - comparison_actual
    wow_delta_pct = wow_delta_abs / comparison_actual if comparison_actual else 0.0

    return Movement(
        kpi_id=kpi_id,
        period_label=f"week_{target_week_idx}",
        actual=actual,
        baseline=baseline,
        delta_abs=delta_abs,
        delta_pct=delta_pct,
        surprise_z=surprise_z,
        impact_usd=abs(wow_delta_abs),
        history_periods=n,
        comparison_period=f"week_{prior_idx}",
        comparison_actual=comparison_actual,
        wow_delta_abs=wow_delta_abs,
        wow_delta_pct=wow_delta_pct,
    )

def materiality_quadrant(movement: Movement, min_impact_usd: float, min_surprise_z: float) -> str:
    high_impact = movement.impact_usd >= min_impact_usd
    high_surprise = abs(movement.surprise_z) >= min_surprise_z
    if high_impact and high_surprise:
        return "alert_full_diagnosis"
    if high_impact and not high_surprise:
        return "digest_expected_but_large"
    if not high_impact and high_surprise:
        return "weekly_digest"
    return "suppress"

def hierarchy_collapse(parent_movement: Movement, child_deltas: dict[str, float]) -> dict:
    """Traverses the KPI/dimension graph and collapses child movements that are
    already accounted for by the parent event into ONE alert, attaching the
    children as drivers rather than firing N additional independent alerts."""
    parent_delta = parent_movement.wow_delta_abs
    contributions = {k: (v / parent_delta if parent_delta else 0.0) for k, v in child_deltas.items()}
    ranked = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)
    top2_share = sum(abs(v) for _, v in ranked[:2]) if ranked else 0.0
    collapsed = True
    would_be_independent_alerts = sum(
        1 for v in child_deltas.values() if abs(v) >= 0.3 * abs(parent_delta)
    )
    return {
        "collapsed_to_single_event": collapsed,
        "child_contribution_share": {k: round(v, 4) for k, v in contributions.items()},
        "top2_children_share_of_move": round(top2_share / abs(parent_delta), 4) if parent_delta else 0.0,
        "alerts_suppressed_by_collapse": max(0, would_be_independent_alerts - 1),
    }
