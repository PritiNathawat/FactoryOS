'use client'

/**
 * IncidentView — Client Component
 * ================================
 * The live Incident Submission page.
 *
 * Flow:
 *   1. Plant Manager fills in the incident form
 *   2. Clicks "Analyze Incident" → POST /api/v1/analysis/incidents
 *   3. Loading state shows animated agent progress
 *   4. On success: save result to sessionStorage → navigate to /decisions
 *   5. On error: show error banner with retry option
 *
 * Also provides a "Run Demo Analysis" button for quick demonstrations
 * (calls GET /api/v1/analysis/incidents/demo — no form required).
 */

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  TextField,
  Typography,
  Alert,
  Chip,
} from '@mui/material'
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined'
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined'
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined'
import PageHeader from '@/components/ui/PageHeader'
import { analyzeIncident, runDemoAnalysis } from '@/lib/api'
import { saveAnalysisResult } from '@/lib/store'
import type { IncidentSeverity } from '@/types'

// ─── Agent Progress Steps ─────────────────────────────────────
// Shown sequentially during analysis to visualise the multi-agent pipeline.

const AGENT_STEPS = [
  { label: 'Manager Agent', detail: 'Classifying incident and assessing risk...' },
  { label: 'Maintenance Agent', detail: 'Analyzing machine history and failure patterns...' },
  { label: 'Inventory Agent', detail: 'Checking parts availability and supplier options...' },
  { label: 'Production Agent', detail: 'Evaluating work orders and production impact...' },
  { label: 'Cost Intelligence Agent', detail: 'Running financial models across repair approaches...' },
  { label: 'Reporting Agent', detail: 'Generating executive summary...' },
]

// ─── Form State ───────────────────────────────────────────────

interface FormState {
  title: string
  description: string
  equipment_id: string
  location: string
  severity: IncidentSeverity
}

const INITIAL_FORM: FormState = {
  title: '',
  description: '',
  equipment_id: '',
  location: '',
  severity: 'high',
}

// ─── Component ────────────────────────────────────────────────

export default function IncidentView() {
  const router = useRouter()
  const [form, setForm] = useState<FormState>(INITIAL_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [activeStep, setActiveStep] = useState(-1)
  const [error, setError] = useState<string | null>(null)

  // Animate through agent steps while the API call runs
  const startAgentAnimation = useCallback(() => {
    setActiveStep(0)
    let step = 0
    const interval = setInterval(() => {
      step += 1
      if (step < AGENT_STEPS.length) {
        setActiveStep(step)
      } else {
        clearInterval(interval)
      }
    }, 3500)
    return interval
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!form.title.trim() || !form.description.trim()) return

    setSubmitting(true)
    setError(null)
    const interval = startAgentAnimation()

    try {
      const result = await analyzeIncident({
        incident: {
          title: form.title.trim(),
          description: form.description.trim(),
          equipment_id: form.equipment_id.trim() || undefined,
          location: form.location.trim() || undefined,
          severity: form.severity,
        },
      })
      saveAnalysisResult(result)
      router.push('/decisions')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed. Please try again.'
      setError(message)
      setSubmitting(false)
      setActiveStep(-1)
    } finally {
      clearInterval(interval)
    }
  }, [form, router, startAgentAnimation])

  const handleDemo = useCallback(async () => {
    setSubmitting(true)
    setError(null)
    const interval = startAgentAnimation()

    try {
      const result = await runDemoAnalysis()
      saveAnalysisResult(result)
      router.push('/decisions')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Demo analysis failed. Is the backend running?'
      setError(message)
      setSubmitting(false)
      setActiveStep(-1)
    } finally {
      clearInterval(interval)
    }
  }, [router, startAgentAnimation])

  const isFormValid = form.title.trim().length > 0 && form.description.trim().length > 10

  if (submitting) {
    return <AnalysisLoading activeStep={activeStep} />
  }

  return (
    <>
      <PageHeader
        title="Report Incident"
        subtitle="Submit a manufacturing disruption for AI-powered analysis"
        action={
          <Button
            variant="outlined"
            size="small"
            startIcon={<PlayArrowOutlinedIcon />}
            onClick={handleDemo}
            id="btn-run-demo"
            sx={{ whiteSpace: 'nowrap' }}
          >
            Run Demo Analysis
          </Button>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
          gap: 3,
        }}
      >
        {/* ── Incident Form ────────────────────────────────── */}
        <Card>
          <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
              <Box
                sx={{
                  width: 36,
                  height: 36,
                  borderRadius: '8px',
                  backgroundColor: '#fef3e2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  '& svg': { fontSize: 20, color: '#f29900' },
                }}
              >
                <WarningAmberOutlinedIcon />
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Incident Details
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <TextField
                id="incident-title"
                label="Incident Title"
                placeholder="e.g. CNC Machine M-12 Bearing Failure"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                required
                fullWidth
                inputProps={{ maxLength: 200 }}
                helperText="A brief, descriptive title for this incident"
              />

              <TextField
                id="incident-description"
                label="Description"
                placeholder="Describe what happened, symptoms observed, and any relevant context..."
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                required
                fullWidth
                multiline
                rows={5}
                inputProps={{ maxLength: 2000 }}
                helperText={`${form.description.length}/2000 characters`}
              />

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <TextField
                  id="incident-equipment"
                  label="Equipment ID"
                  placeholder="e.g. M-12"
                  value={form.equipment_id}
                  onChange={(e) => setForm((f) => ({ ...f, equipment_id: e.target.value }))}
                  fullWidth
                  helperText="Optional — machine or asset identifier"
                />
                <TextField
                  id="incident-location"
                  label="Location"
                  placeholder="e.g. Bay 3, Line A"
                  value={form.location}
                  onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                  fullWidth
                  helperText="Optional — plant section or area"
                />
              </Box>

              <FormControl fullWidth required>
                <InputLabel id="severity-label">Severity</InputLabel>
                <Select
                  labelId="severity-label"
                  id="incident-severity"
                  value={form.severity}
                  label="Severity"
                  onChange={(e) =>
                    setForm((f) => ({ ...f, severity: e.target.value as IncidentSeverity }))
                  }
                >
                  <MenuItem value="low">Low — Minor disruption, production continues</MenuItem>
                  <MenuItem value="medium">Medium — Partial impact, some lines affected</MenuItem>
                  <MenuItem value="high">High — Significant stoppage, multiple systems affected</MenuItem>
                  <MenuItem value="critical">Critical — Full production halt, safety risk</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ pt: 1 }}>
                <Button
                  id="btn-analyze-incident"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={!isFormValid}
                  onClick={handleSubmit}
                  startIcon={<AutoAwesomeOutlinedIcon />}
                  sx={{ py: 1.5 }}
                >
                  Analyze Incident with AI
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* ── AI Platform Info Panel ───────────────────────── */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Card>
            <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
              <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1.5, display: 'block' }}>
                How it works
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {AGENT_STEPS.map((step, i) => (
                  <Box key={step.label} sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
                    <Box
                      sx={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        backgroundColor: '#e8f0fe',
                        color: '#1a73e8',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        fontSize: '0.6875rem',
                        fontWeight: 700,
                        mt: 0.25,
                      }}
                    >
                      {i + 1}
                    </Box>
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                        {step.label}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        {step.detail}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
              <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1.5, display: 'block' }}>
                Demo Mode
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                Try the AI Platform instantly with the pre-configured Machine M-12 bearing failure scenario.
              </Typography>
              <Button
                id="btn-demo-secondary"
                variant="outlined"
                fullWidth
                startIcon={<PlayArrowOutlinedIcon />}
                onClick={handleDemo}
              >
                Run M-12 Demo
              </Button>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </>
  )
}

