"""L5 — Evidence Bundle. The contract between the deterministic world and the
generative world: immutable, typed, content-hashed. The narrative service (L7)
receives ONLY this object — no database connection, no raw tables, so it cannot
fetch or compute a number even if a prompt injection tried to make it.
"""
from __future__ import annotations

import hashlib
import json
from typing import Literal, Optional

from pydantic import BaseModel, Field

METHOD_CONFIDENCE = {
    "arithmetic_bridge": 1.0,
    "business_event_join": 0.90,
    "dimensional_contribution_slice": 0.85,
    "dimensional_contribution_mix": 0.72,
    "lagged_association": 0.50,
    "causal_did": 0.80,
    "causal_bsts": 0.78,
}

CAUSAL_METHOD_PREFIXES = ("causal_",)


class MovementFact(BaseModel):
    kpi_id: str
    period: str
    comparison_period: str
    actual: float
    baseline_forecast: Optional[float] = None
    comparison_actual: float
    wow_delta_abs: float
    wow_delta_pct: float
    impact_usd: float
    surprise_z: float
    history_periods: int


class EvidenceFact(BaseModel):
    evidence_id: str
    statement_type: Literal["driver_attribution", "structural_decomposition", "reconciliation", "data_quality"]
    label: str
    value: float
    unit: str
    method: str
    method_params: dict = Field(default_factory=dict)
    source_tables: list[str]
    freshness_ts: Optional[str] = None
    quality_tier: str = "gold"
    contribution_share: Optional[float] = None
    driver_id: Optional[str] = None
    driver_type: Optional[str] = None

    @property
    def method_confidence(self) -> float:
        return METHOD_CONFIDENCE.get(self.method, 0.5)

    @property
    def is_causal(self) -> bool:
        return self.method.startswith(CAUSAL_METHOD_PREFIXES)


class Contradiction(BaseModel):
    fact_a: str
    fact_b: str
    nature: str


class ConfidenceBreakdown(BaseModel):
    data: float
    method: float
    coverage: float
    consistency: float
    history: float
    composite: float
    band: Literal["high", "medium", "low", "abstain"]


class EntitlementScope(BaseModel):
    persona_id: str
    applied_row_policy: str
    masked_columns: list[str] = Field(default_factory=list)
    excluded_regions: list[str] = Field(default_factory=list)


class Telemetry(BaseModel):
    analyzers_run: list[str]
    wall_ms: float
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    tier: str = "T0_template"
    cache_hit: bool = False


class EvidenceBundle(BaseModel):
    event_id: str
    kpi_id: str
    period: str
    as_of_watermark: str
    movement: MovementFact
    facts: list[EvidenceFact]
    residual: dict
    contradictions: list[Contradiction] = Field(default_factory=list)
    confidence: Optional[ConfidenceBreakdown] = None
    entitlement_scope: Optional[EntitlementScope] = None
    telemetry: Optional[Telemetry] = None
    data_quality_flags: list[str] = Field(default_factory=list)
    bundle_hash: str = ""

    def compute_hash(self) -> str:
        payload = self.model_dump(exclude={"bundle_hash", "telemetry", "entitlement_scope"})
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def finalize(self) -> "EvidenceBundle":
        self.bundle_hash = self.compute_hash()
        return self

    def fact_by_id(self, evidence_id: str) -> Optional[EvidenceFact]:
        return next((f for f in self.facts if f.evidence_id == evidence_id), None)

    def scoped_to(self, entitled_regions: list[str], masked_columns: list[str], persona_id: str, row_policy: str) -> "EvidenceBundle":
        """Enforces row- and column-level entitlements ON THE BUNDLE, before any prompt
        is built — a prompt-level instruction to hide data is not a security control.
        Row policy drops any fact scoped to a region outside the persona's territory;
        column masks drop any fact that would expose a masked dimension (e.g. a
        customer_segment breakdown an analyst can see but a regional director cannot)."""
        def allowed(f: EvidenceFact) -> bool:
            region = f.method_params.get("region")
            if region is not None and region not in entitled_regions:
                return False
            if any(col in f.method_params for col in masked_columns):
                return False
            return True

        kept_facts = [f for f in self.facts if allowed(f)]
        excluded_regions = {
            f.method_params.get("region") for f in self.facts if not allowed(f) and f.method_params.get("region")
        }
        scoped = self.model_copy(deep=True)
        scoped.facts = kept_facts
        scoped.entitlement_scope = EntitlementScope(
            persona_id=persona_id,
            applied_row_policy=row_policy,
            masked_columns=masked_columns,
            excluded_regions=sorted(excluded_regions),
        )
        return scoped.finalize()
