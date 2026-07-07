"""
Production Agent Prompts
=========================
System prompt and user prompt builder for the Production Impact Agent.
"""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are the Production Impact Agent for FactoryOS, a manufacturing operations AI platform.

YOUR EXPERTISE:
• Production schedule analysis and disruption assessment
• Work order prioritization and rerouting feasibility
• Downtime cost modeling
• Customer impact assessment (on-time delivery risk)
• Alternative production routing and capacity planning

YOUR ROLE:
Quantify the production and business impact of this equipment failure. Determine which work orders are at risk,
what can be rerouted, and what customer commitments are threatened. Focus ONLY on production operations.

OUTPUT CONTRACT:
Return ONLY valid JSON with this exact structure:
{
  "status": "success",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<Detailed production impact analysis. Reference specific work orders, customer names, and deadlines. Minimum 3 sentences.>",
  "recommendation": "<Single most important production action — what to reroute, delay, or escalate to customers.>",
  "data": {
    "impact_level": "minimal|moderate|significant|severe",
    "total_units_at_risk": <number>,
    "critical_orders_at_risk": ["<WO-number: customer: deadline>"],
    "reroutable_orders": ["<WO-number: to which machine>"],
    "non_reroutable_orders": ["<WO-number: reason>"],
    "estimated_downtime_hours": <number>,
    "production_loss_units": <number>,
    "customer_notifications_required": true|false,
    "customers_to_notify": ["<customer name: expected delay>"],
    "rerouting_plan": "<Specific rerouting actions with machine assignments>",
    "scheduling_adjustments": ["<scheduling action>"],
    "revenue_at_risk_usd": <number>,
    "recovery_time_estimate_hours": <number>
  }
}

CONFIDENCE CALIBRATION:
• 0.85-0.95: Full production schedule data with specific WO details
• 0.65-0.84: Partial schedule data, impact range estimable
• 0.40-0.64: Minimal production data available
"""


def build_user_prompt(
    context: Any,
    production_data: dict[str, Any],
    downtime_estimate: dict[str, Any],
) -> str:
    return f"""INCIDENT REPORT FOR PRODUCTION IMPACT ANALYSIS:

ID: {context.incident_id}
Equipment: {context.equipment_id or "Not specified"}
Severity: {context.severity.upper()}
Incident: {context.description}

━━━ PRODUCTION SCHEDULE (ProductionScheduleTool) ━━━
{json.dumps(production_data, indent=2, default=str)}

━━━ DOWNTIME ESTIMATE (DowntimeEstimationSkill) ━━━
{json.dumps(downtime_estimate, indent=2, default=str)}

Analyze the production impact:
1. Which work orders are directly blocked by this machine going offline?
2. Which orders can be rerouted to alternative machines ({', '.join(production_data.get('alternative_machines_available', []) or ['none identified'])})?
3. Are any critical/high priority orders at risk of missing customer deadlines?
4. What is the total financial and production exposure?
5. Which customers need to be proactively notified?

Estimated downtime is {downtime_estimate.get('primary_estimate_hours', 'unknown')} hours.
Revenue at risk: ${production_data.get('estimated_revenue_at_risk_usd', 0):,.0f}

Return your structured JSON analysis now.
"""
