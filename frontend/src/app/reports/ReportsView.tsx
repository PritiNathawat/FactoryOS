'use client'

/**
 * ReportsView — Client Component
 * ================================
 * Displays the executive report from the last completed analysis.
 *
 * Data source: sessionStorage (populated by analysis flow)
 * Graceful degradation: professional placeholder if no analysis exists.
 */

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  LinearProgress,
  Typography,
} from '@mui/material'
import SummarizeOutlinedIcon from '@mui/icons-material/SummarizeOutlined'
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined'
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined'
import PageHeader from '@/components/ui/PageHeader'
import StatusChip from '@/components/ui/StatusChip'
import { loadAnalysisResult, loadApprovalDecision } from '@/lib/store'
import type { OrchestratorResult, ApprovalDecision } from '@/types'

export default function ReportsView() {
  const router = useRouter()
  const [result, setResult] = useState<OrchestratorResult | null>(null)
  const [decision, setDecision] = useState<ApprovalDecision | null>(null)

  useEffect(() => {
    setResult(loadAnalysisResult())
    setDecision(loadApprovalDecision())
  }, [])

  return (
    <>
      <PageHeader
        title="Reports"
        subtitle="Incident analysis reports and operational summaries"
      />

      {result ? (
        <FullReport result={result} decision={decision} />
      ) : (
        <EmptyReports onNavigate={() => router.push('/incidents')} />
      )}
    </>
  )
}

// ─── Full Report ──────────────────────────────────────────────

