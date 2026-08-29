"""Minimal rule-based intent resolver for the conversational entry point (P1's job,
without a model call): maps free text to a registered kpi_id, or triggers
abstention mode A when a term is genuinely ambiguous. A vague business term like
"performance" really can mean more than one governed KPI — that ambiguity is not
manufactured for the demo, it is why the clarify mode exists at all.
"""
from __future__ import annotations

from vantage.confidence import AbstentionResult, clarify_ambiguous_kpi

SYNONYMS: dict[str, list[str]] = {
    "revenue": ["net_revenue"],
    "sales": ["net_revenue"],
    "net revenue": ["net_revenue"],
    "margin": ["gross_margin_pct"],
    "profitability": ["gross_margin_pct"],
    "gross margin": ["gross_margin_pct"],
    "units": ["units_sold"],
    "volume": ["units_sold"],
    "price": ["asp"],
    "asp": ["asp"],
    "average selling price": ["asp"],
    "cac": ["cac"],
    "acquisition cost": ["cac"],
    "performance": ["net_revenue", "gross_margin_pct"],  # genuinely ambiguous business term
}


def resolve_intent(text: str) -> tuple[str | None, AbstentionResult | None]:
    lowered = text.lower()
    candidates: set[str] = set()
    for term, kpi_ids in SYNONYMS.items():
        if term in lowered:
            candidates.update(kpi_ids)
    if len(candidates) == 0:
        return None, None
    if len(candidates) > 1:
        matched_term = next(t for t, ids in SYNONYMS.items() if t in lowered and len(ids) > 1)
        return None, clarify_ambiguous_kpi(matched_term, sorted(candidates))
    return next(iter(candidates)), None
