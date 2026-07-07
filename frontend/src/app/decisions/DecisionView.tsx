'use client'

/**
 * DecisionView — Client Component
 * =================================
 * The Decision Center: displays three AI-generated recovery plans
 * and the Plant Manager's approval workflow.
 *
 * Data sources (in priority order):
 *   1. sessionStorage — populated when user came from Incidents page
 *   2. Demo endpoint — "Run Demo" button for direct navigation
 *
 * Plan layout:
 *   Plan A — Economical  (minimize cost)
 *   Plan B — Rapid       (minimize downtime)
 *   Plan C — Balanced    (optimal tradeoff)
 *
 * Approval workflow:
 *   Approve → save decision → show success
 *   Reject  → show rejection confirmation
 *   Request Review → prompt for notes → save
 */

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  TextField,
  Typography,
} from '@mui/material'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined'
import ReviewsOutlinedIcon from '@mui/icons-material/ReviewsOutlined'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined'
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined'
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord'
import PageHeader from '@/components/ui/PageHeader'
import StatusChip from '@/components/ui/StatusChip'
import { runDemoAnalysis } from '@/lib/api'
import {
  loadAnalysisResult,
  saveAnalysisResult,
  saveApprovalDecision,
  clearAnalysisResult,
} from '@/lib/store'
import type { OrchestratorResult, RecoveryPlan, ApprovalAction } from '@/types'

// ─── Plan Visual Config ───────────────────────────────────────

const PLAN_CONFIG = {
  economical: {
    label: 'Plan A — Economical',
    description: 'Minimizes total cost while maintaining acceptable timelines.',
    accent: '#137333',
    accentBg: '#e6f4ea',
    chipLabel: 'Lowest Cost',
    chipBg: '#e6f4ea',
    chipColor: '#137333',
  },
  rapid: {
    label: 'Plan B — Rapid',
    description: 'Minimizes downtime — fastest return to production.',
    accent: '#c5221f',
    accentBg: '#fce8e6',
    chipLabel: 'Fastest',
    chipBg: '#fce8e6',
    chipColor: '#c5221f',
  },
  balanced: {
    label: 'Plan C — Balanced',
    description: 'Optimal tradeoff between cost efficiency and speed.',
    accent: '#1a73e8',
    accentBg: '#e8f0fe',
    chipLabel: 'Recommended',
    chipBg: '#e8f0fe',
    chipColor: '#1a73e8',
  },
} as const

// ─── Main Component ───────────────────────────────────────────

