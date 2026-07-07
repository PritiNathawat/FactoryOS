"""
Reporting Agent
================
Synthesizes all domain agent outputs into an executive-grade report.
The final agent in the pipeline — runs after all domain agents and plan synthesis.

Tools used: None (reporting is synthesis, not data gathering)

Skills used:
  - executive_summary: Structures agent responses before LLM narration

Gemini call: 1 (with all agent responses + plans as context)
"""

from __future__ import annotations

import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.reporting.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas.agent import AgentContext, AgentResponse
from app.skills.executive_summary import ExecutiveSummarySkill


class ReportingAgent(BaseAgent):
    name = "reporting"
    description = (
        "Synthesizes all domain agent outputs into an executive-grade summary. "
        "Produces a clear, actionable report for the Plant Manager to make a decision."
    )

    def __init__(self, tool_registry, gemini_client) -> None:
        super().__init__(tool_registry, gemini_client)
        self._summary_skill = ExecutiveSummarySkill()

    async def execute(
        self,
        context: AgentContext,
        plans: list[dict[str, Any]] | None = None,
    ) -> AgentResponse:
        """
        Execute the reporting agent.

        Unlike domain agents, the Reporting Agent receives the full set of
        agent_results from context.agent_results (populated by the Manager Agent).
        It also optionally receives the finalized plans list.
        """
        start = time.monotonic()
        agent_responses: dict[str, Any] = context.agent_results
        plans = plans or []

        try:
            # ── Skill: Structure the summary ───────────────────
            summary_structure = self._summary_skill.run(
                incident_id=context.incident_id,
                title=context.title,
                category=context.category,
                severity=context.severity,
                risk_level="HIGH" if context.risk_score >= 0.65 else "MEDIUM",
                risk_score=context.risk_score,
                agent_responses=agent_responses,
                plans=plans,
                requires_human_approval=context.requires_immediate_action,
            )

            # ── Gemini call ────────────────────────────────────
            user_prompt = build_user_prompt(
                context=context,
                agent_responses=agent_responses,
                plans=plans,
                summary_structure=summary_structure,
            )
            raw = await self.gemini.generate_json(
                user_prompt=user_prompt,
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,  # Slightly higher for more natural executive prose
            )

            elapsed = int((time.monotonic() - start) * 1000)
            self._logger.info(
                "Executive report generated",
                extra={"incident_id": context.incident_id, "elapsed_ms": elapsed},
            )

            return self._parse_response(raw=raw, tools_used=[], elapsed_ms=elapsed)

        except Exception as exc:
            self._logger.error("ReportingAgent.execute failed", exc_info=exc)
            return self._error_response(str(exc))
