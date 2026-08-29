"""Method #1 on the ladder: arithmetic bridge. Pure algebra — exact by construction,
not inference. Decomposes a revenue movement into Volume, Mix and Price effects at a
chosen segment grain. The three terms always sum exactly to the total delta; this is
the standard FP&A bridge identity, not an approximation.

    Volume effect = (U1 - U0)              * blended_ASP0
    Mix effect    = U1 * sum_s[(mix1_s - mix0_s) * price0_s]
    Price effect  = sum_s[ units1_s * (price1_s - price0_s) ]
"""
from __future__ import annotations

import pandas as pd


def price_volume_mix_bridge(
    prior_df: pd.DataFrame,
    current_df: pd.DataFrame,
    segment_dims: list[str],
    units_col: str = "units",
    revenue_col: str = "net_revenue",
) -> dict:
    def segment_stats(df: pd.DataFrame) -> pd.DataFrame:
        g = df.groupby(segment_dims).agg(units=(units_col, "sum"), revenue=(revenue_col, "sum"))
        g["price"] = g["revenue"] / g["units"].replace(0, pd.NA)
        return g

    s0 = segment_stats(prior_df)
    s1 = segment_stats(current_df)
    seg = s0.join(s1, how="outer", lsuffix="0", rsuffix="1").fillna(0.0)

    u0_total = seg["units0"].sum()
    u1_total = seg["units1"].sum()
    mix0 = (seg["units0"] / u0_total) if u0_total else 0.0
    mix1 = (seg["units1"] / u1_total) if u1_total else 0.0
    price0 = seg["price0"]

    blended_asp0 = (mix0 * price0).sum() if u0_total else 0.0
    volume_effect = (u1_total - u0_total) * blended_asp0
    mix_effect = u1_total * ((mix1 - mix0) * price0).sum()
    price_effect = (seg["units1"] * (seg["price1"] - seg["price0"])).sum()

    total_delta = float(current_df[revenue_col].sum() - prior_df[revenue_col].sum())
    return {
        "method": "arithmetic_bridge",
        "segment_dims": segment_dims,
        "volume_effect": float(volume_effect),
        "mix_effect": float(mix_effect),
        "price_effect": float(price_effect),
        "sum_of_effects": float(volume_effect + mix_effect + price_effect),
        "total_delta": total_delta,
        "reconciles_exactly": abs((volume_effect + mix_effect + price_effect) - total_delta) < 1e-6,
    }
