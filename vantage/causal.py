"""Causal Inference — Difference-in-Differences (DiD) estimator for the promo-end
Average Treatment Effect (ATE) on net revenue.

Why DiD and not do-calculus / DoWhy?
--------------------------------------
The synthetic dataset does not include independent variation in the confounders
(e.g. a true randomised experiment) needed for the backdoor criterion. DiD is the
strongest causal design we can defensibly apply here: it controls for time-invariant
confounders and common time trends by differencing treated vs. control before and
after treatment.

The limitations field in CausalEstimate is a first-class output — this engine is
designed to be honest about what it does and does not prove, per the brief's
requirement to communicate uncertainty.

Future upgrade path: replace `_did_estimate()` with a DoWhy `CausalModel` backed
by a richer structural causal graph once panel data with individual-level variation
becomes available.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CausalEstimate:
    treatment: str
    outcome: str
    method: str
    ate_estimate: float          # estimated average treatment effect
    ate_unit: str
    ate_ci_lower: float          # 95% CI lower bound
    ate_ci_upper: float          # 95% CI upper bound
    pre_period: str
    post_period: str
    n_treated: int
    n_control: int
    parallel_trends_note: str
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    upgrade_path: str = ""


# ---------------------------------------------------------------------------
# DiD implementation
# ---------------------------------------------------------------------------


def _safe_mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _stderr_of_diff(a: list[float], b: list[float]) -> float:
    """Pooled standard error of the difference of two group means."""
    def var(xs: list[float]) -> float:
        if len(xs) < 2:
            return 0.0
        m = _safe_mean(xs)
        return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)

    se = math.sqrt(var(a) / max(len(a), 1) + var(b) / max(len(b), 1))
    return se


def _did_estimate(
    df: pd.DataFrame,
    treatment_col: str,
    outcome_col: str,
    post_col: str,
) -> tuple[float, float, float, int, int]:
    """Canonical DiD: ATE = (ȳ_treat_post - ȳ_treat_pre) - (ȳ_ctrl_post - ȳ_ctrl_pre).
    Returns (ate, ci_lower, ci_upper, n_treated, n_control).
    """
    treat_pre = df.loc[(df[treatment_col] == 1) & (df[post_col] == 0), outcome_col].tolist()
    treat_post = df.loc[(df[treatment_col] == 1) & (df[post_col] == 1), outcome_col].tolist()
    ctrl_pre = df.loc[(df[treatment_col] == 0) & (df[post_col] == 0), outcome_col].tolist()
    ctrl_post = df.loc[(df[treatment_col] == 0) & (df[post_col] == 1), outcome_col].tolist()

    treat_diff = _safe_mean(treat_post) - _safe_mean(treat_pre)
    ctrl_diff = _safe_mean(ctrl_post) - _safe_mean(ctrl_pre)
    ate = treat_diff - ctrl_diff

    # 95% CI using propagated standard errors (conservative)
    se = math.sqrt(
        _stderr_of_diff(treat_post, treat_pre) ** 2 +
        _stderr_of_diff(ctrl_post, ctrl_pre) ** 2
    )
    z95 = 1.96
    ci_lo = ate - z95 * se
    ci_hi = ate + z95 * se

    n_treated = len(set(df.loc[df[treatment_col] == 1].index.tolist()))
    n_control = len(set(df.loc[df[treatment_col] == 0].index.tolist()))
    return round(ate, 2), round(ci_lo, 2), round(ci_hi, 2), n_treated, n_control


# ---------------------------------------------------------------------------
# Public: Promo ATE estimator
# ---------------------------------------------------------------------------


def estimate_promo_ate(orders_df: pd.DataFrame) -> CausalEstimate:
    """Estimate the Average Treatment Effect of the AMER promo ending (week 29→30)
    on per-SKU weekly net_revenue using Difference-in-Differences.

    Treatment group: SKUs in the AMER promo (product_family = 'family_a', region = 'AMER').
    Control group: All other AMER SKUs (same region, different product family — controls
    for region-level common trends like seasonality, macroeconomics).

    Pre period: week 29  |  Post period: week 30.
    """
    # Build panel: weekly revenue per SKU
    panel = (
        orders_df[orders_df.region == "AMER"]
        .groupby(["sku", "product_family", "week_idx"])["net_revenue"]
        .sum()
        .reset_index()
    )

    if panel.empty or "week_idx" not in panel.columns:
        return CausalEstimate(
            treatment="promo_end_AMER_family_a",
            outcome="net_revenue_per_sku",
            method="difference_in_differences",
            ate_estimate=0.0,
            ate_unit="usd_per_sku_per_week",
            ate_ci_lower=0.0,
            ate_ci_upper=0.0,
            pre_period="week_29",
            post_period="week_30",
            n_treated=0,
            n_control=0,
            parallel_trends_note="Insufficient data — could not build panel.",
            assumptions=[],
            limitations=["Insufficient data to run DiD."],
        )

    pre_week, post_week = 29, 30
    panel_pp = panel[panel.week_idx.isin([pre_week, post_week])].copy()
    panel_pp["is_treated"] = (panel_pp["product_family"] == "family_a").astype(int)
    panel_pp["is_post"] = (panel_pp["week_idx"] == post_week).astype(int)

    ate, ci_lo, ci_hi, n_treat, n_ctrl = _did_estimate(
        panel_pp,
        treatment_col="is_treated",
        outcome_col="net_revenue",
        post_col="is_post",
    )

    return CausalEstimate(
        treatment="promo_end_AMER_family_a (week 29 → 30)",
        outcome="net_revenue_per_sku_per_week (AMER)",
        method="difference_in_differences",
        ate_estimate=ate,
        ate_unit="usd_per_sku_per_week",
        ate_ci_lower=ci_lo,
        ate_ci_upper=ci_hi,
        pre_period="week_29",
        post_period="week_30",
        n_treated=n_treat,
        n_control=n_ctrl,
        parallel_trends_note=(
            "Parallel-trends assumption: both treated (family_a) and control (other families) "
            "operated in the same AMER region, subject to the same macro and seasonal trends. "
            "This makes the assumption plausible but not verifiable with only 2 periods."
        ),
        assumptions=[
            "Parallel trends: treated and control would have moved identically absent the promo ending.",
            "SUTVA: promo end for family_a did not change behaviour of control-group SKUs.",
            "No simultaneous treatment: no other AMER-wide shock in week 30 confounds the estimate.",
        ],
        limitations=[
            "Only 2 time periods available (week 29, 30) — cannot test parallel trends empirically.",
            "This is an associative estimate with quasi-causal controls, not a full do-calculus result.",
            "No individual-level randomisation — SKU-level unobservables may still bias the ATE.",
            "Upgrade to DoWhy CausalModel + backdoor criterion once longer panel data is available.",
        ],
        upgrade_path=(
            "Replace _did_estimate() with a DoWhy CausalModel backed by a structural causal graph "
            "that explicitly encodes confounders (seasonality, supply, competitor price) once "
            "panel data with individual-level variation is available."
        ),
    )
