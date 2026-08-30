"""Tests for the remaining completion items:
  - Scenario 4: Competing Hypotheses (Mode B abstention)
  - Proactive alerts engine
  - Drift detection (PSI + rank correlation)
  - Causal inference DiD estimator
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Scenario 4 triggers Mode B competing-hypotheses abstention
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario4_competing_hypotheses_abstains_mode_B():
    from vantage.pipeline import build_scenario4_bundle
    bundle, abstention, debug = build_scenario4_bundle()

    # The bundle must be a real EvidenceBundle for asp KPI
    assert bundle.kpi_id == "asp"

    # Mode B abstention must fire
    assert abstention.mode == "B_competing_hypotheses"

    # Must surface both hypotheses with discriminating tests
    assert len(abstention.competing_hypotheses) == 2
    h_ids = {h["id"] for h in abstention.competing_hypotheses}
    assert "H1_price_elasticity" in h_ids
    assert "H2_competitor_price" in h_ids

    # Each hypothesis must have a discriminating test
    for h in abstention.competing_hypotheses:
        assert len(h.get("discriminating_test", "")) > 10, \
            f"Hypothesis {h['id']} is missing a discriminating test"

    # Confidence consistency score must be penalised (contradictions=1)
    assert bundle.confidence is not None
    assert bundle.confidence.consistency < 1.0, \
        "Contradictions should reduce consistency score below 1.0"

    print(f"Scenario 4 Mode B: {abstention.mode}, hypotheses: {[h['id'] for h in abstention.competing_hypotheses]}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Alert engine fires for a high-surprise-z bundle
# ─────────────────────────────────────────────────────────────────────────────

def test_alerts_fire_for_high_severity_movement():
    from vantage.alerts import evaluate_alerts, DEFAULT_RULES
    from vantage.pipeline import build_scenario1_bundle

    bundle, _ = build_scenario1_bundle()
    alerts = evaluate_alerts(bundle)

    # Scenario 1 is a significant net revenue drop — at least one alert should fire
    # (large-wow-move rule threshold is 5%)
    assert len(alerts) >= 1, "Expected at least 1 alert for Scenario 1 net revenue drop"

    # All alerts must have required fields
    for a in alerts:
        assert a.rule_id
        assert a.kpi_id
        assert a.severity in ("info", "warning", "critical")
        assert a.headline
        assert len(a.channels) >= 1

    print(f"Alerts fired: {[a.rule_id for a in alerts]}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Drift detection — PSI + rank correlation
# ─────────────────────────────────────────────────────────────────────────────

def test_drift_detects_distribution_shift():
    from vantage.drift import detect_data_drift, detect_driver_rank_drift

    # Stable distribution: same values
    stable_a = [100.0, 102.0, 98.0, 101.0, 99.0]
    stable_b = [100.0, 101.0, 99.0, 102.0, 98.0]
    stable_report = detect_data_drift(stable_a, stable_b, metric="test_kpi")
    assert stable_report.alert_level == "stable"
    assert stable_report.score < 0.10

    # Significant shift: completely different distributions
    shifted_a = [10.0, 12.0, 11.0, 10.5, 11.5]
    shifted_b = [200.0, 210.0, 195.0, 205.0, 198.0]
    shifted_report = detect_data_drift(shifted_a, shifted_b, metric="test_kpi_shifted")
    assert shifted_report.alert_level == "significant"
    assert shifted_report.score > 0.25

    # Rank drift: identical rankings → no drift
    snap_a = {"driver_a": 0.9, "driver_b": 0.6, "driver_c": 0.3}
    snap_b = {"driver_a": 0.9, "driver_b": 0.6, "driver_c": 0.3}
    no_drift = detect_driver_rank_drift([snap_a, snap_b])
    assert no_drift.alert_level == "stable"
    assert no_drift.score >= 0.9

    # Rank drift: complete reversal → significant drift
    snap_reversed = {"driver_a": 0.1, "driver_b": 0.4, "driver_c": 0.9}
    rank_drift = detect_driver_rank_drift([snap_a, snap_reversed])
    assert rank_drift.alert_level in ("slight", "significant")

    print(f"PSI stable={stable_report.score:.3f}, shifted={shifted_report.score:.3f}")
    print(f"Rank drift: no_drift rho={no_drift.score}, reversed rho={rank_drift.score}")


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Causal DiD estimator returns a bounded estimate with limitations
# ─────────────────────────────────────────────────────────────────────────────

def test_causal_did_estimate_within_bounds():
    from vantage.causal import estimate_promo_ate
    from vantage.reconciliation import load_sources

    src = load_sources()
    orders = src["orders"]
    estimate = estimate_promo_ate(orders)

    # Must identify the correct treatment and outcome
    assert "promo" in estimate.treatment.lower() or "family_a" in estimate.treatment.lower()
    assert "net_revenue" in estimate.outcome.lower()
    assert estimate.method == "difference_in_differences"

    # ATE must be numeric and CI must bracket the estimate
    assert isinstance(estimate.ate_estimate, float)
    assert estimate.ate_ci_lower <= estimate.ate_estimate <= estimate.ate_ci_upper, \
        f"ATE {estimate.ate_estimate} must be within CI [{estimate.ate_ci_lower}, {estimate.ate_ci_upper}]"

    # Must have at least 1 treated and 1 control SKU
    assert estimate.n_treated >= 1
    assert estimate.n_control >= 1

    # Must honestly state limitations
    assert len(estimate.limitations) >= 2, "CausalEstimate must carry at least 2 limitations"
    assert any("associative" in lim.lower() or "causal" in lim.lower() for lim in estimate.limitations), \
        "At least one limitation must acknowledge this is not a full causal proof"

    print(f"DiD ATE={estimate.ate_estimate:.2f} [{estimate.ate_ci_lower:.2f}, {estimate.ate_ci_upper:.2f}], "
          f"n_treated={estimate.n_treated}, n_control={estimate.n_control}")
    print(f"Key limitation: {estimate.limitations[0]}")