export default function DecisionView() {
  const router = useRouter()
  const [result, setResult] = useState<OrchestratorResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [fetching, setFetching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [approved, setApproved] = useState(false)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<ApprovalAction | null>(null)
  const [pendingPlanId, setPendingPlanId] = useState<string | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')

  useEffect(() => {
    const stored = loadAnalysisResult()
    setResult(stored)
    setLoading(false)
  }, [])

  const handleRunDemo = useCallback(async () => {
    setFetching(true)
    setError(null)
    try {
      const res = await runDemoAnalysis()
      saveAnalysisResult(res)
      setResult(res)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not reach the backend. Is the server running on port 8000?',
      )
    } finally {
      setFetching(false)
    }
  }, [])

  const openDialog = useCallback(
    (action: ApprovalAction, planId: string | null) => {
      setPendingAction(action)
      setPendingPlanId(planId)
      setReviewNotes('')
      setDialogOpen(true)
    },
    [],
  )

  const handleConfirm = useCallback(() => {
    if (!pendingAction || !result) return
    saveApprovalDecision({
      incident_id: result.incident_id,
      selected_plan_id: pendingPlanId,
      action: pendingAction,
      notes: reviewNotes || undefined,
      decided_at: new Date().toISOString(),
    })
    setDialogOpen(false)
    setApproved(true)
    clearAnalysisResult()
  }, [pendingAction, pendingPlanId, result, reviewNotes])

  // ── Loading state ──────────────────────────────────────────
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        <CircularProgress />
      </Box>
    )
  }

  // ── Approval success ───────────────────────────────────────
  if (approved) {
    return (
      <>
        <PageHeader
          title="Decision Center"
          subtitle="AI-generated recovery plans for active incidents"
        />
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 8,
            gap: 2,
            textAlign: 'center',
          }}
        >
          <Box
            sx={{
              width: 72,
              height: 72,
              borderRadius: '50%',
              backgroundColor: '#e6f4ea',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              '& svg': { fontSize: 38, color: '#1e8e3e' },
            }}
          >
            <CheckCircleOutlineIcon />
          </Box>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            Decision Recorded
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', maxWidth: 400 }}>
            Your decision has been logged. In production this would trigger the execution
            workflow and notify the maintenance team.
          </Typography>
          <Button
            variant="contained"
            onClick={() => router.push('/incidents')}
            sx={{ mt: 2 }}
          >
            Analyze Another Incident
          </Button>
        </Box>
      </>
    )
  }

  // ── No result — show prompt ────────────────────────────────
  if (!result) {
    return (
      <>
        <PageHeader
          title="Decision Center"
          subtitle="AI-generated recovery plans for active incidents"
          action={
            <Button
              variant="contained"
              startIcon={<PlayArrowOutlinedIcon />}
              onClick={handleRunDemo}
              disabled={fetching}
              id="btn-run-demo-decisions"
            >
              {fetching ? 'Running Analysis…' : 'Run Demo Analysis'}
            </Button>
          }
        />

        {fetching && <LinearProgress sx={{ mb: 3, borderRadius: 4 }} />}

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 10,
            gap: 2,
            textAlign: 'center',
          }}
        >
          <Box
            sx={{
              width: 72,
              height: 72,
              borderRadius: '16px',
              backgroundColor: '#f1f3f4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              '& svg': { fontSize: 34, color: '#9aa0a6' },
            }}
          >
            <WarningAmberOutlinedIcon />
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            No Active Analysis
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', maxWidth: 380 }}>
            Submit an incident from the{' '}
            <Box
              component="span"
              onClick={() => router.push('/incidents')}
              sx={{ color: 'primary.main', cursor: 'pointer', fontWeight: 500 }}
            >
              Incidents page
            </Box>{' '}
            to generate recovery plans, or run the built-in demo.
          </Typography>
        </Box>
      </>
    )
  }

  // ── Full Decision Center ───────────────────────────────────
  return (
    <>
      <PageHeader
        title="Decision Center"
        subtitle={`Incident: ${result.incident_id}`}
        action={
          <Button
            variant="outlined"
            size="small"
            startIcon={<PlayArrowOutlinedIcon />}
            onClick={handleRunDemo}
            disabled={fetching}
            id="btn-refresh-demo"
          >
            New Demo
          </Button>
        }
      />

      {/* Executive Summary */}
      <ExecutiveSummaryBanner result={result} />

      {/* Human Approval Banner */}
      {result.requires_human_approval && (
        <Alert
          severity="warning"
          icon={<WarningAmberOutlinedIcon />}
          sx={{ mb: 3 }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Human Approval Required
          </Typography>
          <Typography variant="caption">
            {result.human_approval_reason ??
              'This incident requires manual review before plan execution.'}
          </Typography>
        </Alert>
      )}

      {/* Recovery Plans Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
          gap: 3,
          mb: 4,
        }}
      >
        {result.plans.map((plan) => (
          <PlanCard
            key={plan.plan_id}
            plan={plan}
            onApprove={() => openDialog('approved', plan.plan_id)}
          />
        ))}
      </Box>

      {/* Global action strip */}
      <Card sx={{ mb: 3 }}>
        <CardContent
          sx={{
            p: 3,
            '&:last-child': { pb: 3 },
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 2,
            alignItems: { sm: 'center' },
            justifyContent: 'space-between',
          }}
        >
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
              Plant Manager Decision
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Select a plan to approve above, or use the options below.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            <Button
              id="btn-reject"
              variant="outlined"
              color="error"
              startIcon={<CancelOutlinedIcon />}
              onClick={() => openDialog('rejected', null)}
            >
              Reject All Plans
            </Button>
            <Button
              id="btn-request-review"
              variant="outlined"
              startIcon={<ReviewsOutlinedIcon />}
              onClick={() => openDialog('review_requested', null)}
            >
              Request Expert Review
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Agent Findings Accordion */}
      <AgentFindingsPanel result={result} />

      {/* Approval Dialog */}
      <ApprovalDialog
        open={dialogOpen}
        action={pendingAction}
        planId={pendingPlanId}
        notes={reviewNotes}
        onNotesChange={setReviewNotes}
        onConfirm={handleConfirm}
        onClose={() => setDialogOpen(false)}
      />
    </>
  )
}

// ─── Executive Summary Banner ─────────────────────────────────

