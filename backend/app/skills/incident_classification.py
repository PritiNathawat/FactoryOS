"""
IncidentClassificationSkill
-----------------------------
Classifies an incident into a category and severity level based on
keyword analysis and rule-based logic.

Used by: Manager Agent (first step of orchestration)
Output: IncidentClassification (category, severity, affected systems)

Why deterministic (not LLM)?
  Classification needs to be FAST and CONSISTENT. The same incident
  description should always produce the same category. Using rules here
  also means the system works without an API key for routing logic.
  The LLM handles uncertainty and nuance in the downstream domain agents.
"""

from __future__ import annotations

import re
from typing import Any

from app.schemas.incident import IncidentCategory, IncidentClassification, IncidentSeverity
from app.skills.base import BaseSkill


# ─── Classification Rules ─────────────────────────────────────

# Keywords mapped to categories (ordered by specificity)
_CATEGORY_RULES: list[tuple[IncidentCategory, list[str]]] = [
    (IncidentCategory.SAFETY_EVENT, [
        "injury", "accident", "fire", "explosion", "gas leak", "chemical spill",
        "lockout", "tagout", "loto", "emergency", "evacuation", "unsafe",
    ]),
    (IncidentCategory.EQUIPMENT_FAILURE, [
        "failure", "failed", "broken", "seized", "fault", "malfunction",
        "damaged", "cracked", "worn", "bearing", "motor", "drive", "servo",
        "spindle", "hydraulic", "pneumatic", "overload", "trip", "shutdown",
        "noise", "vibration", "leak", "coolant",
    ]),
    (IncidentCategory.QUALITY_ISSUE, [
        "quality", "defect", "scrap", "rework", "tolerance", "dimensional",
        "surface finish", "out of spec", "non-conforming", "reject",
    ]),
    (IncidentCategory.SUPPLY_CHAIN, [
        "supplier", "supply", "delivery", "shipment", "procurement", "shortage",
        "out of stock", "lead time", "vendor", "material",
    ]),
    (IncidentCategory.SCHEDULED_MAINTENANCE, [
        "scheduled", "preventive", "planned", "pm", "lubrication", "inspection",
        "calibration", "overhaul",
    ]),
    (IncidentCategory.UNPLANNED_DOWNTIME, [
        "down", "stopped", "halt", "shutdown", "not running", "not producing",
        "idle", "unplanned",
    ]),
]

# Severity escalation keywords
_SEVERITY_ESCALATORS: dict[IncidentSeverity, list[str]] = {
    IncidentSeverity.CRITICAL: [
        "critical", "severe", "catastrophic", "complete failure", "production stopped",
        "safety risk", "injury", "fire", "explosion", "all lines down",
    ],
    IncidentSeverity.HIGH: [
        "high", "urgent", "major", "significant", "multiple", "all orders",
        "customer escalation", "line down", "cannot produce",
    ],
    IncidentSeverity.MEDIUM: [
        "medium", "moderate", "partial", "reduced", "intermittent", "degraded",
    ],
    IncidentSeverity.LOW: [
        "low", "minor", "small", "slight", "occasional", "intermittent",
    ],
}

# Systems keywords
_SYSTEM_KEYWORDS: dict[str, list[str]] = {
    "spindle": ["spindle", "bearing", "rotation"],
    "coolant": ["coolant", "cooling", "fluid", "leak"],
    "servo": ["servo", "drive", "axis", "motion"],
    "hydraulics": ["hydraulic", "pressure", "fluid"],
    "electrical": ["electrical", "power", "voltage", "current", "control"],
    "mechanical": ["mechanical", "gear", "belt", "chain", "coupling"],
    "software": ["software", "plc", "controller", "program", "cnc"],
}


class IncidentClassificationSkill(BaseSkill):

    @property
    def name(self) -> str:
        return "incident_classification"

    @property
    def description(self) -> str:
        return (
            "Classifies an incident into category and severity using keyword-based rules. "
            "Identifies affected systems and flags immediate action requirements."
        )

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """
        Classify an incident.

        Args:
            title: Incident title
            description: Full incident description
            reported_severity: Operator-reported severity (IncidentSeverity)

        Returns:
            dict matching IncidentClassification schema
        """
        title: str = kwargs.get("title", "")
        description: str = kwargs.get("description", "")
        reported_severity: str = kwargs.get("reported_severity", IncidentSeverity.MEDIUM.value)

        text = f"{title} {description}".lower()

        # ── Category classification ────────────────────────
        category = IncidentCategory.UNKNOWN
        confidence = 0.5
        for cat, keywords in _CATEGORY_RULES:
            if any(kw in text for kw in keywords):
                category = cat
                # Count keyword matches for confidence
                matches = sum(1 for kw in keywords if kw in text)
                confidence = min(0.5 + (matches * 0.1), 0.95)
                break

        # ── Severity determination ─────────────────────────
        # Start with operator-reported severity, escalate if keywords suggest worse
        severity = IncidentSeverity(reported_severity)
        for level in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH, IncidentSeverity.MEDIUM]:
            if any(kw in text for kw in _SEVERITY_ESCALATORS[level]):
                # Only escalate, never de-escalate reported severity
                if list(IncidentSeverity).index(level) <= list(IncidentSeverity).index(severity):
                    severity = level
                break

        # ── Affected systems ───────────────────────────────
        affected = [
            system for system, keywords in _SYSTEM_KEYWORDS.items()
            if any(kw in text for kw in keywords)
        ]

        # ── Immediate action flag ──────────────────────────
        requires_immediate = (
            severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]
            or any(kw in text for kw in _SEVERITY_ESCALATORS[IncidentSeverity.CRITICAL])
        )

        result = IncidentClassification(
            category=category,
            severity=severity,
            confidence=confidence,
            affected_systems=affected,
            requires_immediate_action=requires_immediate,
            classification_reasoning=(
                f"Category '{category.value}' identified from keyword analysis. "
                f"Severity set to '{severity.value}' based on "
                f"{'escalated keyword match' if severity != IncidentSeverity(reported_severity) else 'operator report'}. "
                f"Affected systems: {', '.join(affected) or 'unspecified'}."
            ),
        )
        return result.model_dump()
