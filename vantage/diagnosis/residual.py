"""Residual accounting: after every driver on the ladder has claimed its share of the
movement, what's left over is stated explicitly rather than folded silently into the
last driver found. A large unexplained share is a signal to lower confidence and
soften the narrative's claim, not a reason to keep searching until the residual
disappears.
"""
from __future__ import annotations


def residual_accounting(total_delta: float, attributed: dict[str, float]) -> dict:
    explained = sum(attributed.values())
    residual = total_delta - explained
    return {
        "total_delta": total_delta,
        "attributed": dict(attributed),
        "explained_amount": explained,
        "explained_share": explained / total_delta if total_delta else 0.0,
        "residual_amount": residual,
        "residual_share": residual / total_delta if total_delta else 0.0,
    }
