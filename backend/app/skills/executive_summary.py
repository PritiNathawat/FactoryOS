"""
ExecutiveSummarySkill
----------------------
Generates a structured executive summary from all agent responses.

Used by: Reporting Agent (and Manager Agent for quick summaries)

This skill formats the collected agent outputs into a coherent
text summary that a Plant Manager can read in under 60 seconds.
It is deterministic — the same inputs always produce the same structure.
The Reporting Agent's LLM call then enriches this with narrative polish.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.skills.base import BaseSkill


class ExecutiveSummarySkill(BaseSkill):

    @property
    def name(self) -> str:
        return "executive_summary"

    @property
    def description(self) -> str:
        return (
            "Structures all agent responses into an executive summary template "
            "for the Reporting Agent to narrate."
        )

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """
        Build executive summary structure.

        Args:
            incident_id: str
            title: str
            category: str
            severity: str
            risk_level: str
            risk_score: float
            agent_responses: dict[str, AgentResponse.model_dump()]
            plans: list[RecoveryPlan.model_dump()]
            requires_human_approval: bool
        """
        incident_id = kwargs.get("incident_id", "UNKNOWN")
        title = kwargs.get("title", "Unspecified Incident")
        category = kwargs.get("category", "unknown")
        severity = kwargs.get("severity", "medium")
        risk_level = kwargs.get("risk_level", "MEDIUM")
        risk_score = float(kwargs.get("risk_score", 0.5))
        agent_responses: dict[str, Any] = kwargs.get("agent_responses", {})
        plans: list[dict] = kwargs.get("plans", [])
        requires_approval = kwargs.get("requires_human_approval", True)

        # Extract key recommendations from each agent
        agent_highlights = []
        for agent_name, response in agent_responses.items():
            rec = response.get("recommendation", "No recommendation provided")
            conf = response.get("confidence", 0.0)
            agent_highlights.append(
                f"• {agent_name.upper()} Agent (confidence {conf:.0%}): {rec}"
            )

        # Summarize plans
        plan_summaries = []
        for plan in plans:
            plan_summaries.append(
                f"  Plan {plan.get('plan_id', '?')} — {plan.get('label', '')}: "
                f"${plan.get('estimated_cost_usd', 0):,.0f} cost, "
                f"{plan.get('estimated_downtime_hours', 0):.1f}h downtime"
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        summary_template = {
            "generated_at": timestamp,
            "incident_id": incident_id,
            "incident_title": title,
            "classification": f"{category.replace('_', ' ').title()} — {severity.upper()}",
            "risk_assessment": f"{risk_level} (score: {risk_score:.2f}/1.00)",
            "requires_approval": requires_approval,
            "agent_findings": agent_highlights,
            "recovery_plans": plan_summaries,
            "total_plans": len(plans),
            "formatted_summary": (
                f"INCIDENT REPORT — {incident_id}\n"
                f"{'=' * 50}\n"
                f"Title:    {title}\n"
                f"Class:    {category.replace('_', ' ').title()} | {severity.upper()}\n"
                f"Risk:     {risk_level} ({risk_score:.2f}/1.00)\n"
                f"Generated: {timestamp}\n\n"
                f"AGENT FINDINGS:\n"
                + "\n".join(agent_highlights) + "\n\n"
                f"RECOVERY OPTIONS ({len(plans)} plans generated):\n"
                + "\n".join(plan_summaries) + "\n\n"
                f"{'⚠ HUMAN APPROVAL REQUIRED' if requires_approval else '✓ Within auto-approval threshold'}"
            ),
        }

        return summary_template
