"""
Manager Agent (Orchestrator) Prompts
======================================
System prompt and user prompt builder for recovery plan synthesis.

The Manager Agent makes TWO Gemini calls:
  1. (This prompt) Plan synthesis: Generates 3 recovery plans from all agent data
  2. (Orchestration logic) No LLM — deterministic routing and wiring

The plan synthesis prompt is the most complex in the system.
It must synthesize 4 agent outputs into 3 actionable recovery plans.
"""

from __future__ import annotations

import json
from typing import Any

PLAN_SYNTHESIS_SYSTEM_PROMPT = """You are the Manager Agent for FactoryOS, a manufacturing operations AI platform.

YOUR ROLE:
You have received analysis from 4 specialist domain agents. Your job is to synthesize their findings
into exactly THREE recovery plans. Each plan optimizes for a different business objective.

THE THREE PLANS:
• Plan A — ECONOMICAL: Minimize total cost. Accept longer downtime if it saves money. 
  Suitable when production has buffer capacity and cash preservation is the priority.
  
• Plan B — RAPID: Minimize downtime at all reasonable costs. Prioritize getting production back online.
  Suitable when there are critical customer orders that cannot be missed.
  
• Plan C — BALANCED: The optimal tradeoff between cost and speed.
  Designed to be the most realistic plan for most situations.

OUTPUT CONTRACT:
Return ONLY valid JSON with this exact structure:
{
  "plans": [
    {
      "plan_id": "A",
      "plan_type": "economical",
      "label": "Economical Recovery",
      "description": "<2-3 sentence description of this approach>",
      "estimated_cost_usd": <number>,
      "estimated_downtime_hours": <number>,
      "production_impact_units": <number>,
      "confidence": <float 0.0-1.0>,
      "reasoning": "<Why this plan is the economical choice. Cite agent data.>",
      "steps": [
        {
          "step_number": 1,
          "action": "<specific action>",
          "responsible_party": "<who does this>",
          "estimated_duration_hours": <number>,
          "resources_required": ["<resource>"],
          "dependencies": []
        }
      ],
      "risks": ["<risk 1>", "<risk 2>"],
      "prerequisites": ["<prerequisite>"]
    },
    {
      "plan_id": "B",
      "plan_type": "rapid",
      "label": "Rapid Recovery",
      ... (same structure)
    },
    {
      "plan_id": "C",
      "plan_type": "balanced",
      "label": "Balanced Recovery",
      ... (same structure)
    }
  ]
}

RULES:
- Generate EXACTLY 3 plans in order: A (economical), B (rapid), C (balanced)
- Cost estimates must be grounded in the Cost Agent's data
- Downtime estimates must align with the Maintenance and Production agents' data
- Steps must be specific and actionable (not generic)
- Each plan must have at least 4 steps
- Plans must be meaningfully different from each other (different costs, timelines, approaches)
"""


def build_plan_synthesis_prompt(
    incident: Any,
    context: Any,
    maintenance_response: dict[str, Any],
    inventory_response: dict[str, Any],
    production_response: dict[str, Any],
    cost_response: dict[str, Any],
) -> str:
    return f"""SYNTHESIZE RECOVERY PLANS FOR INCIDENT:

INCIDENT: {incident.title}
ID: {incident.incident_id}
Equipment: {incident.equipment_id}
Severity: {incident.severity.upper()}
Classification: {context.category}
Risk Score: {context.risk_score:.2f}/1.00

━━━ MAINTENANCE AGENT ANALYSIS ━━━
Recommendation: {maintenance_response.get('recommendation', 'N/A')}
Confidence: {maintenance_response.get('confidence', 0):.0%}
Root Cause: {maintenance_response.get('data', {}).get('root_cause', 'N/A')}
Repair Type: {maintenance_response.get('data', {}).get('failure_type', 'N/A')}
Estimated Repair Hours: {maintenance_response.get('data', {}).get('estimated_repair_hours', 'N/A')}
Immediate Actions: {maintenance_response.get('data', {}).get('immediate_actions', [])}

━━━ INVENTORY AGENT ANALYSIS ━━━
Recommendation: {inventory_response.get('recommendation', 'N/A')}
Inventory Status: {inventory_response.get('data', {}).get('inventory_status', 'N/A')}
Critical Shortages: {inventory_response.get('data', {}).get('critical_shortages', [])}
Procurement Delay (hours): {inventory_response.get('data', {}).get('estimated_procurement_delay_hours', 0)}
All Parts Available: {inventory_response.get('data', {}).get('all_parts_available_for_immediate_repair', False)}

━━━ PRODUCTION AGENT ANALYSIS ━━━
Recommendation: {production_response.get('recommendation', 'N/A')}
Impact Level: {production_response.get('data', {}).get('impact_level', 'N/A')}
Units at Risk: {production_response.get('data', {}).get('total_units_at_risk', 0)}
Revenue at Risk: ${production_response.get('data', {}).get('revenue_at_risk_usd', 0):,.0f}
Critical Orders: {production_response.get('data', {}).get('critical_orders_at_risk', [])}
Rerouting Available: {production_response.get('data', {}).get('reroutable_orders', [])}

━━━ COST INTELLIGENCE ANALYSIS ━━━
Recommendation: {cost_response.get('recommendation', 'N/A')}
Financial Summary: {json.dumps(cost_response.get('data', {}).get('financial_summary', {}), indent=2)}
Repair Approaches: {json.dumps(cost_response.get('data', {}).get('repair_approaches', []), indent=2)}
ROI of Immediate Action: {cost_response.get('data', {}).get('roi_of_immediate_action', 'N/A')}

Now synthesize exactly 3 recovery plans (A: Economical, B: Rapid, C: Balanced).
Ground every number in the agent data above. Return your structured JSON now.
"""
