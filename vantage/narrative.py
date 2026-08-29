"""L7 — Narrative generation and the numeric firewall.

Generation is template-based (T0): the narrative service never calls a model to
produce the demo's default text, which is the strongest possible demonstration of
"the LLM contributes zero numbers" — it isn't merely disciplined, it's architecturally
absent from the money path. `route_tier` still implements the complexity-based
T0/T1/T2 routing decision the design calls for (evaluated for every bundle and shown
in telemetry) even though this prototype's rendering path is T0 end to end; wiring a
real model behind the T1/T2 decision is a swap-in at that one call site, not a
redesign — the firewall below verifies whichever engine produced the text.

Every quantitative claim in the rendered text carries an [E-id] citation. The
firewall then re-derives every numeral from the raw text and checks it against the
evidence bundle independently of how the text was produced — template or model —
so a hallucinated number is structurally caught, not just discouraged by a prompt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from vantage.evidence import EvidenceBundle, EvidenceFact
from vantage.confidence import AbstentionResult
from vantage.registries import Persona

CAUSAL_VERBS = re.compile(r"\b(caused|drove|driven by|led to|resulted in|because of)\b", re.IGNORECASE)
NUMERAL_RE = re.compile(r"-?\$?\d[\d,]*\.?\d*\s?%?")

# Identifier patterns that legitimately contain digits but are not quantitative claims —
# a SKU code or an [E-03] citation is not a "number" the firewall should be verifying.
_IDENTIFIER_PATTERNS = [
    re.compile(r"\[E-\d+\]"),
    re.compile(r"\bSKU-\d+\b"),
    re.compile(r"\bE-\d+\b"),
    re.compile(r"\bweek[_-]\d+\b", re.IGNORECASE),
    re.compile(r"\bCMP-[\w-]+\b"),
]


def _strip_identifiers(text: str) -> str:
    for pattern in _IDENTIFIER_PATTERNS:
        text = pattern.sub(" ", text)
    return text


@dataclass
class NarrativeResult:
    headline: str
    what_changed: str
    why: list[dict]
    what_we_dont_know: str
    confidence_statement: str
    evidence_ids_used: list[str]
    full_text: str
    tier: str


@dataclass
class FirewallVerdict:
    passed: bool
    orphan_numerals: list[str] = field(default_factory=list)
    causal_overreach: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def route_tier(bundle: EvidenceBundle) -> str:
    """Complexity-based tier decision — evaluated for every bundle regardless of which
    engine ends up rendering the text, so the routing logic itself is demoable."""
    n_drivers = len([f for f in bundle.facts if f.statement_type == "driver_attribution"])
    if bundle.contradictions or (bundle.confidence and bundle.confidence.band in ("low", "abstain")):
        return "T2_frontier"
    if n_drivers >= 3:
        return "T1_small_model"
    return "T0_template"


def _fmt_usd(v: float) -> str:
    return f"${v:,.0f}" if abs(v) >= 1 else f"${v:.2f}"


def _fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _driver_verb(method: str) -> str:
    if method.startswith("causal_"):
        return "caused"
    if method == "business_event_join":
        return "coincided with"
    if method.startswith("dimensional_contribution"):
        return "accounts for"
    return "is associated with"


def render_narrative(
    bundle: EvidenceBundle,
    persona: Persona,
    driver_facts: Optional[list[EvidenceFact]] = None,
) -> NarrativeResult:
    tier = route_tier(bundle)
    m = bundle.movement
    driver_facts = driver_facts or [f for f in bundle.facts if f.statement_type == "driver_attribution" and f.driver_id != "residual"]
    driver_facts = sorted(driver_facts, key=lambda f: abs(f.value), reverse=True)
    max_drivers = {"summary": 2, "segment": 3, "sku": 4, "full": len(driver_facts)}.get(persona.depth, 3)
    shown = driver_facts[:max_drivers]

    direction = "fell" if m.wow_delta_abs < 0 else "rose"
    headline = f"{bundle.kpi_id.replace('_', ' ').title()} {direction} {_fmt_pct(abs(m.wow_delta_pct))} WoW ({_fmt_usd(m.wow_delta_abs)})"

    what_changed = (
        f"{bundle.kpi_id.replace('_', ' ').title()} {direction} to {_fmt_usd(m.actual)} in {m.period}, "
        f"down {_fmt_usd(abs(m.wow_delta_abs))} ({_fmt_pct(m.wow_delta_pct)}) from {_fmt_usd(m.comparison_actual)} "
        f"in {m.comparison_period}."
    )

    why_items = []
    evidence_ids: list[str] = []
    for f in shown:
        verb = _driver_verb(f.method)
        share_txt = f" ({_fmt_pct(abs(f.contribution_share))} of the movement)" if f.contribution_share is not None else ""
        text = f"{f.label} {verb} {_fmt_usd(f.value)}{share_txt} [{f.evidence_id}]"
        why_items.append({"driver": f.driver_id, "text": text, "evidence_ids": [f.evidence_id], "method": f.method})
        evidence_ids.append(f.evidence_id)

    residual = bundle.residual or {}
    residual_share = residual.get("residual_share")
    residual_txt = (
        f"{_fmt_pct(abs(residual_share))} of the movement is unattributed residual." if residual_share is not None else ""
    )
    stale_note = ""
    if bundle.data_quality_flags:
        stale_note = f" Data-quality flags active: {', '.join(bundle.data_quality_flags)}."
    masked_note = ""
    if bundle.entitlement_scope and bundle.entitlement_scope.masked_columns:
        masked_note = f" Column-level detail not shown at your access level: {', '.join(bundle.entitlement_scope.masked_columns)}."
    what_we_dont_know = (residual_txt + stale_note + masked_note).strip() or "No material gaps identified."

    band = bundle.confidence.band if bundle.confidence else "unknown"
    confidence_statement = (
        f"Confidence: {band.upper()} (composite {bundle.confidence.composite:.2f}) — "
        f"based on {bundle.confidence.history:.0%} of the required history, "
        f"{bundle.confidence.coverage:.0%} of the movement explained."
        if bundle.confidence
        else "Confidence not computed."
    )

    parts = [headline, "", what_changed, ""]
    for item in why_items:
        parts.append("- " + item["text"])
    parts += ["", f"What we don't know: {what_we_dont_know}", "", confidence_statement]
    full_text = "\n".join(parts)

    return NarrativeResult(
        headline=headline,
        what_changed=what_changed,
        why=why_items,
        what_we_dont_know=what_we_dont_know,
        confidence_statement=confidence_statement,
        evidence_ids_used=evidence_ids,
        full_text=full_text,
        tier=tier,
    )


def render_abstention_narrative(abstention: AbstentionResult) -> str:
    lines = [f"[ABSTAIN — {abstention.mode}]", "", abstention.reliable_findings, "", f"Blocker: {abstention.blocker}", f"Why it matters: {abstention.why_it_matters}", f"Resolution: {abstention.resolution_path} (owner: {abstention.eta_or_owner})", f"What you can still do: {abstention.what_you_can_still_do}"]
    if abstention.clarifying_question:
        lines.append(f"Clarifying question: {abstention.clarifying_question}")
    for h in abstention.competing_hypotheses:
        lines.append(f"- Hypothesis: {h}")
    return "\n".join(lines)


def _extract_numerals(text: str) -> list[float]:
    out = []
    for raw in NUMERAL_RE.findall(text):
        cleaned = raw.replace("$", "").replace(",", "").replace("%", "").strip()
        if not cleaned or cleaned in ("-", "."):
            continue
        try:
            val = float(cleaned)
        except ValueError:
            continue
        if "%" in raw:
            val = val / 100.0
        out.append(val)
    return out


def _known_values(bundle: EvidenceBundle) -> list[float]:
    vals: list[float] = []
    m = bundle.movement
    for v in [m.actual, m.wow_delta_abs, m.wow_delta_pct, m.comparison_actual, m.baseline_forecast, m.impact_usd, m.surprise_z]:
        try:
            fv = float(v)
            if fv == fv:  # not NaN
                vals.extend([fv, abs(fv)])
        except (TypeError, ValueError):
            pass
    for f in bundle.facts:
        vals.extend([f.value, abs(f.value)])
        if f.contribution_share is not None:
            vals.extend([f.contribution_share, abs(f.contribution_share)])
    if bundle.confidence:
        vals.extend([bundle.confidence.composite, bundle.confidence.data, bundle.confidence.method, bundle.confidence.coverage, bundle.confidence.consistency, bundle.confidence.history])
    return vals


def _tolerance_for(k: float) -> float:
    """Tolerance must scale with magnitude. Fraction/percentage-scale known values
    (shares, confidence components — everything in roughly [-1, 1]) get a tight floor
    sized to one-decimal-place display rounding (~0.1 percentage point); anything
    looser would let two genuinely different percentages, or a fabricated one against
    an unrelated zero-valued fact, pass as "close enough". Dollar-scale values get a
    floor sized to whole-currency-unit rounding instead."""
    floor = 0.006 if abs(k) <= 1 else 1.0
    return max(floor, abs(k) * 0.02)


def numeric_firewall(text: str, bundle: EvidenceBundle) -> FirewallVerdict:
    """Extracts every numeral from the text and requires each to match some value in
    the evidence bundle within tolerance. This is ~30 lines of logic and it is what
    makes a hallucinated figure structurally impossible to ship, regardless of which
    tier produced the text."""
    known = _known_values(bundle)
    orphans = []
    for val in _extract_numerals(_strip_identifiers(text)):
        if not any(abs(val - k) <= _tolerance_for(k) for k in known):
            orphans.append(str(val))
    return FirewallVerdict(passed=len(orphans) == 0, orphan_numerals=orphans)


_EVIDENCE_CITE_RE = re.compile(r"\[(E-\d+)\]")


def causal_language_gate(text: str, bundle: EvidenceBundle) -> FirewallVerdict:
    """Causal verbs are permitted only on a sentence that cites a fact produced by a
    causal_* method. Scans every sentence of the rendered text — not just the
    structured driver list — so a causal claim smuggled in anywhere (an appended
    sentence, an aside) is still caught."""
    violations = []
    for sentence in text.split("\n"):
        if not CAUSAL_VERBS.search(sentence):
            continue
        cited_ids = _EVIDENCE_CITE_RE.findall(sentence)
        cited_facts = [bundle.fact_by_id(eid) for eid in cited_ids]
        justified = any(f is not None and f.is_causal for f in cited_facts)
        if not justified:
            violations.append(sentence.strip())
    return FirewallVerdict(passed=len(violations) == 0, causal_overreach=violations)


def verify_narrative(narrative: NarrativeResult, bundle: EvidenceBundle) -> FirewallVerdict:
    numeric = numeric_firewall(narrative.full_text, bundle)
    causal = causal_language_gate(narrative.full_text, bundle)
    return FirewallVerdict(
        passed=numeric.passed and causal.passed,
        orphan_numerals=numeric.orphan_numerals,
        causal_overreach=causal.causal_overreach,
    )


def inject_violation_demo(narrative: NarrativeResult) -> NarrativeResult:
    """Deliberately corrupts a passing narrative with a fabricated causal claim and an
    orphan numeral, for the live firewall-catch demo. Never used on the real output path."""
    corrupted = narrative.full_text + (
        "\n- This was primarily caused by a 3.4% swing in competitor pricing in the region. [E-99]"
    )
    return NarrativeResult(**{**narrative.__dict__, "full_text": corrupted})
