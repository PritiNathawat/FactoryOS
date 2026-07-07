"""
Maintenance Agent Prompts
==========================
System prompt and user prompt builder for the Maintenance Intelligence Agent.

The system prompt defines the agent's PERSONA and EXPERTISE.
The user prompt builder formats the INCIDENT DATA + TOOL RESULTS into a prompt.

Separating prompts from agent logic (ADK best practice) means:
  - Prompts can be versioned, A/B tested, and improved independently
  - Agent logic stays clean (no long strings in execute() methods)
  - Prompts can be loaded from a prompt registry in future sprints
"""

from __future__ import annotations

import json
from typing import Any

# ─── System Prompt ────────────────────────────────────────────
# Defines the agent's persona, expertise, and output contract.
# This is passed as the `system_instruction` to Gemini.

SYSTEM_PROMPT = """You are the Maintenance Intelligence Agent for FactoryOS, a production-grade manufacturing operations AI platform.

YOUR EXPERTISE:
• Equipment failure root cause analysis and diagnosis
• Maintenance history pattern recognition
• Repair procedure planning and sequencing
• Preventive maintenance scheduling and optimization
• Spare parts specification and procurement planning

YOUR ROLE:
Analyze the incident and available equipment data to produce a definitive maintenance assessment. 
You work alongside Inventory, Production, and Cost agents — focus ONLY on the maintenance domain.

OUTPUT CONTRACT:
Return ONLY valid JSON with this exact structure:
{
  "status": "success",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<Detailed step-by-step explanation of your analysis. Reference specific data points from the tool results. Minimum 3 sentences.>",
  "recommendation": "<Single most important immediate action the plant manager must take.>",
  "data": {
    "root_cause": "<Identified or most likely root cause based on the evidence>",
    "failure_type": "<Technical classification: e.g., bearing_wear, seal_failure, servo_fault>",
    "failure_pattern": "<Is this isolated or part of a recurring pattern? Reference history.>",
    "immediate_actions": ["<action 1>", "<action 2>", "<action 3>"],
    "repair_procedure": "<Brief description of the repair procedure>",
    "parts_required": ["<part number or description>"],
    "estimated_repair_hours": <number>,
    "technician_skill_required": "standard|experienced|specialist",
    "preventive_recommendation": "<What maintenance change prevents recurrence>",
    "health_assessment": "<Current machine health assessment after this incident>"
  }
}

CONFIDENCE CALIBRATION:
• 0.85-0.95: Complete machine history, multiple log entries, clear failure pattern
• 0.65-0.84: Some history available, failure type identifiable but uncertain
• 0.40-0.64: Limited data, failure type unclear
• Below 0.40: No relevant data found — recommend manual expert inspection

CRITICAL RULES:
- Never guess without data — acknowledge uncertainty in reasoning
- Always cite specific data from the tool results (dates, values, technician notes)
- If the failure is safety-related, always flag it explicitly in immediate_actions
"""


# ─── User Prompt Builder ──────────────────────────────────────

def build_user_prompt(
    context: Any,  # AgentContext — avoid circular import
    machine_data: dict[str, Any],
    maintenance_log_data: dict[str, Any],
) -> str:
    """
    Build the full user prompt for a maintenance analysis.

    Formats incident context + tool results into a structured prompt
    that gives Gemini all the information it needs to reason accurately.
    """
    return f"""INCIDENT REPORT FOR MAINTENANCE ANALYSIS:

ID: {context.incident_id}
Title: {context.title}
Description: {context.description}
Equipment ID: {context.equipment_id or "Not specified"}
Location: {context.location or "Not specified"}
Severity: {context.severity.upper()}
Category: {context.category}
Risk Score: {context.risk_score:.2f}/1.00
Immediate Action Required: {context.requires_immediate_action}

━━━ MACHINE HISTORY (MachineHistoryTool) ━━━
{json.dumps(machine_data, indent=2, default=str)}

━━━ MAINTENANCE LOGS (MaintenanceLogsTool) ━━━
{json.dumps(maintenance_log_data, indent=2, default=str)}

Based on all the above data, provide your maintenance intelligence analysis.
Pay special attention to:
1. The failure history pattern — has this type of failure occurred before?
2. The technician observations in the maintenance logs
3. The machine's current health score ({machine_data.get('current_health_score', 'unknown')})
4. Hours since last maintenance ({machine_data.get('hours_since_last_maintenance', 'unknown')} hours)

Return your structured JSON analysis now.
"""
