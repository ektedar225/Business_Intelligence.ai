"""Loaders for the persona registry and lever registry — both plain YAML config,
so onboarding a new persona or lever is a config commit, matching the KPI contract pattern."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

BASE = Path(__file__).parent


class MetricScope(BaseModel):
    regions: list[str]
    categories: str | list[str]


class Persona(BaseModel):
    persona_id: str
    display_name: str
    role: str
    word_budget: int
    depth: str
    vocabulary_level: str
    metric_scope: MetricScope
    decision_rights: list[str]
    lever_rights: list[str] = []
    column_masks: list[str]
    channel: list[str]
    cadence: str


class ExpectedImpact(BaseModel):
    point: float
    ci_low: float
    ci_high: float
    unit: str
    source: str


class MonitoringPlan(BaseModel):
    watch_metrics: list[str]
    window_days: int
    success_threshold: str
    rollback_trigger: str


class Lever(BaseModel):
    lever_id: str
    driver_id: str
    owner_role: str
    lead_time_days: int
    cost_to_pull: str
    expected_impact: ExpectedImpact
    constraints: list[str]
    default_monitoring_plan: MonitoringPlan


class PersonaRegistry:
    def __init__(self, path: Path = BASE / "personas.yaml"):
        raw = yaml.safe_load(path.read_text())
        self.personas = {p["persona_id"]: Persona.model_validate(p) for p in raw}

    def get(self, persona_id: str) -> Persona:
        return self.personas[persona_id]

    def all(self) -> list[Persona]:
        return list(self.personas.values())


class LeverRegistry:
    def __init__(self, path: Path = BASE / "levers.yaml"):
        raw = yaml.safe_load(path.read_text())
        self.levers = {lv["lever_id"]: Lever.model_validate(lv) for lv in raw}

    def get(self, lever_id: str) -> Optional[Lever]:
        return self.levers.get(lever_id)

    def for_driver(self, driver_id: str) -> Optional[Lever]:
        for lv in self.levers.values():
            if lv.driver_id == driver_id:
                return lv
        return None

    def all(self) -> list[Lever]:
        return list(self.levers.values())


_persona_registry: Optional[PersonaRegistry] = None
_lever_registry: Optional[LeverRegistry] = None


def get_persona_registry() -> PersonaRegistry:
    global _persona_registry
    if _persona_registry is None:
        _persona_registry = PersonaRegistry()
    return _persona_registry


def get_lever_registry() -> LeverRegistry:
    global _lever_registry
    if _lever_registry is None:
        _lever_registry = LeverRegistry()
    return _lever_registry
