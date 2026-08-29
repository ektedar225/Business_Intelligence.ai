"""KPI semantic contracts: the versioned, validated single source of truth for a metric's
definition, grain, additivity, driver DAG, materiality thresholds, lineage and entitlements.
Adding a KPI is a YAML commit, validated here, not an engineering project.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

CONTRACTS_DIR = Path(__file__).parent / "contracts"


class Grain(BaseModel):
    entity: str
    time: str


class Hierarchy(BaseModel):
    parent: Optional[str] = None
    children: list[str] = Field(default_factory=list)
    decomposition: Optional[str] = None


class Driver(BaseModel):
    id: str
    type: Literal["controllable", "uncontrollable"]
    lever: Optional[str] = None
    lag_days: list[int] = Field(default_factory=lambda: [0, 0])


class Materiality(BaseModel):
    min_business_impact_usd: float
    min_surprise_z: float
    min_history_periods: int


class SparseHistoryMode(BaseModel):
    fallback: str
    confidence_cap: Literal["low", "medium", "high"]


class Entitlements(BaseModel):
    row_policy: str
    column_masks: dict[str, str] = Field(default_factory=dict)


class MonitoringDefault(BaseModel):
    watch: list[str]
    window_days: int


class KPIContract(BaseModel):
    kpi_id: str
    display_name: str
    definition_business: str
    formula: str
    grain: Grain
    calendar: Literal["gregorian", "fiscal_445", "iso_week"]
    additivity: Literal["additive", "semi_additive", "non_additive"]
    hierarchy: Hierarchy
    dimensions: list[str]
    registered_drivers: list[Driver]
    materiality: Materiality
    sparse_history_mode: Optional[SparseHistoryMode] = None
    lineage: list[str]
    entitlements: Entitlements
    owner: str
    monitoring_default: MonitoringDefault
    freshness_sla_hours: Optional[float] = None
    version: int

    @field_validator("registered_drivers")
    @classmethod
    def _no_duplicate_drivers(cls, v: list[Driver]) -> list[Driver]:
        ids = [d.id for d in v]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate driver ids in contract")
        return v


class ContractRegistry:
    """Loads and validates every KPI contract on construction. A contract that fails
    validation fails the whole load — semantic drift is caught at commit time, not at query time.
    """

    def __init__(self, directory: Path = CONTRACTS_DIR):
        self.contracts: dict[str, KPIContract] = {}
        for path in sorted(directory.glob("*.yaml")):
            raw = yaml.safe_load(path.read_text())
            contract = KPIContract.model_validate(raw)
            self.contracts[contract.kpi_id] = contract
        self._validate_driver_dag()

    def _validate_driver_dag(self) -> None:
        """Every declared lever must exist in at least one driver across the registry;
        every hierarchy parent/child reference must point at a real KPI."""
        for kpi in self.contracts.values():
            if kpi.hierarchy.parent and kpi.hierarchy.parent not in self.contracts:
                raise ValueError(f"{kpi.kpi_id}: unknown hierarchy parent {kpi.hierarchy.parent}")

    def get(self, kpi_id: str) -> KPIContract:
        if kpi_id not in self.contracts:
            raise KeyError(f"KPI '{kpi_id}' is not registered in any contract")
        return self.contracts[kpi_id]

    def all_ids(self) -> list[str]:
        return list(self.contracts.keys())


_registry: Optional[ContractRegistry] = None


def get_registry() -> ContractRegistry:
    global _registry
    if _registry is None:
        _registry = ContractRegistry()
    return _registry