function FullReport({
  result,
  decision,
}: {
  result: OrchestratorResult
  decision: ApprovalDecision | null
}) {
  const analyzed = new Date(result.analyzed_at)
  const confidencePct = Math.round(result.confidence_overall * 100)
  const selectedPlan = decision?.selected_plan_id
    ? result.plans.find((p) => p.plan_id === decision.selected_plan_id)
    : null

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* ── Report Header ─────────────────────────────────── */}
      <Card sx={{ borderLeft: '4px solid #1a73e8' }}>
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              gap: 3,
              justifyContent: 'space-between',
              alignItems: { sm: 'flex-start' },
            }}
          >
            <Box>
              <Typography variant="overline" sx={{ color: 'text.secondary', mb: 0.5, display: 'block' }}>
                Incident Report
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
                {result.incident_id}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                Analyzed {analyzed.toLocaleDateString()} at {analyzed.toLocaleTimeString()}
                {result.model_used ? ` · ${result.model_used}` : ''}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <StatusChip
                status={
                  result.incident_severity === 'critical'
                    ? 'critical'
                    : result.incident_severity === 'high'
                    ? 'warning'
                    : 'info'
                }
                label={`Severity: ${result.incident_severity.toUpperCase()}`}
              />
              {decision && (
                <StatusChip
                  status={
                    decision.action === 'approved'
                      ? 'healthy'
                      : decision.action === 'rejected'
                      ? 'critical'
                      : 'warning'
                  }
                  label={
                    decision.action === 'approved'
                      ? `Plan ${decision.selected_plan_id ?? ''} Approved`
                      : decision.action === 'rejected'
                      ? 'All Plans Rejected'
                      : 'Under Review'
                  }
                />
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* ── Executive Summary ─────────────────────────────── */}
      <Card>
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1.5, display: 'block' }}>
            Executive Summary
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.primary', lineHeight: 1.8 }}>
            {result.executive_summary}
          </Typography>

          <Divider sx={{ my: 2.5 }} />

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(4, 1fr)' },
              gap: 2,
            }}
          >
            <ReportMetric label="Category" value={result.incident_category.replace(/_/g, ' ')} />
            <ReportMetric label="Agents Consulted" value={`${result.agents_consulted.length}`} />
            <ReportMetric label="Plans Generated" value={`${result.plans.length}`} />
            <ReportMetric label="AI Confidence" value={`${confidencePct}%`} />
          </Box>
        </CardContent>
      </Card>

      {/* ── Selected Plan Summary ─────────────────────────── */}
      {selectedPlan && (
        <Card sx={{ borderLeft: '4px solid #1e8e3e' }}>
          <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
            <Typography variant="overline" sx={{ color: 'success.dark', mb: 1.5, display: 'block' }}>
              Approved Recovery Plan
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5 }}>
              {selectedPlan.label}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
              {selectedPlan.description}
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
              <ReportMetric
                label="Est. Cost"
                value={`$${selectedPlan.estimated_cost_usd.toLocaleString()}`}
              />
              <ReportMetric label="Downtime" value={`${selectedPlan.estimated_downtime_hours}h`} />
              <ReportMetric label="Steps" value={`${selectedPlan.steps.length}`} />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ── Agent Performance ─────────────────────────────── */}
      <Card>
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Typography variant="overline" sx={{ color: 'text.secondary', mb: 2, display: 'block' }}>
            Agent Performance
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {Object.entries(result.agent_responses).map(([key, agent]) => (
              <Box key={key}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.75 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                    {agent.agent_name ?? key}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      {Math.round((agent.confidence ?? 0) * 100)}% confidence
                    </Typography>
                    <Chip
                      label={agent.status}
                      size="small"
                      sx={{
                        height: 18,
                        fontSize: '0.625rem',
                        fontWeight: 600,
                        backgroundColor:
                          agent.status === 'success'
                            ? '#e6f4ea'
                            : agent.status === 'error'
                            ? '#fce8e6'
                            : '#fef3e2',
                        color:
                          agent.status === 'success'
                            ? '#137333'
                            : agent.status === 'error'
                            ? '#c5221f'
                            : '#b06000',
                      }}
                    />
                  </Box>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={Math.round((agent.confidence ?? 0) * 100)}
                  sx={{ height: 5, borderRadius: 4 }}
                />
                {agent.recommendation && (
                  <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block' }}>
                    {agent.recommendation}
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

// ─── Empty Reports Placeholder ────────────────────────────────

function EmptyReports({ onNavigate }: { onNavigate: () => void }) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
        gap: 3,
      }}
    >
      {/* Prompt card */}
      <Card sx={{ gridColumn: { md: '1 / -1' } }}>
        <CardContent
          sx={{
            p: 4,
            '&:last-child': { pb: 4 },
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 2,
          }}
        >
          <Box
            sx={{
              width: 64,
              height: 64,
              borderRadius: '14px',
              backgroundColor: '#e8f0fe',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              '& svg': { fontSize: 32, color: '#1a73e8' },
            }}
          >
            <SummarizeOutlinedIcon />
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            No Reports Yet
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', maxWidth: 400 }}>
            Reports are generated automatically after each incident analysis. Submit an
            incident and complete the approval workflow to generate your first report.
          </Typography>
          <Button variant="contained" onClick={onNavigate} sx={{ mt: 1 }}>
            Report an Incident
          </Button>
        </CardContent>
      </Card>

      {/* Preview cards — show what reports will look like */}
      {PREVIEW_REPORTS.map((preview) => (
        <Card key={preview.id} sx={{ opacity: 0.5 }}>
          <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
              <Box
                sx={{
                  '& svg': { fontSize: 20, color: '#9aa0a6' },
                }}
              >
                {preview.icon}
              </Box>
              <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.disabled' }}>
                {preview.title}
              </Typography>
            </Box>
            <Typography variant="caption" sx={{ color: 'text.disabled' }}>
              {preview.description}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Box>
  )
}

const PREVIEW_REPORTS = [
  {
    id: 'incident-summary',
    icon: <WarningAmberOutlinedIcon />,
    title: 'Incident Summary',
    description: 'Root cause, affected systems, and timeline of events.',
  },
  {
    id: 'agent-findings',
    icon: <AccountTreeOutlinedIcon />,
    title: 'Agent Findings',
    description: 'Individual analysis from each AI agent with confidence scores.',
  },
  {
    id: 'recovery-outcome',
    icon: <SummarizeOutlinedIcon />,
    title: 'Recovery Outcome',
    description: 'Selected recovery plan, actions taken, and lessons learned.',
  },
]

// ─── Helpers ──────────────────────────────────────────────────

function ReportMetric({ label, value }: { label: string; value: string }) {
  return (
    <Box sx={{ textAlign: 'left' }}>
      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 700, color: 'text.primary' }}>
        {value}
      </Typography>
    </Box>
  )
}
