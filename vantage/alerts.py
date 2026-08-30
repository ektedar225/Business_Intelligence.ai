"""Proactive Alert Engine — evaluates materiality thresholds per persona channel and
fires structured alerts. Delivery is currently a console-log stub (prefixed
[ALERT STUB]) so the channel routing logic is real and wirable to email / Slack /
Teams without touching the evaluation layer.

Design note: personas.yaml already names channels (email, dashboard, slack_digest).
This module honours that contract — it just swaps the transport for a log line until
the integrations are wired.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional

from vantage.evidence import EvidenceBundle

logger = logging.getLogger("vantage.alerts")

@dataclass
class AlertRule:
    rule_id: str
    kpi_id: str
    trigger: Literal["surprise_z", "wow_pct", "confidence_band"]
    threshold: float
    band_values: list[str] = field(default_factory=list)
    severity: Literal["info", "warning", "critical"] = "warning"
    target_personas: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=lambda: ["dashboard"])

@dataclass
class Alert:
    rule_id: str
    kpi_id: str
    period: str
    severity: str
    headline: str
    detail: str
    triggered_value: float
    target_personas: list[str]
    channels: list[str]
    fired_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

DEFAULT_RULES: list[AlertRule] = [
    AlertRule(
        rule_id="high-surprise-z",
        kpi_id="*",
        trigger="surprise_z",
        threshold=2.0,
        severity="critical",
        target_personas=["cfo", "regional_director_emea"],
        channels=["email", "dashboard"],
    ),
    AlertRule(
        rule_id="large-wow-move",
        kpi_id="*",
        trigger="wow_pct",
        threshold=0.05,
        severity="warning",
        target_personas=[],
        channels=["dashboard"],
    ),
    AlertRule(
        rule_id="low-confidence-alert",
        kpi_id="*",
        trigger="confidence_band",
        threshold=0.0,
        band_values=["low", "abstain"],
        severity="warning",
        target_personas=["analyst"],
        channels=["slack_digest", "dashboard"],
    ),
    AlertRule(
        rule_id="net-revenue-critical-drop",
        kpi_id="net_revenue",
        trigger="wow_pct",
        threshold=0.08,
        severity="critical",
        target_personas=["cfo"],
        channels=["email", "dashboard"],
    ),
]

def evaluate_alerts(
    bundle: EvidenceBundle,
    rules: Optional[list[AlertRule]] = None,
) -> list[Alert]:
    """Check a bundle against each alert rule and return all triggered alerts."""
    rules = rules or DEFAULT_RULES
    alerts: list[Alert] = []
    m = bundle.movement
    confidence_band = bundle.confidence.band if bundle.confidence else "unknown"

    for rule in rules:
        if rule.kpi_id != "*" and rule.kpi_id != bundle.kpi_id:
            continue

        triggered = False
        triggered_value = 0.0

        if rule.trigger == "surprise_z":
            val = abs(m.surprise_z) if m.surprise_z is not None else 0.0
            if val >= rule.threshold:
                triggered, triggered_value = True, val

        elif rule.trigger == "wow_pct":
            val = abs(m.wow_delta_pct) if m.wow_delta_pct is not None else 0.0
            if val >= rule.threshold:
                triggered, triggered_value = True, val

        elif rule.trigger == "confidence_band":
            if confidence_band in rule.band_values:
                triggered, triggered_value = True, bundle.confidence.composite if bundle.confidence else 0.0

        if not triggered:
            continue

        direction = "fell" if (m.wow_delta_abs or 0) < 0 else "rose"
        headline = (
            f"[{rule.severity.upper()}] {bundle.kpi_id.replace('_', ' ').title()} "
            f"{direction} {abs(m.wow_delta_pct or 0) * 100:.1f}% WoW in {m.period}"
        )
        detail = (
            f"Rule '{rule.rule_id}' triggered: {rule.trigger}={triggered_value:.3f} "
            f"(threshold={rule.threshold}). Confidence: {confidence_band.upper()}."
        )
        alert = Alert(
            rule_id=rule.rule_id,
            kpi_id=bundle.kpi_id,
            period=m.period,
            severity=rule.severity,
            headline=headline,
            detail=detail,
            triggered_value=round(triggered_value, 4),
            target_personas=rule.target_personas,
            channels=rule.channels,
        )
        alerts.append(alert)

    return alerts

def deliver_alerts(alerts: list[Alert]) -> list[dict]:
    """Deliver each alert to its target channels. Currently a structured log stub —
    replace the per-channel block with real transport clients (SendGrid, Slack SDK,
    Teams webhook) without changing the evaluation layer above.
    """
    delivery_log: list[dict] = []
    for alert in alerts:
        for channel in alert.channels:
            if channel == "email":
                logger.info(
                    "[ALERT STUB] EMAIL → %s | %s | %s",
                    ", ".join(alert.target_personas) or "all",
                    alert.headline,
                    alert.detail,
                )
            elif channel == "slack_digest":
                logger.info(
                    "[ALERT STUB] SLACK → %s | %s",
                    alert.headline,
                    alert.detail,
                )
            else:
                logger.info(
                    "[ALERT STUB] DASHBOARD → %s",
                    alert.headline,
                )
            delivery_log.append({
                "channel": channel,
                "severity": alert.severity,
                "headline": alert.headline,
                "personas": alert.target_personas,
                "fired_at": alert.fired_at,
                "status": "stub_logged",
            })
    return delivery_log
