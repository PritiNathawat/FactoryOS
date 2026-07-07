"""
Manager Agent (Orchestrator)
==============================
The central coordinator of the FactoryOS AI Platform.

Orchestration Flow:
  1. Pre-fetch shared tools (machine_history, incident_history)
  2. Run IncidentClassificationSkill — deterministic category/severity
  3. Run RiskAssessmentSkill — composite risk score
  4. Build AgentContext with all pre-fetched data
  5. Run 4 domain agents in PARALLEL using asyncio.gather()
  6. Synthesize 3 recovery plans via a dedicated Gemini call
  7. Run Reporting Agent with all data
  8. Build and return OrchestratorResult

Why parallel execution (asyncio.gather)?
  Domain agents are independent — Maintenance doesn't need Inventory's output
  and vice versa. Running them sequentially would be unnecessarily slow.
  asyncio.gather() runs all 4 concurrent Gemini calls simultaneously.

Why a separate synthesis step?
  No single domain agent has the full picture. The plan synthesis step
  is a dedicated LLM reasoning step with ALL agent data available — this
  produces better plans than any individual agent could generate alone.

ADK Migration Path:
  This entire class maps to google-adk's SequentialAgent + ParallelAgent pattern:
  - Sequential: Pre-fetch → Classify → Assess → [Parallel agents] → Synthesize → Report
  - Parallel: The 4 domain agents in step 5
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from app.agents.cost.cost_agent import CostIntelligenceAgent
from app.agents.inventory.inventory_agent import InventoryAgent
from app.agents.maintenance.maintenance_agent import MaintenanceAgent
from app.agents.orchestrator.prompts import (
    PLAN_SYNTHESIS_SYSTEM_PROMPT,
    build_plan_synthesis_prompt,
)
from app.agents.production.production_agent import ProductionAgent
from app.agents.reporting.reporting_agent import ReportingAgent
from app.core.gemini import GeminiClient
from app.mcp.registry import MCPToolRegistry
from app.schemas.agent import AgentContext, AgentResponse, AgentStatus
from app.schemas.incident import IncidentInput, IncidentSeverity
from app.schemas.recovery import OrchestratorResult, RecoveryPlan, RecoveryStep, PlanType
from app.skills.incident_classification import IncidentClassificationSkill
from app.skills.risk_assessment import RiskAssessmentSkill

logger = logging.getLogger(__name__)


class ManagerAgent:
    """
    Orchestrates the full FactoryOS AI analysis pipeline.

    Not a subclass of BaseAgent — the Manager has a different interface
    (run_analysis vs execute) because it takes an IncidentInput and
    returns an OrchestratorResult, not an AgentResponse.
    """

    name = "manager"
    description = (
        "Orchestrates the complete incident analysis pipeline. "
        "Coordinates domain agents and synthesizes recovery plans."
    )
    version = "0.1.0"

    def __init__(
        self,
        tool_registry: MCPToolRegistry,
        gemini_client: GeminiClient,
        maintenance_agent: MaintenanceAgent,
        inventory_agent: InventoryAgent,
        production_agent: ProductionAgent,
        cost_agent: CostIntelligenceAgent,
        reporting_agent: ReportingAgent,
    ) -> None:
        self.tools = tool_registry
        self.gemini = gemini_client
        self._maintenance = maintenance_agent
        self._inventory = inventory_agent
        self._production = production_agent
        self._cost = cost_agent
        self._reporting = reporting_agent

        # Skills (deterministic, no LLM)
        self._classification_skill = IncidentClassificationSkill()
        self._risk_skill = RiskAssessmentSkill()

    async def run_analysis(self, incident: IncidentInput) -> OrchestratorResult:
        """
        Run the complete FactoryOS analysis pipeline for an incident.

        This is the single entry point called by AIPlatformService.
        Returns a fully structured OrchestratorResult with 3 recovery plans.
        """
        pipeline_start = time.monotonic()
        logger.info("Starting incident analysis", extra={"incident_id": incident.incident_id})

        try:
            # ── Step 1: Pre-fetch shared tool data ────────────
            logger.debug("Step 1: Pre-fetching shared tool data")
            machine_data, incident_history_data = await asyncio.gather(
                self._fetch_tool("machine_history", {"equipment_id": incident.equipment_id or "UNKNOWN"}),
                self._fetch_tool("incident_history", {"equipment_id": incident.equipment_id, "limit": 5}),
                return_exceptions=True,
            )
            machine_data = machine_data if isinstance(machine_data, dict) else {}
            incident_history_data = incident_history_data if isinstance(incident_history_data, dict) else {}

            # ── Step 2: Incident Classification (deterministic) ──
            logger.debug("Step 2: Running IncidentClassificationSkill")
            classification = self._classification_skill.run(
                title=incident.title,
                description=incident.description,
                reported_severity=incident.severity.value,
            )

            # ── Step 3: Risk Assessment (deterministic) ────────
            logger.debug("Step 3: Running RiskAssessmentSkill")
            risk = self._risk_skill.run(
                severity=classification["severity"],
                machine_health_score=machine_data.get("current_health_score", 0.5),
                revenue_at_risk_usd=0,  # Will be filled by Production Agent
                historical_incident_count=incident_history_data.get("total_matching_incidents", 0),
            )

            # ── Step 4: Build shared AgentContext ─────────────
            logger.debug("Step 4: Building AgentContext")
            context = AgentContext(
                incident_id=incident.incident_id,
                title=incident.title,
                description=incident.description,
                equipment_id=incident.equipment_id,
                location=incident.location,
                severity=classification["severity"],
                category=classification["category"],
                risk_score=risk["risk_score"],
                requires_immediate_action=risk["requires_human_approval"],
                tool_results={
                    "machine_history": machine_data,
                    "incident_history": incident_history_data,
                },
            )

            # ── Step 5: Run domain agents in PARALLEL ─────────
            logger.info(
                "Step 5: Running 4 domain agents in parallel",
                extra={"incident_id": incident.incident_id},
            )
            maintenance_resp, inventory_resp, production_resp, cost_resp = await asyncio.gather(
                self._maintenance.execute(context),
                self._inventory.execute(context),
                self._production.execute(context),
                self._cost.execute(context),
                return_exceptions=True,
            )

            # Normalize: convert exceptions to error responses
            maintenance_resp = self._normalize_response(maintenance_resp, "maintenance")
            inventory_resp = self._normalize_response(inventory_resp, "inventory")
            production_resp = self._normalize_response(production_resp, "production")
            cost_resp = self._normalize_response(cost_resp, "cost")

            agent_responses_dict = {
                "maintenance": maintenance_resp.model_dump(),
                "inventory": inventory_resp.model_dump(),
                "production": production_resp.model_dump(),
                "cost": cost_resp.model_dump(),
            }

            # ── Step 6: Synthesize 3 Recovery Plans ───────────
            logger.info("Step 6: Synthesizing recovery plans via Gemini")
            plans = await self._synthesize_plans(
                incident=incident,
                context=context,
                maintenance_response=agent_responses_dict["maintenance"],
                inventory_response=agent_responses_dict["inventory"],
                production_response=agent_responses_dict["production"],
                cost_response=agent_responses_dict["cost"],
            )

            # ── Step 7: Run Reporting Agent ────────────────────
            logger.info("Step 7: Running Reporting Agent")
            reporting_context = context.model_copy(
                update={"agent_results": agent_responses_dict}
            )
            plans_as_dicts = [p.model_dump() for p in plans]
            reporting_resp = await self._reporting.execute(
                context=reporting_context,
                plans=plans_as_dicts,
            )
            executive_summary = (
                reporting_resp.data.get("executive_summary", "")
                or reporting_resp.recommendation
            )

            # ── Step 8: Compute overall confidence ────────────
            confidence_scores = [
                resp.confidence
                for resp in [maintenance_resp, inventory_resp, production_resp, cost_resp]
                if resp.status not in [AgentStatus.ERROR, AgentStatus.SKIPPED]
            ]
            overall_confidence = (
                round(sum(confidence_scores) / len(confidence_scores), 3)
                if confidence_scores
                else 0.5
            )

            # Human approval is required when risk is high or confidence is low
            requires_approval = risk["requires_human_approval"] or overall_confidence < 0.70
            approval_reason = None
            if requires_approval:
                reasons = []
                if risk["requires_human_approval"]:
                    reasons.append(f"Risk score {risk['risk_score']:.2f} exceeds threshold")
                if overall_confidence < 0.70:
                    reasons.append(f"Overall agent confidence {overall_confidence:.0%} below 70% threshold")
                approval_reason = ". ".join(reasons)

            elapsed_total = int((time.monotonic() - pipeline_start) * 1000)
            logger.info(
                "Incident analysis complete",
                extra={
                    "incident_id": incident.incident_id,
                    "elapsed_ms": elapsed_total,
                    "confidence": overall_confidence,
                    "plans_generated": len(plans),
                    "requires_approval": requires_approval,
                },
            )

            return OrchestratorResult(
                incident_id=incident.incident_id,
                status="completed",
                agents_consulted=["maintenance", "inventory", "production", "cost", "reporting"],
                incident_category=classification["category"],
                incident_severity=classification["severity"],
                plans=plans,
                executive_summary=executive_summary,
                confidence_overall=overall_confidence,
                requires_human_approval=requires_approval,
                human_approval_reason=approval_reason,
                analyzed_at=datetime.now(timezone.utc).isoformat(),
                agent_responses=agent_responses_dict,
                model_used=self.gemini._model,
            )

        except Exception as exc:
            logger.error("ManagerAgent.run_analysis failed", exc_info=exc)
            raise

    async def _fetch_tool(self, tool_name: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Fetch data from a single tool. Returns empty dict on failure."""
        try:
            tool = self.tools.require(tool_name)
            result = await tool.run(input_data)
            return result.data if result.success and result.data else {}
        except Exception:
            logger.warning("Pre-fetch failed for tool: %s", tool_name)
            return {}

    def _normalize_response(
        self, response: AgentResponse | BaseException, agent_name: str
    ) -> AgentResponse:
        """Convert an exception from asyncio.gather into a typed error AgentResponse."""
        if isinstance(response, BaseException):
            logger.error("Agent %s raised exception: %s", agent_name, response)
            return AgentResponse(
                agent_name=agent_name,
                status=AgentStatus.ERROR,
                confidence=0.0,
                reasoning=f"Agent failed with exception: {response}",
                recommendation="Manual investigation required.",
                error_message=str(response),
            )
        return response

    async def _synthesize_plans(
        self,
        incident: IncidentInput,
        context: AgentContext,
        maintenance_response: dict[str, Any],
        inventory_response: dict[str, Any],
        production_response: dict[str, Any],
        cost_response: dict[str, Any],
    ) -> list[RecoveryPlan]:
        """
        Make the plan synthesis Gemini call.

        This is Gemini call #5 — it synthesizes all 4 agent outputs into
        3 distinct recovery plans (Economical, Rapid, Balanced).
        """
        user_prompt = build_plan_synthesis_prompt(
            incident=incident,
            context=context,
            maintenance_response=maintenance_response,
            inventory_response=inventory_response,
            production_response=production_response,
            cost_response=cost_response,
        )

        try:
            raw = await self.gemini.generate_json(
                user_prompt=user_prompt,
                system_instruction=PLAN_SYNTHESIS_SYSTEM_PROMPT,
                temperature=0.4,
            )

            plans_raw = raw.get("plans", [])
            plans = []
            for p in plans_raw[:3]:  # Ensure max 3 plans
                try:
                    plan_type_str = p.get("plan_type", "balanced")
                    try:
                        plan_type = PlanType(plan_type_str)
                    except ValueError:
                        plan_type = PlanType.BALANCED

                    steps = [
                        RecoveryStep(
                            step_number=s.get("step_number", i + 1),
                            action=s.get("action", ""),
                            responsible_party=s.get("responsible_party", "Maintenance Team"),
                            estimated_duration_hours=float(s.get("estimated_duration_hours", 1)),
                            resources_required=s.get("resources_required", []),
                            dependencies=s.get("dependencies", []),
                        )
                        for i, s in enumerate(p.get("steps", []))
                    ]

                    plans.append(
                        RecoveryPlan(
                            plan_id=p.get("plan_id", "A"),
                            plan_type=plan_type,
                            label=p.get("label", "Recovery Plan"),
                            description=p.get("description", ""),
                            estimated_cost_usd=float(p.get("estimated_cost_usd", 0)),
                            estimated_downtime_hours=float(p.get("estimated_downtime_hours", 0)),
                            production_impact_units=p.get("production_impact_units"),
                            confidence=float(p.get("confidence", 0.7)),
                            reasoning=p.get("reasoning", ""),
                            steps=steps,
                            risks=p.get("risks", []),
                            prerequisites=p.get("prerequisites", []),
                        )
                    )
                except Exception as parse_err:
                    logger.warning("Failed to parse plan: %s", parse_err)

            if not plans:
                plans = self._generate_fallback_plans(context)

            return plans

        except Exception as exc:
            logger.error("Plan synthesis failed, using fallbacks: %s", exc)
            return self._generate_fallback_plans(context)

    def _generate_fallback_plans(self, context: AgentContext) -> list[RecoveryPlan]:
        """
        Generate minimal fallback plans when Gemini synthesis fails.
        These ensure the API always returns 3 plans, even in degraded mode.
        """
        base_step = RecoveryStep(
            step_number=1,
            action="Dispatch maintenance technician for immediate inspection",
            responsible_party="Maintenance Manager",
            estimated_duration_hours=1.0,
            resources_required=["Maintenance technician", "Inspection tools"],
            dependencies=[],
        )
        plans = []
        for plan_id, plan_type, label, cost, hours in [
            ("A", PlanType.ECONOMICAL, "Economical Recovery", 18000.0, 12.0),
            ("B", PlanType.RAPID, "Rapid Recovery", 45000.0, 6.0),
            ("C", PlanType.BALANCED, "Balanced Recovery", 28000.0, 9.0),
        ]:
            plans.append(
                RecoveryPlan(
                    plan_id=plan_id,
                    plan_type=plan_type,
                    label=label,
                    description=f"{label} approach for {context.equipment_id}.",
                    estimated_cost_usd=cost,
                    estimated_downtime_hours=hours,
                    confidence=0.5,
                    reasoning="Fallback plan generated due to synthesis error.",
                    steps=[base_step],
                    risks=["Plan generated in fallback mode — manual review required"],
                )
            )
        return plans