// ─── Analysis Loading View ────────────────────────────────────

function AnalysisLoading({ activeStep }: { activeStep: number }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        py: 8,
        gap: 4,
      }}
    >
      {/* Progress bar */}
      <Box sx={{ width: '100%', maxWidth: 560 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            AI Platform Analyzing
          </Typography>
          <CircularProgress size={20} sx={{ mt: 0.25 }} />
        </Box>
        <LinearProgress sx={{ borderRadius: 4, height: 6 }} />
        <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.75, display: 'block' }}>
          Running multi-agent analysis — typically 10–30 seconds
        </Typography>
      </Box>

      {/* Agent steps */}
      <Card sx={{ width: '100%', maxWidth: 560 }}>
        <CardContent sx={{ p: 3, '&:last-child': { pb: 3 } }}>
          <Typography variant="overline" sx={{ color: 'text.secondary', mb: 2, display: 'block' }}>
            Agent Pipeline
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {AGENT_STEPS.map((step, i) => {
              const isDone = i < activeStep
              const isActive = i === activeStep
              const isPending = i > activeStep

              return (
                <Box
                  key={step.label}
                  sx={{
                    display: 'flex',
                    gap: 2,
                    alignItems: 'center',
                    opacity: isPending ? 0.4 : 1,
                    transition: 'opacity 0.4s ease',
                  }}
                >
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      backgroundColor: isDone
                        ? '#e6f4ea'
                        : isActive
                        ? '#e8f0fe'
                        : '#f1f3f4',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      transition: 'background-color 0.3s ease',
                    }}
                  >
                    {isDone ? (
                      <Typography sx={{ fontSize: 14, color: '#1e8e3e' }}>✓</Typography>
                    ) : isActive ? (
                      <CircularProgress size={14} thickness={5} />
                    ) : (
                      <Typography sx={{ fontSize: 12, color: '#9aa0a6' }}>{i + 1}</Typography>
                    )}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 600,
                        color: isDone ? 'success.dark' : isActive ? 'primary.main' : 'text.secondary',
                      }}
                    >
                      {step.label}
                    </Typography>
                    {isActive && (
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        {step.detail}
                      </Typography>
                    )}
                    {isDone && (
                      <Chip
                        label="Complete"
                        size="small"
                        sx={{
                          height: 18,
                          fontSize: '0.625rem',
                          fontWeight: 600,
                          backgroundColor: '#e6f4ea',
                          color: '#137333',
                          mt: 0.25,
                        }}
                      />
                    )}
                  </Box>
                </Box>
              )
            })}
          </Box>
        </CardContent>
      </Card>

      <Divider sx={{ width: '100%', maxWidth: 560 }} />
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        Do not close this window. You will be redirected automatically when analysis is complete.
      </Typography>
    </Box>
  )
}
