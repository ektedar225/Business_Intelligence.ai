"""L1 — Reconciliation & Conformance.

Projects heterogeneous sources (daily orders, weekly marketing, hourly supply
snapshots) onto one calendar, resolves SKUs to a conformed product dimension,
watermarks every fact with the freshness of its slowest contributing source, and
enforces grain-safe aggregation so a ratio metric (ASP, margin %) is always
recomputed from summed components rather than averaged across dimensions —
the single rule that prevents the most common BI bug.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class FreshnessReport:
    source: str
    latest_ts: datetime
    as_of: datetime
    lag_hours: float
    sla_hours: float
    breached: bool
    quality_tier: str


def load_sources() -> dict[str, pd.DataFrame]:
    return {
        "orders": pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["date", "week_start"]),
        "marketing": pd.read_csv(DATA_DIR / "marketing.csv", parse_dates=["week_start"]),
        "supply": pd.read_csv(DATA_DIR / "supply.csv", parse_dates=["timestamp"]),
        "dim_sku": pd.read_csv(DATA_DIR / "dim_sku.csv"),
        "cac_new_family": pd.read_csv(DATA_DIR / "cac_new_family.csv", parse_dates=["week_start"]),
    }


def conform_calendar(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Projects any date column onto the enterprise Gregorian, Monday-start ISO week
    calendar declared in the KPI contracts, so week-over-week comparisons never
    silently mix calendars."""
    out = df.copy()
    out["iso_week_start"] = pd.to_datetime(out[date_col]).dt.to_period("W-SUN").apply(lambda p: p.start_time)
    return out


def entity_resolve(orders: pd.DataFrame, dim_sku: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Joins order lines to the conformed SKU dimension. Rows whose SKU has no mapping
    are not silently dropped: they accumulate into a reported reconciliation residual."""
    merged = orders.merge(dim_sku[["sku", "product_family", "category"]], on="sku", how="left", suffixes=("", "_dim"))
    unmapped = merged[merged["product_family_dim"].isna()] if "product_family_dim" in merged else merged.iloc[0:0]
    residual = {
        "unmapped_rows": int(len(unmapped)),
        "unmapped_revenue_usd": float(unmapped["net_revenue"].sum()) if len(unmapped) else 0.0,
        "total_rows": int(len(merged)),
        "residual_share": float(len(unmapped) / len(merged)) if len(merged) else 0.0,
    }
    return merged, residual


def freshness_report(source: str, timestamps: pd.Series, as_of: datetime, sla_hours: float) -> FreshnessReport:
    latest = pd.to_datetime(timestamps).max()
    if latest.tzinfo is None:
        latest = latest.tz_localize("UTC")
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    lag_hours = (as_of - latest.to_pydatetime()).total_seconds() / 3600.0
    breached = lag_hours > sla_hours
    tier = "gold" if not breached else ("silver" if lag_hours < sla_hours * 3 else "bronze")
    return FreshnessReport(source, latest.to_pydatetime(), as_of, lag_hours, sla_hours, breached, tier)


def grain_safe_asp(df: pd.DataFrame) -> float:
    """Non-additive metric rule: ASP is always net_revenue.sum() / units.sum(),
    recomputed from summed components — never the mean of per-row unit prices."""
    units = df["units"].sum()
    return float(df["net_revenue"].sum() / units) if units else 0.0


def naive_vs_governed_margin(orders: pd.DataFrame, supply: pd.DataFrame, dim_sku: pd.DataFrame) -> dict:
    """The L1 'demo moment': averaging a margin % across regions vs. recomputing it
    from summed components. Same data, only one answer is correct."""
    cost_by_sku_region = supply.groupby(["sku", "region"])["unit_cost"].mean().rename("unit_cost")
    merged = orders.merge(dim_sku[["sku"]], on="sku", how="left")
    merged = merged.merge(cost_by_sku_region, on=["sku", "region"], how="left")
    merged["cogs"] = merged["units"] * merged["unit_cost"]

    by_region = merged.groupby("region").apply(
        lambda g: (g["net_revenue"].sum() - g["cogs"].sum()) / g["net_revenue"].sum(),
        include_groups=False,
    )
    naive_overall = float(by_region.mean())  # WRONG: averaging a ratio across regions
    governed_overall = float(
        (merged["net_revenue"].sum() - merged["cogs"].sum()) / merged["net_revenue"].sum()
    )  # RIGHT: recomputed from summed numerator/denominator
    return {
        "by_region_pct": {k: round(v * 100, 2) for k, v in by_region.items()},
        "naive_average_pct": round(naive_overall * 100, 2),
        "governed_recomputed_pct": round(governed_overall * 100, 2),
        "delta_pp": round((naive_overall - governed_overall) * 100, 2),
    }