function ExecutiveSummaryBanner({ result }: { result: OrchestratorResult }) {
  const confidencePct = Math.round(result.confidence_overall * 100)

  return (
    <Card sx={{ mb: 3, borderLeft: '4px solid #1a73e8' }}>
      <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 3,
            justifyContent: 'space-between',
          }}
        >
          <Box sx={{ flex: 1 }}>
            <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1, display: 'block' }}>
              Executive Summary
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.primary', lineHeight: 1.7 }}>
              {result.executive_summary}
            </Typography>
          </Box>

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 1.5,
              minWidth: 200,
              flexShrink: 0,
            }}
          >
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>
                Category
              </Typography>
              <StatusChip
                status="warning"
                label={result.incident_category.replace(/_/g, ' ')}
                size="small"
              />
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>
                Severity
              </Typography>
              <StatusChip
                status={
                  result.incident_severity === 'critical'
                    ? 'critical'
                    : result.incident_severity === 'high'
                    ? 'warning'
                    : 'info'
                }
                label={result.incident_severity.toUpperCase()}
                size="small"
              />
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>
                AI Confidence
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={confidencePct}
                  sx={{
                    flex: 1,
                    height: 6,
                    borderRadius: 4,
                    '& .MuiLinearProgress-bar': {
                      backgroundColor:
                        confidencePct >= 75
                          ? '#1e8e3e'
                          : confidencePct >= 50
                          ? '#f29900'
                          : '#d93025',
                    },
                  }}
                />
                <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.primary', minWidth: 36 }}>
                  {confidencePct}%
                </Typography>
              </Box>
            </Box>
            <Box>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>
                Agents Consulted
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {result.agents_consulted.length} agents
              </Typography>
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

// ─── Recovery Plan Card ───────────────────────────────────────

