'use client'

/**
 * EmptyState
 * ===========
 * Placeholder component for features not yet implemented.
 *
 * Used by Incidents, Decision Center, and Reports pages in Sprint 1.
 * Better than a blank page — it communicates intent clearly and looks intentional.
 */

import { Box, Typography } from '@mui/material'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  /** Icon rendered in the colored container — should be an MUI icon component */
  icon: ReactNode
  /** Feature name — displayed as the heading */
  feature: string
  /** Short description of what this feature will do */
  description: string
  /** When this feature will be available (e.g. "Sprint 2") */
  availableIn: string
}

export default function EmptyState({
  icon,
  feature,
  description,
  availableIn,
}: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: { xs: 8, md: 12 },
        textAlign: 'center',
        gap: 1.5,
      }}
    >
      {/* Icon container */}
      <Box
        sx={{
          width: 72,
          height: 72,
          borderRadius: '16px',
          backgroundColor: '#f1f3f4',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 1,
          '& svg': { fontSize: 34, color: '#9aa0a6' },
        }}
      >
        {icon}
      </Box>

      {/* Feature name */}
      <Typography
        variant="h5"
        sx={{ fontWeight: 600, color: 'text.primary' }}
      >
        {feature}
      </Typography>

      {/* Description */}
      <Typography
        variant="body2"
        sx={{ color: 'text.secondary', maxWidth: 380 }}
      >
        {description}
      </Typography>

      {/* Sprint label */}
      <Typography
        variant="caption"
        sx={{
          mt: 1,
          display: 'inline-block',
          px: 2,
          py: 0.5,
          borderRadius: 6,
          backgroundColor: '#f1f3f4',
          color: 'text.secondary',
          fontWeight: 500,
        }}
      >
        Available in {availableIn}
      </Typography>
    </Box>
  )
}
