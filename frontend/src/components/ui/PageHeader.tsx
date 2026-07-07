'use client'

/**
 * PageHeader
 * ===========
 * Consistent top-of-page section used on every route.
 *
 * Renders a page title, optional subtitle, optional right-side action slot,
 * and a divider to separate the header from page content.
 *
 * The `action` slot is intentionally generic (ReactNode) — callers decide
 * what goes there (e.g., a "New Incident" button in Sprint 2).
 */

import { Box, Divider, Typography, type SxProps, type Theme } from '@mui/material'
import type { ReactNode } from 'react'

interface PageHeaderProps {
  /** The page title — rendered as an <h1> for correct semantic structure */
  title: string
  /** Optional subtitle displayed below the title */
  subtitle?: string
  /** Optional content rendered on the right side of the header */
  action?: ReactNode
  sx?: SxProps<Theme>
}

export default function PageHeader({
  title,
  subtitle,
  action,
  sx,
}: PageHeaderProps) {
  return (
    <Box sx={{ mb: 4, ...sx }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: 2,
        }}
      >
        {/* Title + subtitle */}
        <Box>
          {/* h1 for SEO and screen reader semantics — one per page */}
          <Typography
            variant="h4"
            component="h1"
            sx={{ fontWeight: 600, color: 'text.primary', mb: subtitle ? 0.5 : 0 }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {subtitle}
            </Typography>
          )}
        </Box>

        {/* Right-side action slot */}
        {action && <Box sx={{ flexShrink: 0, ml: 2 }}>{action}</Box>}
      </Box>

      <Divider />
    </Box>
  )
}
