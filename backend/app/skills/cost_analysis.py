"""
CostAnalysisSkill
------------------
Synthesizes cost data from multiple sources into a comparative analysis.

Used by: Cost Intelligence Agent
Output: Total cost estimates for each plan type with business impact scoring

This skill does NOT make LLM calls — it performs structured financial
computation. The Cost Agent then uses this output to generate its
AI-powered cost recommendation.
"""

from __future__ import annotations

from typing import Any

from app.skills.base import BaseSkill


class CostAnalysisSkill(BaseSkill):

    @property
    def name(self) -> str:
        return "cost_analysis"

    @property
    def description(self) -> str:
        return (
            "Synthesizes cost data from tool results into a comparative financial analysis "
            "of multiple repair approaches. Returns ROI and business impact metrics."
        )

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """
        Compute comparative cost analysis.

        Args:
            plans: list of dicts with keys:
                - plan_name: str
                - repair_type: str
                - labor_cost_usd: float
                - parts_cost_usd: float
                - downtime_hours: float
                - downtime_cost_per_hour_usd: float
                - expediting_premium_usd: float
            revenue_at_risk_usd: float (from ProductionScheduleTool)
            cost_of_deferring_usd: float (from CostEstimatorTool)
        """
        plans: list[dict] = kwargs.get("plans", [])
        revenue_at_risk = float(kwargs.get("revenue_at_risk_usd", 0))
        cost_of_deferring = float(kwargs.get("cost_of_deferring_usd", 0))

        analyzed_plans = []
        for plan in plans:
            labor = float(plan.get("labor_cost_usd", 0))
            parts = float(plan.get("parts_cost_usd", 0))
            downtime_hours = float(plan.get("downtime_hours", 0))
            downtime_rate = float(plan.get("downtime_cost_per_hour_usd", 4200))
            expediting = float(plan.get("expediting_premium_usd", 0))

            direct_cost = labor + parts + expediting
            downtime_cost = downtime_hours * downtime_rate
            total_cost = direct_cost + downtime_cost

            # ROI: how much more does deferring cost vs. acting now?
            roi_of_action = round(cost_of_deferring / total_cost, 2) if total_cost > 0 else 0.0

            # Business impact score: 0 (best) to 1 (worst)
            max_expected_cost = max(p.get("total_estimate", 100000) for p in plans) or 100000
            impact_score = round(min(total_cost / max_expected_cost, 1.0), 3)

            analyzed_plans.append({
                "plan_name": plan.get("plan_name", "Unknown"),
                "repair_type": plan.get("repair_type", ""),
                "direct_cost_usd": round(direct_cost, 2),
                "downtime_cost_usd": round(downtime_cost, 2),
                "total_cost_usd": round(total_cost, 2),
                "downtime_hours": downtime_hours,
                "roi_vs_deferral": roi_of_action,
                "business_impact_score": impact_score,
                "cost_breakdown": {
                    "labor": labor,
                    "parts": parts,
                    "downtime_loss": downtime_cost,
                    "expediting": expediting,
                },
            })

        # Sort by total cost (cheapest first)
        analyzed_plans.sort(key=lambda p: p["total_cost_usd"])

        # Identify recommended plan (best ROI vs deferring)
        recommended = max(analyzed_plans, key=lambda p: p["roi_vs_deferral"]) if analyzed_plans else None

        return {
            "plans": analyzed_plans,
            "revenue_at_risk_usd": revenue_at_risk,
            "cost_of_deferring_usd": cost_of_deferring,
            "recommended_plan": recommended["plan_name"] if recommended else None,
            "total_financial_exposure_usd": revenue_at_risk + (analyzed_plans[-1]["total_cost_usd"] if analyzed_plans else 0),
            "acting_now_saves_usd": round(cost_of_deferring - (analyzed_plans[0]["total_cost_usd"] if analyzed_plans else 0), 2),
        }
