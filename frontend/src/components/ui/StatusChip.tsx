'use client'

/**
 * StatusChip
 * ===========
 * Translates a semantic StatusLevel into a colored pill indicator.
 *
 * Callers express meaning: status="warning"
 * This component decides appearance: amber background, amber dot, dark amber text
 *
 * Why this matters: if the design for "warning" changes, it changes here — not
 * scattered across every component that uses it.
 */

import { Box, Chip, type SxProps, type Theme } from '@mui/material'
import type { StatusLevel } from '@/types'

// ─── Status → Visual Token Mapping ────────────────────────────
// Colors are intentionally NOT from the MUI theme palette.
// These are custom status indicator colors matching Google Cloud's status patterns.
const STATUS_CONFIG: Record<
  StatusLevel,
  { bg: string; color: string; dot: string; defaultLabel: string }
> = {
  healthy: {
    bg: '#e6f4ea',
    color: '#137333',
    dot: '#1e8e3e',
    defaultLabel: 'Healthy',
  },
  warning: {
    bg: '#fef3e2',
    color: '#b06000',
    dot: '#f29900',
    defaultLabel: 'Warning',
  },
  critical: {
    bg: '#fce8e6',
    color: '#c5221f',
    dot: '#d93025',
    defaultLabel: 'Critical',
  },
  info: {
    bg: '#e8f0fe',
    color: '#1967d2',
    dot: '#1a73e8',
    defaultLabel: 'Info',
  },
  neutral: {
    bg: '#f1f3f4',
    color: '#5f6368',
    dot: '#80868b',
    defaultLabel: 'Neutral',
  },
}

// ─── Component ────────────────────────────────────────────────

interface StatusChipProps {
  status: StatusLevel
  /** Override the default label for this status. */
  label?: string
  size?: 'small' | 'medium'
  sx?: SxProps<Theme>
}

export default function StatusChip({
  status,
  label,
  size = 'small',
  sx,
}: StatusChipProps) {
  const config = STATUS_CONFIG[status]
  const displayLabel = label ?? config.defaultLabel

  return (
    <Chip
      size={size}
      label={
        // Render label as a flex row with a leading dot indicator.
        // Using a Box here (not a CSS ::before pseudo-element) is more reliable
        // across browsers and easier to reason about in JSX.
        <Box
          component="span"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}
        >
          <Box
            component="span"
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: config.dot,
              flexShrink: 0,
              display: 'inline-block',
            }}
          />
          {displayLabel}
        </Box>
      }
      sx={{
        backgroundColor: config.bg,
        color: config.color,
        fontWeight: 600,
        fontSize: size === 'small' ? '0.6875rem' : '0.75rem',
        height: size === 'small' ? 24 : 28,
        '& .MuiChip-label': { px: '10px' },
        ...sx,
      }}
    />
  )
}
