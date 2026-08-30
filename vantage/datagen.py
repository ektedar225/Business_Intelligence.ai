"""Synthetic data generator for three deliberately mismatched sources (S1 Orders, S2
Marketing, S3 Supply/Inventory) with known, injected ground-truth drivers for a
multi-factor Net Revenue movement, a stale-feed abstention scenario, and a
sparse-history product launch. Ground truth is written alongside the data so the
Recovery Scorecard (vantage/scorecard.py) can measure whether the diagnosis engine
actually finds what was put in, rather than merely sounding plausible.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

REGIONS = ["EMEA", "AMER", "APAC"]
CHANNELS = ["direct", "marketplace"]
SEGMENTS = ["Consumer", "SMB", "Enterprise"]
SEGMENT_SHARE = {"Consumer": 0.5, "SMB": 0.3, "Enterprise": 0.2}

SKU_CATALOG = {
    "SKU-1001": ("family_a", "Electronics", 120.0),
    "SKU-4471": ("family_b", "Electronics", 95.0),
    "SKU-4472": ("family_b", "Electronics", 80.0),
    "SKU-2001": ("family_c", "Home", 45.0),
    "SKU-3001": ("family_d", "Apparel", 30.0),
}
MARKETPLACE_PRICE_FACTOR = 0.88

REGION_DEMAND_WEIGHT = {"EMEA": 1.0, "AMER": 1.15, "APAC": 0.85}
REGION_COST_MULTIPLIER = {"EMEA": 1.0, "AMER": 0.95, "APAC": 1.55}
DOW_SEASONALITY = {0: 1.0, 1: 1.0, 2: 1.02, 3: 1.02, 4: 1.05, 5: 0.85, 6: 0.75}

N_WEEKS = 30
START_DATE = datetime(2026, 1, 5, tzinfo=timezone.utc)
CURRENT_WEEK_IDX = N_WEEKS - 1
PRIOR_WEEK_IDX = N_WEEKS - 2

PROMO_SKU, PROMO_REGION = "SKU-1001", "AMER"
PROMO_WEEKS = {26, 27, 28, 29}
PROMO_DEPTH = 0.15
PROMO_LIFT = 0.74

STOCKOUT_SKU, STOCKOUT_REGION, STOCKOUT_WAREHOUSE = "SKU-4471", "EMEA", "DE"
STOCKOUT_WEEK = 30
STOCKOUT_DAYS = {3, 4}

CHANNEL_SPLIT_PRIOR = {"direct": 0.65, "marketplace": 0.35}
CHANNEL_SPLIT_CURRENT = {"direct": 0.53, "marketplace": 0.47}
CHANNEL_SHIFT_WEEK = 30

RETURNS_RATE = 0.02
NOISE_STD = 0.03

GM_STALE_WAREHOUSE = "DE"
GM_SLA_HOURS = 6.0
GM_ACTUAL_STALENESS_HOURS = 26.0

NEW_FAMILY = "family_e"
NEW_FAMILY_LAUNCH_WEEK = 28

def _week_start(week_idx_0based: int) -> datetime:
    return START_DATE + timedelta(weeks=week_idx_0based)

def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)

def generate_orders(seed: int = 7) -> pd.DataFrame:
    rng = _rng(seed)
    rows = []
    for week0 in range(N_WEEKS):
        week1 = week0 + 1
        for day_offset in range(7):
            date = _week_start(week0) + timedelta(days=day_offset)
            dow = date.weekday()
            for region in REGIONS:
                for sku, (family, category, base_price) in SKU_CATALOG.items():
                    is_promo_slice = (
                        sku == PROMO_SKU and region == PROMO_REGION and week1 in PROMO_WEEKS
                    )
                    is_stockout_slice = (
                        sku == STOCKOUT_SKU
                        and region == STOCKOUT_REGION
                        and week1 == STOCKOUT_WEEK
                        and (day_offset + 1) in STOCKOUT_DAYS
                    )
                    base_units = 9.0 * REGION_DEMAND_WEIGHT[region] * DOW_SEASONALITY[dow]
                    if is_promo_slice:
                        base_units *= 1.0 + PROMO_LIFT
                    noise = float(rng.normal(1.0, NOISE_STD))
                    total_units = max(0.0, base_units * noise)
                    if is_stockout_slice:
                        total_units = 0.0

                    split = (
                        CHANNEL_SPLIT_CURRENT if week1 == CHANNEL_SHIFT_WEEK else CHANNEL_SPLIT_PRIOR
                    )
                    for channel in CHANNELS:
                        units = total_units * split[channel]
                        if units <= 0:
                            continue
                        price = base_price * (
                            MARKETPLACE_PRICE_FACTOR if channel == "marketplace" else 1.0
                        )
                        discount_rate = PROMO_DEPTH if is_promo_slice else 0.0
                        gross_amount = units * price
                        discount_amount = gross_amount * discount_rate
                        returns_amount = gross_amount * RETURNS_RATE
                        for seg in SEGMENTS:
                            seg_share = SEGMENT_SHARE[seg]
                            rows.append(
                                {
                                    "date": date.date().isoformat(),
                                    "week_start": _week_start(week0).date().isoformat(),
                                    "week_idx": week1,
                                    "region": region,
                                    "channel": channel,
                                    "category": category,
                                    "product_family": family,
                                    "sku": sku,
                                    "customer_segment": seg,
                                    "units": units * seg_share,
                                    "gross_amount": gross_amount * seg_share,
                                    "discount_amount": discount_amount * seg_share,
                                    "returns_amount": returns_amount * seg_share,
                                }
                            )
    df = pd.DataFrame(rows)
    df["net_revenue"] = df["gross_amount"] - df["discount_amount"] - df["returns_amount"]
    return df

def generate_marketing(seed: int = 11) -> pd.DataFrame:
    rng = _rng(seed)
    rows = []
    families = sorted({v[0] for v in SKU_CATALOG.values()})
    for week0 in range(N_WEEKS):
        week1 = week0 + 1
        ws = _week_start(week0).date().isoformat()
        for family in families:
            for region in REGIONS:
                base_spend = 4000 * (1.15 if region == "AMER" else 1.0)
                spend = float(base_spend * rng.normal(1.0, 0.05))
                is_promo = family == PROMO_SKU_FAMILY() and region == PROMO_REGION and week1 in PROMO_WEEKS
                if is_promo:
                    spend *= 1.6
                rows.append(
                    {
                        "week_start": ws,
                        "week_idx": week1,
                        "campaign_id": f"CMP-{family}-{region}",
                        "product_family": family,
                        "region": region,
                        "spend": spend,
                        "impressions": int(spend * 40),
                        "promo_flag": bool(is_promo),
                        "promo_depth": PROMO_DEPTH if is_promo else 0.0,
                    }
                )
    for week1 in range(NEW_FAMILY_LAUNCH_WEEK, N_WEEKS + 1):
        ws = _week_start(week1 - 1).date().isoformat()
        rows.append(
            {
                "week_start": ws,
                "week_idx": week1,
                "campaign_id": f"CMP-{NEW_FAMILY}-LAUNCH",
                "product_family": NEW_FAMILY,
                "region": "EMEA",
                "spend": float(6000 * rng.normal(1.0, 0.05)),
                "impressions": 90000,
                "promo_flag": True,
                "promo_depth": 0.0,
            }
        )
    return pd.DataFrame(rows)

def PROMO_SKU_FAMILY() -> str:
    return SKU_CATALOG[PROMO_SKU][0]

def generate_supply(seed: int = 13, as_of: datetime | None = None) -> pd.DataFrame:
    """Hourly snapshot feed. S3 is deliberately the lowest-quality, latest-arriving
    source: rows for the final GM_ACTUAL_STALENESS_HOURS before as_of are withheld to
    simulate a feed that has breached its 6h freshness SLA (used by the abstain demo).
    """
    rng = _rng(seed)
    as_of = as_of or (_week_start(CURRENT_WEEK_IDX) + timedelta(days=6, hours=23))
    warehouse_by_region = {"EMEA": "DE", "AMER": "US-East", "APAC": "SG"}
    rows = []
    unit_costs = {sku: base_price * 0.55 for sku, (_, _, base_price) in SKU_CATALOG.items()}
    cutoff = as_of - timedelta(hours=GM_ACTUAL_STALENESS_HOURS)
    t = START_DATE
    while t <= as_of:
        for sku, (family, category, _) in SKU_CATALOG.items():
            for region in REGIONS:
                warehouse = warehouse_by_region[region]
                if sku == STOCKOUT_SKU and region == STOCKOUT_REGION and warehouse == STOCKOUT_WAREHOUSE:
                    week1 = ((t - START_DATE).days // 7) + 1
                    day1 = ((t - START_DATE).days % 7) + 1
                    stockout = week1 == STOCKOUT_WEEK and day1 in STOCKOUT_DAYS
                else:
                    stockout = False
                on_hand = 0 if stockout else int(max(0, rng.normal(400, 40)))
                cost = unit_costs[sku] * REGION_COST_MULTIPLIER[region] * float(rng.normal(1.0, 0.01))
                if t > cutoff:
                    continue
                rows.append(
                    {
                        "timestamp": t.isoformat(),
                        "sku": sku,
                        "warehouse": warehouse,
                        "region": region,
                        "on_hand_units": on_hand,
                        "stockout_flag": bool(stockout),
                        "unit_cost": cost,
                    }
                )
        t += timedelta(hours=1)
    return pd.DataFrame(rows)

def generate_cac_new_family(seed: int = 17) -> pd.DataFrame:
    """A newly launched product line with only 3 weeks of history by the current week —
    too little for the seasonal baseline, forcing the sparse-history fallback
    (plan-vs-actual / peer-cohort, confidence capped Low)."""
    rng = _rng(seed)
    new_customers_by_week = {28: 40, 29: 55, 30: 22}
    rows = []
    for week1 in range(NEW_FAMILY_LAUNCH_WEEK, N_WEEKS + 1):
        ws = _week_start(week1 - 1).date().isoformat()
        spend = float(6000 * rng.normal(1.0, 0.05))
        new_customers = new_customers_by_week.get(week1, 35)
        rows.append(
            {
                "week_start": ws,
                "week_idx": week1,
                "product_family": NEW_FAMILY,
                "region": "EMEA",
                "spend": spend,
                "new_customers": new_customers,
                "cac": spend / new_customers,
            }
        )
    return pd.DataFrame(rows)

def sku_dimension_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"sku": sku, "product_family": fam, "category": cat, "base_price": price}
            for sku, (fam, cat, price) in SKU_CATALOG.items()
        ]
    )

@dataclass
class GroundTruthDriver:
    driver_id: str
    label: str
    true_dollar_impact: float
    true_share: float

def compute_ground_truth(orders: pd.DataFrame) -> dict:
    """Directly measures, from the generated data, the dollar impact of each injected
    driver on the week-over-week Net Revenue movement — this is the answer key the
    diagnosis engine is blind to and the Recovery Scorecard grades against.
    """
    cur = orders[orders.week_idx == CURRENT_WEEK_IDX + 1]
    prior = orders[orders.week_idx == PRIOR_WEEK_IDX + 1]
    total_delta = cur.net_revenue.sum() - prior.net_revenue.sum()

    def slice_rev(df, sku=None, region=None):
        d = df
        if sku:
            d = d[d.sku == sku]
        if region:
            d = d[d.region == region]
        return d.net_revenue.sum()

    promo_delta = slice_rev(cur, PROMO_SKU, PROMO_REGION) - slice_rev(prior, PROMO_SKU, PROMO_REGION)
    stockout_delta = slice_rev(cur, STOCKOUT_SKU, STOCKOUT_REGION) - slice_rev(
        prior, STOCKOUT_SKU, STOCKOUT_REGION
    )

    excl = cur[~(((cur.sku == PROMO_SKU) & (cur.region == PROMO_REGION)) | ((cur.sku == STOCKOUT_SKU) & (cur.region == STOCKOUT_REGION)))]
    total_units_excl = excl.units.sum()
    avg_direct_price = SKU_CATALOG_avg_price("direct")
    avg_marketplace_price = SKU_CATALOG_avg_price("marketplace")
    split_shift = CHANNEL_SPLIT_PRIOR["direct"] - CHANNEL_SPLIT_CURRENT["direct"]
    channel_mix_delta = -total_units_excl * split_shift * (avg_direct_price - avg_marketplace_price)

    explained = promo_delta + stockout_delta + channel_mix_delta
    noise_delta = total_delta - explained

    drivers = [
        GroundTruthDriver("promo_calendar", "Promo campaign ended (SKU-1001, AMER)", promo_delta, promo_delta / total_delta),
        GroundTruthDriver("stockout_rate", "SKU-4471 stockout in DE warehouse", stockout_delta, stockout_delta / total_delta),
        GroundTruthDriver("channel_mix", "Mix shift toward lower-ASP marketplace channel", channel_mix_delta, channel_mix_delta / total_delta),
        GroundTruthDriver("noise", "Unattributable / residual noise", noise_delta, noise_delta / total_delta),
    ]
    return {
        "total_delta_usd": total_delta,
        "total_delta_pct": total_delta / prior.net_revenue.sum(),
        "prior_week_revenue": prior.net_revenue.sum(),
        "current_week_revenue": cur.net_revenue.sum(),
        "drivers": [asdict(d) for d in drivers],
    }

def SKU_CATALOG_avg_price(channel: str) -> float:
    factor = MARKETPLACE_PRICE_FACTOR if channel == "marketplace" else 1.0
    prices = [p for _, _, p in SKU_CATALOG.values()]
    return float(np.mean(prices)) * factor

def build_and_persist(seed: int = 7) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    orders = generate_orders(seed)
    marketing = generate_marketing(seed + 1)
    as_of = _week_start(CURRENT_WEEK_IDX) + timedelta(days=6, hours=23)
    supply = generate_supply(seed + 2, as_of=as_of)
    dim_sku = sku_dimension_table()
    cac_new_family = generate_cac_new_family(seed + 3)

    orders.to_csv(DATA_DIR / "orders.csv", index=False)
    marketing.to_csv(DATA_DIR / "marketing.csv", index=False)
    supply.to_csv(DATA_DIR / "supply.csv", index=False)
    dim_sku.to_csv(DATA_DIR / "dim_sku.csv", index=False)
    cac_new_family.to_csv(DATA_DIR / "cac_new_family.csv", index=False)

    ground_truth = compute_ground_truth(orders)
    meta = {
        "as_of": as_of.isoformat(),
        "current_week_start": _week_start(CURRENT_WEEK_IDX).date().isoformat(),
        "prior_week_start": _week_start(PRIOR_WEEK_IDX).date().isoformat(),
        "gm_stale_warehouse": GM_STALE_WAREHOUSE,
        "gm_sla_hours": GM_SLA_HOURS,
        "gm_actual_staleness_hours": GM_ACTUAL_STALENESS_HOURS,
        "new_family": NEW_FAMILY,
        "new_family_launch_week": NEW_FAMILY_LAUNCH_WEEK,
        "current_week_idx": CURRENT_WEEK_IDX + 1,
        "prior_week_idx": PRIOR_WEEK_IDX + 1,
    }
    payload = {"ground_truth": ground_truth, "meta": meta}
    (DATA_DIR / "ground_truth.json").write_text(json.dumps(payload, indent=2, default=str))
    return payload

if __name__ == "__main__":
    result = build_and_persist()
    print(json.dumps(result, indent=2, default=str))
