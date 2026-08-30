"""Conversational intent resolver for VANTAGE.
Uses Google Gemini LLM for natural language understanding with intelligent ambiguity
detection and seamless fallback to rule-based mapping when offline.
"""
from __future__ import annotations

import json
from typing import Optional

from vantage.confidence import AbstentionResult, clarify_ambiguous_kpi
from vantage.llm import call_gemini

REGISTERED_KPIS = ["net_revenue", "gross_margin_pct", "units_sold", "asp", "cac"]

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
    "performance": ["net_revenue", "gross_margin_pct"],
}

INTENT_SYSTEM_INSTRUCTION = """You are an intent understanding engine for the VANTAGE Business Intelligence platform.
Registered KPIs:
- 'net_revenue': Total revenue, dollar sales, top-line revenue, financial sales performance
- 'gross_margin_pct': Profitability, gross margin percentage, unit margin rate
- 'units_sold': Sales volume, quantity of units, number of items sold
- 'asp': Average selling price, price per unit
- 'cac': Customer acquisition cost, marketing acquisition efficiency per new customer

Instructions:
1. If the user query relates to revenue or general sales (dollars), map to 'net_revenue'. If it explicitly asks about unit count or volume, map to 'units_sold'.
2. If the user query is genuinely ambiguous across multiple KPIs (e.g. 'performance', 'overall financial health', 'growth', 'business outcomes'), set is_ambiguous=true, identify the ambiguous_term, and list candidate KPI IDs in candidates.
3. If the query does not relate to business metrics or registered KPIs, set matched_kpi=null.

Output MUST be valid JSON in this exact structure:
{"matched_kpi": string or null, "is_ambiguous": bool, "ambiguous_term": string or null, "candidates": [string]}"""

def _resolve_rule_based(text: str) -> tuple[str | None, AbstentionResult | None]:
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

def resolve_intent(text: str, use_llm: bool = True) -> tuple[str | None, AbstentionResult | None]:
    if not use_llm:
        return _resolve_rule_based(text)

    prompt = f'User query: "{text}"'
    resp = call_gemini(
        prompt=prompt,
        system_instruction=INTENT_SYSTEM_INSTRUCTION,
        json_mode=True,
        temperature=0.0,
        timeout_secs=6,
    )

    if resp.error or not resp.text:
        return _resolve_rule_based(text)

    try:
        parsed = json.loads(resp.text)
        if parsed.get("is_ambiguous") and len(parsed.get("candidates", [])) > 1:
            term = parsed.get("ambiguous_term") or text
            valid_cands = [c for c in parsed["candidates"] if c in REGISTERED_KPIS]
            if len(valid_cands) > 1:
                return None, clarify_ambiguous_kpi(term, valid_cands)

        matched = parsed.get("matched_kpi")
        if matched and matched in REGISTERED_KPIS:
            return matched, None
        if matched is None and not parsed.get("is_ambiguous"):
            rule_kpi, rule_abstain = _resolve_rule_based(text)
            return rule_kpi, rule_abstain
    except Exception:
        return _resolve_rule_based(text)

    return _resolve_rule_based(text)
