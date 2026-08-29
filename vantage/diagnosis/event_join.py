"""Method #3 on the ladder: business-event join. Nearly free and often the actual
answer — join registered operational facts (promo start/end, stockout flags) from S2
(marketing) and S3 (supply) onto the movement's time window and dimension scope, then
compute the exact dollar delta for that scope. High certainty, but still honestly
labeled as coincidence-in-time-and-scope, not proven causation — that distinction is
enforced later by the narrative's causal-language gate.
"""
from __future__ import annotations

import pandas as pd


def find_promo_end_events(marketing_df: pd.DataFrame, prior_week: int, current_week: int) -> list[dict]:
    """A campaign that was promo_flag=True in the prior week and promo_flag=False (or
    absent) in the current week, for the same product_family/region — a promo-ended event."""
    prior = marketing_df[(marketing_df.week_idx == prior_week) & (marketing_df.promo_flag)]
    current_keys = set(
        marketing_df[(marketing_df.week_idx == current_week) & (marketing_df.promo_flag)][
            ["product_family", "region"]
        ].itertuples(index=False, name=None)
    )
    events = []
    for _, row in prior.iterrows():
        key = (row.product_family, row.region)
        if key not in current_keys:
            events.append(
                {
                    "event_type": "promo_ended",
                    "campaign_id": row.campaign_id,
                    "product_family": row.product_family,
                    "region": row.region,
                    "promo_depth": float(row.promo_depth),
                    "window": f"week_{prior_week}_active -> week_{current_week}_ended",
                }
            )
    return events


def find_stockout_events(supply_df: pd.DataFrame, week_start, week_end) -> list[dict]:
    tz = supply_df.timestamp.dt.tz
    start_ts = pd.Timestamp(week_start).tz_localize(tz) if tz and pd.Timestamp(week_start).tzinfo is None else pd.Timestamp(week_start)
    end_ts = pd.Timestamp(week_end).tz_localize(tz) if tz and pd.Timestamp(week_end).tzinfo is None else pd.Timestamp(week_end)
    window = supply_df[(supply_df.timestamp >= start_ts) & (supply_df.timestamp <= end_ts)]
    flagged = window[window.stockout_flag]
    if flagged.empty:
        return []
    events = []
    for (sku, warehouse, region), grp in flagged.groupby(["sku", "warehouse", "region"]):
        events.append(
            {
                "event_type": "stockout",
                "sku": sku,
                "warehouse": warehouse,
                "region": region,
                "hours_flagged": int(len(grp)),
                "window": f"{grp.timestamp.min()} -> {grp.timestamp.max()}",
            }
        )
    return events


def scope_dollar_impact(
    prior_df: pd.DataFrame, current_df: pd.DataFrame, scope: dict, value_col: str = "net_revenue"
) -> tuple[float, float, float, pd.Index, pd.Index]:
    """Filters both periods to the event's exact dimension scope and returns the WoW
    delta for that scope — an exact partition sum, plus the row indices consumed so the
    caller can remove them from the unattributed pool (residual accounting waterfall)."""
    def apply_scope(df: pd.DataFrame) -> pd.DataFrame:
        mask = pd.Series(True, index=df.index)
        for k, v in scope.items():
            if k in df.columns:
                mask &= df[k] == v
        return df[mask]

    p = apply_scope(prior_df)
    c = apply_scope(current_df)
    prior_val = float(p[value_col].sum())
    current_val = float(c[value_col].sum())
    return current_val - prior_val, prior_val, current_val, p.index, c.index
