/**
 * FactoryOS — Shared TypeScript Types
 *
 * Single source of truth for types used across the frontend.
 * Components express business semantics through these types,
 * not implementation details like colors or CSS classes.
 */

// ─── Status ───────────────────────────────────────────────────

/**
 * Semantic status levels used across all status indicators.
 * Components map these to colors internally — callers express meaning, not appearance.
 */
export type StatusLevel = 'healthy' | 'warning' | 'critical' | 'info' | 'neutral'

// ─── Environment ──────────────────────────────────────────────

export type Environment = 'development' | 'staging' | 'production'

// ─── Navigation ───────────────────────────────────────────────

export interface NavItem {
  label: string
  href: string
}

// ─── Dashboard ────────────────────────────────────────────────

export interface MetricCardData {
  id: string
  title: string
  value: string
  /** Optional secondary line displayed below the main value */
  detail?: string
  status: StatusLevel
  /** Overrides the default status label on the chip */
  statusLabel?: string
}

// ─── API ──────────────────────────────────────────────────────

/** Standard error envelope returned by the FactoryOS API */
export interface APIError {
  error: string
  detail: string
  status_code: number
}

/** Response body for GET /api/v1/health */
export interface HealthResponse {
  status: string
  timestamp: string
  environment: string
}

/** Response body for GET /api/v1/version */
export interface VersionResponse {
  name: string
  version: string
  environment: string
}

// ─── AI Platform — Incident Input ─────────────────────────────

/** Severity levels matching the backend IncidentSeverity enum */
export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical'

/**
 * Incident input submitted to the AI Platform.
 * Mirrors backend app/schemas/incident.py → IncidentInput
 */
export interface IncidentInput {
  incident_id?: string
  title: string
  description: string
  equipment_id?: string
  location?: string
  reported_by?: string
  severity: IncidentSeverity
}

/** Request body for POST /api/v1/analysis/incidents */
export interface AnalysisRequest {
  incident: IncidentInput
}

// ─── AI Platform — Recovery Plans ─────────────────────────────

export type PlanType = 'economical' | 'rapid' | 'balanced'

/**
 * A single step within a RecoveryPlan.
 * Mirrors backend app/schemas/recovery.py → RecoveryStep
 */
export interface RecoveryStep {
  step_number: number
  action: string
  responsible_party: string
  estimated_duration_hours: number
  resources_required: string[]
  dependencies: string[]
}

/**
 * One of three AI-generated recovery plans (A, B, or C).
 * Mirrors backend app/schemas/recovery.py → RecoveryPlan
 */
export interface RecoveryPlan {
  plan_id: string         // "A", "B", or "C"
  plan_type: PlanType
  label: string           // "Economical Recovery", "Rapid Recovery", "Balanced Recovery"
  description: string
  estimated_cost_usd: number
  estimated_downtime_hours: number
  production_impact_units?: number
  confidence: number      // 0.0 - 1.0
  reasoning: string
  steps: RecoveryStep[]
  risks: string[]
  prerequisites: string[]
}

// ─── AI Platform — Agent Responses ────────────────────────────

export type AgentStatus = 'success' | 'partial' | 'error' | 'skipped'

/**
 * Response from a single domain agent.
 * Mirrors backend app/schemas/agent.py → AgentResponse
 */
export interface AgentResponse {
  agent_name: string
  status: AgentStatus
  confidence: number
  reasoning: string
  recommendation: string
  tools_used: string[]
  data: Record<string, unknown>
  execution_time_ms?: number
  error_message?: string
}

// ─── AI Platform — Orchestrator Result ────────────────────────

/**
 * The complete result of running the FactoryOS AI pipeline.
 * Mirrors backend app/schemas/recovery.py → OrchestratorResult
 *
 * This is what POST /api/v1/analysis/incidents returns.
 */
export interface OrchestratorResult {
  incident_id: string
  status: string
  agents_consulted: string[]
  incident_category: string
  incident_severity: string
  plans: RecoveryPlan[]
  executive_summary: string
  confidence_overall: number  // 0.0 - 1.0
  requires_human_approval: boolean
  human_approval_reason?: string
  analyzed_at: string
  agent_responses: Record<string, AgentResponse>
  model_used?: string
}

// ─── AI Platform — Platform Status ────────────────────────────

export interface AgentMeta {
  name: string
  description: string
  version: string
}

/** Response from GET /api/v1/analysis/status */
export interface PlatformStatus {
  status: string
  gemini_mode: 'mock' | 'live'
  gemini_model: string
  agents: AgentMeta[]
  tools: string[]
  tool_count: number
  agent_count: number
}

// ─── Approval Decisions ───────────────────────────────────────

export type ApprovalAction = 'approved' | 'rejected' | 'review_requested'

export interface ApprovalDecision {
  incident_id: string
  selected_plan_id: string | null
  action: ApprovalAction
  notes?: string
  decided_at: string
}
