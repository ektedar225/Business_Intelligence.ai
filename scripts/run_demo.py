#!/usr/bin/env python3
"""Headless sanity check: regenerates synthetic data, runs all three scenarios end to
end, and prints the recovery scorecard + firewall verdicts + telemetry. Useful to
confirm the engine works without starting the API/browser.

    python3 scripts/run_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from vantage.datagen import build_and_persist
from vantage.pipeline import build_scenario1_bundle, build_scenario2_bundle, build_scenario3_bundle
from vantage.scorecard import recovery_scorecard
from vantage.narrative import render_narrative, verify_narrative
from vantage.registries import get_persona_registry


def main() -> None:
    print("Regenerating synthetic data with injected ground truth…")
    build_and_persist()

    print("\n=== Scenario 1 — multi-factor Net Revenue movement ===")
    bundle1, _ = build_scenario1_bundle()
    cfo = get_persona_registry().get("cfo")
    narrative = render_narrative(bundle1, cfo)
    print(narrative.full_text)
    verdict = verify_narrative(narrative, bundle1)
    print(f"\nNumeric firewall: {'PASSED' if verdict.passed else 'FAILED — ' + str(verdict.orphan_numerals)}")

    print("\n=== Recovery Scorecard ===")
    sc = recovery_scorecard(bundle1)
    print(f"Driver recall@3: {sc['driver_recall_at_3_label']}")
    print(f"Rank correlation: {sc['rank_correlation_spearman']}")
    print(f"Attribution MAE: {sc['attribution_mae_pp']}pp (target <{sc['attribution_mae_target_pp']}pp)")
    print(f"Residual error: {sc['residual_error_pp']}pp (target <{sc['residual_error_target_pp']}pp)")

    print("\n=== Scenario 2 — abstain on stale S3 feed ===")
    _, abstention, _ = build_scenario2_bundle()
    print(f"Mode: {abstention.mode}\nBlocker: {abstention.blocker}")

    print("\n=== Scenario 3 — sparse-history CAC ===")
    bundle3, _ = build_scenario3_bundle()
    print(f"Confidence band: {bundle3.confidence.band} (composite {bundle3.confidence.composite})")

    print("\nAll scenarios ran. Start the API + dashboard with:")
    print("  python3 -m uvicorn api.main:app --reload --port 8420")


if __name__ == "__main__":
    main()
