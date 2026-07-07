"""
RiskAssessmentSkill
--------------------
Computes a composite risk score for an incident based on multiple factors.

Used by: Manager Agent (after classification, before agent routing)
Output: risk_score (0.0-1.0), risk_level, contributing_factors

Risk dimensions:
  1. Severity weight (40%) — how severe is the incident category?
  2. Machine health (25%) — what's the health score of the affected machine?
  3. Production impact (20%) — how much production is at risk?
  4. Historical recurrence (15%) — is this a recurring issue?

A high risk score (>0.75) triggers requires_human_approval=True in the result.
"""

from __future__ import annotations

from typing import Any

from app.skills.base import BaseSkill


# Risk weights (must sum to 1.0)
_WEIGHTS = {
    "severity": 0.40,
    "machine_health": 0.25,
    "production_impact": 0.20,
    "historical_recurrence": 0.15,
}

# Severity → base risk score
_SEVERITY_SCORES = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.50,
    "low": 0.25,
}

# Risk level thresholds
_RISK_LEVELS = {
    (0.80, 1.01): "CRITICAL",
    (0.60, 0.80): "HIGH",
    (0.40, 0.60): "MEDIUM",
    (0.00, 0.40): "LOW",
}


class RiskAssessmentSkill(BaseSkill):

    @property
    def name(self) -> str:
        return "risk_assessment"

    @property
    def description(self) -> str:
        return (
            "Computes a composite risk score (0.0-1.0) from severity, machine health, "
            "production impact, and historical recurrence. Returns risk level and factors."
        )

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """
        Compute risk score.

        Args:
            severity: Incident severity string ("low", "medium", "high", "critical")
            machine_health_score: 0.0-1.0 from MachineHistoryTool (default 0.5)
            revenue_at_risk_usd: From ProductionScheduleTool (default 0)
            historical_incident_count: From IncidentHistoryTool (default 0)
        """
        severity = kwargs.get("severity", "medium")
        machine_health = float(kwargs.get("machine_health_score", 0.5))
        revenue_at_risk = float(kwargs.get("revenue_at_risk_usd", 0))
        historical_count = int(kwargs.get("historical_incident_count", 0))

        # 1. Severity component
        severity_score = _SEVERITY_SCORES.get(severity, 0.5)

        # 2. Machine health component (inverted: 0 health = max risk)
        health_score = 1.0 - machine_health

        # 3. Production impact (normalized: $500k = max risk)
        production_score = min(revenue_at_risk / 500_000, 1.0)

        # 4. Historical recurrence (3+ incidents = max risk)
        recurrence_score = min(historical_count / 3.0, 1.0)

        # Weighted composite
        composite = (
            severity_score * _WEIGHTS["severity"]
            + health_score * _WEIGHTS["machine_health"]
            + production_score * _WEIGHTS["production_impact"]
            + recurrence_score * _WEIGHTS["historical_recurrence"]
        )
        composite = round(min(max(composite, 0.0), 1.0), 3)

        # Determine risk level
        risk_level = "UNKNOWN"
        for (low, high), level in _RISK_LEVELS.items():
            if low <= composite < high:
                risk_level = level
                break

        # Identify primary contributing factors
        factors = []
        if severity_score >= 0.75:
            factors.append(f"High severity incident ({severity})")
        if health_score >= 0.50:
            factors.append(f"Machine health degraded ({machine_health:.0%})")
        if production_score >= 0.40:
            factors.append(f"Significant production revenue at risk (${revenue_at_risk:,.0f})")
        if recurrence_score >= 0.33:
            factors.append(f"Recurring issue — {historical_count} similar incidents on record")
        if not factors:
            factors.append("No major individual risk factors — composite score from all dimensions")

        return {
            "risk_score": composite,
            "risk_level": risk_level,
            "requires_human_approval": composite >= 0.65,
            "contributing_factors": factors,
            "score_breakdown": {
                "severity": round(severity_score * _WEIGHTS["severity"], 3),
                "machine_health": round(health_score * _WEIGHTS["machine_health"], 3),
                "production_impact": round(production_score * _WEIGHTS["production_impact"], 3),
                "historical_recurrence": round(recurrence_score * _WEIGHTS["historical_recurrence"], 3),
            },
        }
