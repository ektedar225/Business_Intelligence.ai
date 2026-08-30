"""Method #2 on the ladder: dimensional contribution. Two complementary techniques:

`beam_search_slices` is Adtributor-style exploratory attribution — for an additive
metric, summing the delta within any row-filtered slice is an EXACT partition of the
total delta (no inference), so it is cheap and safe to search. It is beam-searched
over the dimension lattice (single dims, then pairwise combinations seeded from the
best single-dim slices) to avoid combinatorial explosion, and surfaces the candidate
hot-spots that business-event-join and mix analysis then explain.

`mix_variance_effect` isolates the pure compositional-shift contribution of one
categorical dimension (e.g. channel) — how much revenue moved purely because the
proportion of volume in each category changed, holding per-category prices at their
prior value. This is exact for the two-way case (single dimension) and is what
separates "channel mix shifted" from "volume changed" without conflating them.
"""
from __future__ import annotations

from itertools import combinations

import pandas as pd

def beam_search_slices(
    prior_df: pd.DataFrame,
    current_df: pd.DataFrame,
    dims: list[str],
    value_col: str = "net_revenue",
    top_k: int = 5,
    depth: int = 2,
) -> list[dict]:
    prior_df = prior_df.copy()
    current_df = current_df.copy()
    prior_df["_side"] = "prior"
    current_df["_side"] = "current"
    combined = pd.concat([prior_df, current_df], ignore_index=True)

    def score(group_dims: list[str]) -> pd.DataFrame:
        piv = combined.groupby(group_dims + ["_side"])[value_col].sum().unstack("_side", fill_value=0.0)
        piv["delta"] = piv.get("current", 0.0) - piv.get("prior", 0.0)
        return piv

    results: list[dict] = []
    frontier: list[tuple[list[str], pd.DataFrame]] = []
    for d in dims:
        piv = score([d])
        frontier.append(([d], piv))
        for idx, row in piv.reindex(piv["delta"].abs().sort_values(ascending=False).index).head(top_k).iterrows():
            key = idx if isinstance(idx, tuple) else (idx,)
            results.append(
                {
                    "dims": [d],
                    "values": list(key),
                    "delta": float(row["delta"]),
                    "prior": float(row.get("prior", 0.0)),
                    "current": float(row.get("current", 0.0)),
                }
            )

    if depth >= 2:
        top_single = sorted(results, key=lambda r: abs(r["delta"]), reverse=True)[:top_k]
        for r in top_single:
            base_dim = r["dims"][0]
            base_val = r["values"][0]
            for d2 in dims:
                if d2 == base_dim:
                    continue
                sub_prior = prior_df[prior_df[base_dim] == base_val]
                sub_current = current_df[current_df[base_dim] == base_val]
                piv = (
                    pd.concat([sub_prior.assign(_side="prior"), sub_current.assign(_side="current")])
                    .groupby([d2, "_side"])[value_col]
                    .sum()
                    .unstack("_side", fill_value=0.0)
                )
                piv["delta"] = piv.get("current", 0.0) - piv.get("prior", 0.0)
                for val2, row in piv.reindex(piv["delta"].abs().sort_values(ascending=False).index).head(2).iterrows():
                    results.append(
                        {
                            "dims": [base_dim, d2],
                            "values": [base_val, val2],
                            "delta": float(row["delta"]),
                            "prior": float(row.get("prior", 0.0)),
                            "current": float(row.get("current", 0.0)),
                        }
                    )

    deduped: dict[frozenset, dict] = {}
    for r in results:
        key = frozenset(zip(r["dims"], r["values"]))
        deduped[key] = r
    ranked = sorted(deduped.values(), key=lambda r: abs(r["delta"]), reverse=True)
    return ranked[: top_k * 3]

def mix_variance_effect(
    prior_df: pd.DataFrame,
    current_df: pd.DataFrame,
    dimension: str,
    units_col: str = "units",
    revenue_col: str = "net_revenue",
) -> dict:
    p = prior_df.groupby(dimension).agg(units=(units_col, "sum"), revenue=(revenue_col, "sum"))
    c = current_df.groupby(dimension).agg(units=(units_col, "sum"), revenue=(revenue_col, "sum"))
    joined = p.join(c, how="outer", lsuffix="_prior", rsuffix="_current").fillna(0.0)

    u0 = joined["units_prior"].sum()
    u1 = joined["units_current"].sum()
    share0 = joined["units_prior"] / u0 if u0 else joined["units_prior"] * 0.0
    share1 = joined["units_current"] / u1 if u1 else joined["units_current"] * 0.0
    price0 = (joined["revenue_prior"] / joined["units_prior"].replace(0, pd.NA)).fillna(0.0)

    mix_effect = float(u1 * ((share1 - share0) * price0).sum())
    by_value = ((share1 - share0) * price0 * u1).to_dict()
    return {
        "method": "dimensional_contribution_mix",
        "dimension": dimension,
        "mix_effect": mix_effect,
        "share_prior": share0.round(4).to_dict(),
        "share_current": share1.round(4).to_dict(),
        "by_value_contribution": {k: float(v) for k, v in by_value.items()},
    }
