'use client'

/**
 * MetricCard
 * ===========
 * The core dashboard information card.
 *
 * Layout:
 *   ┌──────────────────────────────────┐
 *   │  [icon container]  [StatusChip]  │
 *   │                                  │
 *   │  TITLE (overline)                │
 *   │  Value (h5, semibold)            │
 *   │  detail (body2, gray) optional   │
 *   └──────────────────────────────────┘
 *
 * The icon container uses a colored background derived from the status level,
 * creating a visual hierarchy that communicates health at a glance.
 */

import {
  Box,
  Card,
  CardContent,
  Typography,
  type SxProps,
  type Theme,
} from '@mui/material'
import type { ReactNode } from 'react'
import type { StatusLevel } from '@/types'
import StatusChip from './StatusChip'

// Icon container colors — same semantic mapping as StatusChip
const ICON_COLORS: Record<StatusLevel, { bg: string; color: string }> = {
  healthy:  { bg: '#e6f4ea', color: '#1e8e3e' },
  warning:  { bg: '#fef3e2', color: '#f29900' },
  critical: { bg: '#fce8e6', color: '#d93025' },
  info:     { bg: '#e8f0fe', color: '#1a73e8' },
  neutral:  { bg: '#f1f3f4', color: '#5f6368' },
}

interface MetricCardProps {
  /** Section label — displayed as small uppercase overline text */
  title: string
  /** Primary metric — the main value displayed prominently */
  value: string
  /** Optional secondary line below the value */
  detail?: string
  /** Semantic status level — controls icon background and chip color */
  status: StatusLevel
  /** Override the default status label on the chip */
  statusLabel?: string
  /** MUI icon component rendered inside the icon container */
  icon: ReactNode
  sx?: SxProps<Theme>
}

export default function MetricCard({
  title,
  value,
  detail,
  status,
  statusLabel,
  icon,
  sx,
}: MetricCardProps) {
  const iconColors = ICON_COLORS[status]

  return (
    <Card sx={{ height: '100%', ...sx }}>
      <CardContent
        sx={{
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          // Override MUI's default 16px bottom padding on the last child
          '&:last-child': { pb: 3 },
        }}
      >
        {/* ── Row 1: Icon + Status Chip ─────────────────────── */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            mb: 2.5,
          }}
        >
          {/* Colored icon container */}
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: '10px',
              backgroundColor: iconColors.bg,
              color: iconColors.color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              // Target the SVG icon inside
              '& svg': { fontSize: 22 },
            }}
          >
            {icon}
          </Box>

          <StatusChip status={status} label={statusLabel} />
        </Box>

        {/* ── Row 2: Title ──────────────────────────────────── */}
        <Typography
          variant="overline"
          component="p"
          sx={{
            mb: 0.75,
            color: 'text.secondary',
            lineHeight: 1,
          }}
        >
          {title}
        </Typography>

        {/* ── Row 3: Primary value ──────────────────────────── */}
        <Typography
          variant="h5"
          component="p"
          sx={{
            fontWeight: 600,
            color: 'text.primary',
            lineHeight: 1.3,
            // Allow long values (e.g., "Schedule Preventive Maintenance") to wrap
            wordBreak: 'break-word',
          }}
        >
          {value}
        </Typography>

        {/* ── Row 4: Optional detail ────────────────────────── */}
        {detail && (
          <Typography
            variant="body2"
            sx={{ mt: 0.75, color: 'text.secondary' }}
          >
            {detail}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