function PlanCard({
  plan,
  onApprove,
}: {
  plan: RecoveryPlan
  onApprove: () => void
}) {
  const [stepsOpen, setStepsOpen] = useState(false)
  const config = PLAN_CONFIG[plan.plan_type] ?? PLAN_CONFIG.balanced
  const confidencePct = Math.round(plan.confidence * 100)

  return (
    <Card
      sx={{
        display: 'flex',
        flexDirection: 'column',
        border: `1px solid ${config.accentBg}`,
        borderTop: `3px solid ${config.accent}`,
      }}
    >
      <CardContent sx={{ flex: 1, p: 3, '&:last-child': { pb: 0 } }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, color: config.accent, lineHeight: 1.3 }}>
            {plan.label}
          </Typography>
          <Chip
            label={config.chipLabel}
            size="small"
            sx={{
              backgroundColor: config.chipBg,
              color: config.chipColor,
              fontWeight: 700,
              fontSize: '0.6875rem',
              ml: 1,
              flexShrink: 0,
            }}
          />
        </Box>

        <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2.5, lineHeight: 1.6 }}>
          {plan.description}
        </Typography>

        {/* Key metrics */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 1.5,
            mb: 2.5,
          }}
        >
          <MetricRow label="Est. Cost" value={`$${plan.estimated_cost_usd.toLocaleString()}`} />
          <MetricRow label="Downtime" value={`${plan.estimated_downtime_hours}h`} />
          {plan.production_impact_units != null && (
            <MetricRow label="Lost Units" value={plan.production_impact_units.toLocaleString()} />
          )}
          <MetricRow label="Confidence" value={`${confidencePct}%`} />
        </Box>

        {/* Confidence bar */}
        <Box sx={{ mb: 2.5 }}>
          <LinearProgress
            variant="determinate"
            value={confidencePct}
            sx={{
              height: 5,
              borderRadius: 4,
              '& .MuiLinearProgress-bar': { backgroundColor: config.accent },
            }}
          />
        </Box>

        {/* Reasoning */}
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 2 }}>
          {plan.reasoning}
        </Typography>

        {/* Risks */}
        {plan.risks.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1, display: 'block' }}>
              Risks
            </Typography>
            <List dense disablePadding>
              {plan.risks.map((risk, i) => (
                <ListItem key={i} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 20 }}>
                    <FiberManualRecordIcon sx={{ fontSize: 8, color: config.accent }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={risk}
                    primaryTypographyProps={{ variant: 'caption', color: 'text.secondary' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Steps accordion */}
        {plan.steps.length > 0 && (
          <Box>
            <Button
              size="small"
              onClick={() => setStepsOpen((o) => !o)}
              endIcon={stepsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              sx={{ p: 0, color: 'text.secondary', fontSize: '0.75rem' }}
            >
              {plan.steps.length} Execution Steps
            </Button>
            <Collapse in={stepsOpen}>
              <List dense disablePadding sx={{ mt: 1 }}>
                {plan.steps.map((step) => (
                  <ListItem key={step.step_number} disablePadding sx={{ mb: 1, alignItems: 'flex-start' }}>
                    <ListItemIcon sx={{ minWidth: 24, mt: 0.25 }}>
                      <Box
                        sx={{
                          width: 18,
                          height: 18,
                          borderRadius: '50%',
                          backgroundColor: config.accentBg,
                          color: config.accent,
                          fontSize: '0.625rem',
                          fontWeight: 700,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {step.step_number}
                      </Box>
                    </ListItemIcon>
                    <ListItemText
                      primary={step.action}
                      secondary={`${step.responsible_party} · ${step.estimated_duration_hours}h`}
                      primaryTypographyProps={{ variant: 'caption', fontWeight: 600 }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </Box>
        )}
      </CardContent>

      <Divider />

      {/* Approve button */}
      <Box sx={{ p: 2 }}>
        <Button
          id={`btn-approve-plan-${plan.plan_id.toLowerCase()}`}
          variant="contained"
          fullWidth
          startIcon={<CheckCircleOutlineIcon />}
          onClick={onApprove}
          sx={{
            backgroundColor: config.accent,
            '&:hover': { backgroundColor: config.accent, opacity: 0.9 },
          }}
        >
          Approve Plan {plan.plan_id}
        </Button>
      </Box>
    </Card>
  )
}

// ─── Metric Row ───────────────────────────────────────────────

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <Box
      sx={{
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        p: 1.5,
      }}
    >
      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 700, color: 'text.primary' }}>
        {value}
      </Typography>
    </Box>
  )
}

// ─── Agent Findings Panel ─────────────────────────────────────

function AgentFindingsPanel({ result }: { result: OrchestratorResult }) {
  const [open, setOpen] = useState(false)
  const agents = Object.entries(result.agent_responses)

  if (agents.length === 0) return null

  return (
    <Card>
      <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
          }}
          onClick={() => setOpen((o) => !o)}
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Agent Findings ({agents.length} agents)
          </Typography>
          {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </Box>
        <Collapse in={open}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
              gap: 2,
              mt: 2,
            }}
          >
            {agents.map(([key, agent]) => (
              <Box
                key={key}
                sx={{
                  p: 2,
                  borderRadius: '8px',
                  border: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, textTransform: 'capitalize' }}>
                    {agent.agent_name ?? key}
                  </Typography>
                  <StatusChip
                    status={
                      agent.status === 'success'
                        ? 'healthy'
                        : agent.status === 'error'
                        ? 'critical'
                        : 'warning'
                    }
                    label={agent.status}
                    size="small"
                  />
                </Box>
                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
                  {agent.recommendation}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={Math.round((agent.confidence ?? 0) * 100)}
                  sx={{ height: 4, borderRadius: 2 }}
                />
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Confidence: {Math.round((agent.confidence ?? 0) * 100)}%
                </Typography>
              </Box>
            ))}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  )
}

// ─── Approval Dialog ──────────────────────────────────────────

interface ApprovalDialogProps {
  open: boolean
  action: ApprovalAction | null
  planId: string | null
  notes: string
  onNotesChange: (v: string) => void
  onConfirm: () => void
  onClose: () => void
}

function ApprovalDialog({
  open,
  action,
  planId,
  notes,
  onNotesChange,
  onConfirm,
  onClose,
}: ApprovalDialogProps) {
  const titles: Record<ApprovalAction, string> = {
    approved: planId ? `Approve Plan ${planId}` : 'Approve Plan',
    rejected: 'Reject All Plans',
    review_requested: 'Request Expert Review',
  }

  const descriptions: Record<ApprovalAction, string> = {
    approved: `You are approving ${planId ? `Plan ${planId}` : 'this plan'} for immediate execution. This decision will be logged and the maintenance team will be notified.`,
    rejected:
      'You are rejecting all generated plans. This will be logged and the incident will remain open for further analysis.',
    review_requested:
      'You are requesting an expert review. Please add notes to help the reviewer understand your concerns.',
  }

  if (!action) return null

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{titles[action]}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
          {descriptions[action]}
        </Typography>
        {(action === 'review_requested' || action === 'rejected') && (
          <TextField
            fullWidth
            label="Notes (optional)"
            multiline
            rows={3}
            value={notes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Add context for the reviewer..."
            sx={{ mt: 1 }}
          />
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
        <Button onClick={onClose} variant="outlined">
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color={action === 'rejected' ? 'error' : 'primary'}
          id="btn-confirm-decision"
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  )
}
