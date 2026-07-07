"""
DowntimeEstimationSkill
------------------------
Estimates equipment downtime based on failure type and historical data.

Used by: Maintenance Agent, Production Agent
Output: estimated hours for different repair approaches

This skill uses historical resolution time data to produce
statistically-grounded estimates rather than guesses.
"""

from __future__ import annotations

from typing import Any

from app.skills.base import BaseSkill


# Baseline repair times by failure type (hours)
# Based on industry standard MTTR data for manufacturing environments
_BASELINE_TIMES: dict[str, dict[str, float]] = {
    "bearing_failure": {
        "minimum": 4.0,   # Best case: part in stock, experienced tech
        "expected": 7.0,  # Typical case
        "maximum": 12.0,  # Worst case: complications, part delayed
    },
    "servo_fault": {
        "minimum": 8.0,
        "expected": 14.0,
        "maximum": 72.0,  # If servo drive needs procurement
    },
    "coolant_leak": {
        "minimum": 2.0,
        "expected": 4.0,
        "maximum": 8.0,
    },
    "tool_changer_jam": {
        "minimum": 1.0,
        "expected": 2.5,
        "maximum": 6.0,
    },
    "electrical_fault": {
        "minimum": 3.0,
        "expected": 8.0,
        "maximum": 48.0,
    },
    "mechanical_damage": {
        "minimum": 6.0,
        "expected": 16.0,
        "maximum": 72.0,
    },
    "unknown": {
        "minimum": 4.0,
        "expected": 12.0,
        "maximum": 48.0,
    },
}

# Adjustment multipliers
_PART_AVAILABILITY_MULTIPLIER = {
    "in_stock": 1.0,
    "low_stock": 1.1,
    "out_of_stock": 3.5,  # Includes procurement lead time
    "emergency_order": 1.8,
}

_TECH_EXPERIENCE_MULTIPLIER = {
    "expert": 0.8,
    "experienced": 1.0,
    "standard": 1.2,
}


class DowntimeEstimationSkill(BaseSkill):

    @property
    def name(self) -> str:
        return "downtime_estimation"

    @property
    def description(self) -> str:
        return (
            "Estimates equipment downtime in hours for a given failure type. "
            "Adjusts estimate based on parts availability and technician experience."
        )

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """
        Estimate downtime.

        Args:
            failure_type: Type of failure (matches _BASELINE_TIMES keys)
            parts_status: "in_stock", "low_stock", "out_of_stock", "emergency_order"
            tech_experience: "expert", "experienced", "standard"
            historical_avg_hours: From IncidentHistoryTool (optional override)
        """
        failure_type = kwargs.get("failure_type", "unknown").lower().replace(" ", "_")
        parts_status = kwargs.get("parts_status", "in_stock")
        tech_experience = kwargs.get("tech_experience", "experienced")
        historical_avg = kwargs.get("historical_avg_hours")

        baseline = _BASELINE_TIMES.get(failure_type, _BASELINE_TIMES["unknown"])
        parts_mult = _PART_AVAILABILITY_MULTIPLIER.get(parts_status, 1.0)
        tech_mult = _TECH_EXPERIENCE_MULTIPLIER.get(tech_experience, 1.0)

        adjusted_min = round(baseline["minimum"] * parts_mult * tech_mult, 1)
        adjusted_expected = round(baseline["expected"] * parts_mult * tech_mult, 1)
        adjusted_max = round(baseline["maximum"] * parts_mult * tech_mult, 1)

        # Blend with historical data if available (weighted 60% baseline, 40% historical)
        if historical_avg is not None:
            blended = round(adjusted_expected * 0.6 + float(historical_avg) * 0.4, 1)
        else:
            blended = adjusted_expected

        return {
            "failure_type": failure_type,
            "estimated_hours_minimum": adjusted_min,
            "estimated_hours_expected": blended,
            "estimated_hours_maximum": adjusted_max,
            "confidence_interval": f"{adjusted_min}h – {adjusted_max}h",
            "primary_estimate_hours": blended,
            "assumptions": [
                f"Parts availability: {parts_status}",
                f"Technician experience: {tech_experience}",
                f"Historical data {'included' if historical_avg else 'not available'}",
            ],
            "adjustment_factors": {
                "parts_availability": parts_mult,
                "technician_experience": tech_mult,
            },
        }
