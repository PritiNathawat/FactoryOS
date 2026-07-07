'use client'

/**
 * DashboardGrid
 * ==============
 * Renders the four manufacturing operations metric cards
 * plus a live AI Platform status strip fetched from the backend.
 *
 * Manufacturing cards: realistic mock data (intentional — no live sensor feed yet)
 * AI Platform strip: live data from GET /api/v1/analysis/status
 *
 * Grid layout:
 *   Mobile (xs):  1 column
 *   Tablet (sm):  2 columns
 *   Desktop (lg): 4 columns
 */

import { Box, Card, CardContent, Chip, Typography } from '@mui/material'
import FactoryOutlinedIcon from '@mui/icons-material/FactoryOutlined'
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined'
import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined'
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined'
import MetricCard from '@/components/ui/MetricCard'
import { useEffect, useState } from 'react'
import { getPlatformStatus } from '@/lib/api'
import type { StatusLevel, PlatformStatus } from '@/types'
import type { ReactNode } from 'react'

// ─── Manufacturing Metrics (intentional mock data) ────────────
// Represents realistic sensor data that would come from IoT integration
// in a production deployment. Shown as static data for the capstone demo.

interface DashboardMetric {
  id: string
  title: string
  value: string
  detail?: string
  status: StatusLevel
  statusLabel: string
  icon: ReactNode
}

const DASHBOARD_METRICS: DashboardMetric[] = [
  {
    id: 'factory-health',
    title: 'Factory Health',
    value: 'Healthy',
    status: 'healthy',
    statusLabel: 'All Systems Normal',
    icon: <FactoryOutlinedIcon />,
  },
  {
    id: 'active-incident',
    title: 'Active Incident',
    value: 'Machine M-12',
    detail: 'Inspection Required',
    status: 'warning',
    statusLabel: 'Attention Required',
    icon: <WarningAmberOutlinedIcon />,
  },
  {
    id: 'inventory-status',
    title: 'Inventory Status',
    value: 'Normal',
    status: 'healthy',
    statusLabel: 'Stock Sufficient',
    icon: <Inventory2OutlinedIcon />,
  },
  {
    id: 'ai-recommendation',
    title: 'AI Recommendation',
    value: 'Schedule Preventive Maintenance',
    status: 'info',
    statusLabel: 'Action Suggested',
    icon: <AutoAwesomeOutlinedIcon />,
  },
]

// ─── Component ────────────────────────────────────────────────

export default function DashboardGrid() {
  const [platformStatus, setPlatformStatus] = useState<PlatformStatus | null>(null)
  const [statusError, setStatusError] = useState(false)

  useEffect(() => {
    getPlatformStatus()
      .then(setPlatformStatus)
      .catch(() => setStatusError(true))
  }, [])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Manufacturing metric cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            lg: 'repeat(4, 1fr)',
          },
          gap: 3,
        }}
      >
        {DASHBOARD_METRICS.map((metric) => (
          <MetricCard
            key={metric.id}
            title={metric.title}
            value={metric.value}
            detail={metric.detail}
            status={metric.status}
            statusLabel={metric.statusLabel}
            icon={metric.icon}
          />
        ))}
      </Box>

      {/* AI Platform live status strip */}
      <AIPlatformStatus status={platformStatus} error={statusError} />
    </Box>
  )
}

// ─── AI Platform Status Strip ─────────────────────────────────

function AIPlatformStatus({
  status,
  error,
}: {
  status: PlatformStatus | null
  error: boolean
}) {
  if (error) {
    return (
      <Card sx={{ borderLeft: '4px solid #f29900' }}>
        <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            AI Platform status unavailable — backend may not be running on port 8000.
          </Typography>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card sx={{ borderLeft: '4px solid #1a73e8' }}>
      <CardContent
        sx={{
          p: 2.5,
          '&:last-child': { pb: 2.5 },
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          gap: 2,
          alignItems: { sm: 'center' },
          justifyContent: 'space-between',
        }}
      >
        <Box>
          <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 0.25 }}>
            AI Platform
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
            {status ? 'Operational' : 'Connecting…'}
          </Typography>
        </Box>

        {status && (
          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
            <StatusBadge
              label={status.gemini_mode === 'live' ? 'Gemini Live' : 'Mock Mode'}
              color={status.gemini_mode === 'live' ? '#1e8e3e' : '#b06000'}
              bg={status.gemini_mode === 'live' ? '#e6f4ea' : '#fef3e2'}
            />
            <StatusBadge
              label={`${status.agent_count} Agents`}
              color="#1967d2"
              bg="#e8f0fe"
            />
            <StatusBadge
              label={`${status.tool_count} MCP Tools`}
              color="#5f6368"
              bg="#f1f3f4"
            />
            <StatusBadge
              label={status.gemini_model}
              color="#5f6368"
              bg="#f1f3f4"
            />
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

function StatusBadge({
  label,
  color,
  bg,
}: {
  label: string
  color: string
  bg: string
}) {
  return (
    <Chip
      label={label}
      size="small"
      sx={{
        backgroundColor: bg,
        color,
        fontWeight: 600,
        fontSize: '0.6875rem',
        height: 24,
      }}
    />
  )
}
