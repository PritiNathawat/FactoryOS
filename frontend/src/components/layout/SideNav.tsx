'use client'

/**
 * SideNav
 * ========
 * Persistent navigation drawer on desktop, temporary (slide-in) on mobile.
 *
 * Navigation pattern: Google Cloud Console style
 *   - Active item: blue filled container (#e8f0fe background, #1a73e8 text + icon)
 *   - Hover state: very light gray (#f1f3f4)
 *   - Icons: outlined style, 20px
 *
 * Implementation notes:
 *   - Uses usePathname() for active route detection — no manual tracking
 *   - Uses useRouter().push() instead of <Link component> to avoid MUI polymorphic typing issues
 *   - The logo area height (64px) matches the TopBar Toolbar height exactly
 */

import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from '@mui/material'
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined'
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined'
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined'
import SummarizeOutlinedIcon from '@mui/icons-material/SummarizeOutlined'
import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing'
import { usePathname, useRouter } from 'next/navigation'
import type { ReactNode } from 'react'

// ─── Navigation Configuration ─────────────────────────────────

interface NavItem {
  label: string
  href: string
  icon: ReactNode
  ariaLabel: string
}

const NAV_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: <DashboardOutlinedIcon sx={{ fontSize: 20 }} />,
    ariaLabel: 'Navigate to Dashboard',
  },
  {
    label: 'Incidents',
    href: '/incidents',
    icon: <WarningAmberOutlinedIcon sx={{ fontSize: 20 }} />,
    ariaLabel: 'Navigate to Incidents',
  },
  {
    label: 'Decision Center',
    href: '/decisions',
    icon: <AccountTreeOutlinedIcon sx={{ fontSize: 20 }} />,
    ariaLabel: 'Navigate to Decision Center',
  },
  {
    label: 'Reports',
    href: '/reports',
    icon: <SummarizeOutlinedIcon sx={{ fontSize: 20 }} />,
    ariaLabel: 'Navigate to Reports',
  },
]

// ─── Props ────────────────────────────────────────────────────

interface SideNavProps {
  drawerWidth: number
  mobileOpen: boolean
  onClose: () => void
}

// ─── Drawer Content ───────────────────────────────────────────

function DrawerContent({ onClose }: { onClose: () => void }) {
  const pathname = usePathname()
  const router = useRouter()

  const handleNavigate = (href: string) => {
    router.push(href)
    onClose() // Close mobile drawer after navigation
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* ── Logo Area — matches TopBar height ─────────────── */}
      <Toolbar
        sx={{
          px: 2.5,
          gap: 1.5,
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          flexShrink: 0,
        }}
      >
        {/* Logo icon */}
        <Box
          sx={{
            width: 34,
            height: 34,
            borderRadius: '9px',
            backgroundColor: '#e8f0fe',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <PrecisionManufacturingIcon sx={{ color: '#1a73e8', fontSize: 18 }} />
        </Box>

        {/* Wordmark */}
        <Box>
          <Typography
            variant="h6"
            component="div"
            sx={{
              fontWeight: 700,
              fontSize: '0.9375rem',
              color: 'text.primary',
              letterSpacing: '-0.2px',
              lineHeight: 1.2,
            }}
          >
            FactoryOS
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontSize: '0.625rem',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              lineHeight: 1,
            }}
          >
            AI Operations
          </Typography>
        </Box>
      </Toolbar>

      {/* ── Navigation Items ──────────────────────────────── */}
      <Box sx={{ flex: 1, overflowY: 'auto', pt: 1.5, pb: 1 }}>
        <List disablePadding>
          {NAV_ITEMS.map((item) => {
            // An item is active if the current path is exactly the href
            // or starts with href/ (for nested routes in future sprints)
            const isActive =
              pathname === item.href ||
              (item.href !== '/' && pathname.startsWith(item.href + '/'))

            return (
              <ListItem key={item.href} disablePadding>
                <ListItemButton
                  selected={isActive}
                  onClick={() => handleNavigate(item.href)}
                  aria-label={item.ariaLabel}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            )
          })}
        </List>
      </Box>

      {/* ── Footer ────────────────────────────────────────── */}
      <Box
        sx={{
          p: 2,
          borderTop: '1px solid rgba(0,0,0,0.06)',
          flexShrink: 0,
        }}
      >
        <Typography
          variant="caption"
          sx={{ display: 'block', color: 'text.secondary', fontSize: '0.6875rem' }}
        >
          FactoryOS v0.1.0
        </Typography>
        <Typography
          variant="caption"
          sx={{ color: 'text.secondary', fontSize: '0.6875rem' }}
        >
          Sprint 1 — Foundation
        </Typography>
      </Box>
    </Box>
  )
}

// ─── Main Component ───────────────────────────────────────────

export default function SideNav({
  drawerWidth,
  mobileOpen,
  onClose,
}: SideNavProps) {
  return (
    <Box
      component="nav"
      sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      aria-label="Main navigation"
    >
      {/* Mobile: temporary drawer (slides in, overlay) */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onClose}
        ModalProps={{
          keepMounted: true, // Better mobile performance — keeps DOM in place
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <DrawerContent onClose={onClose} />
      </Drawer>

      {/* Desktop: permanent drawer (always visible, no overlay) */}
      <Drawer
        variant="permanent"
        open
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <DrawerContent onClose={onClose} />
      </Drawer>
    </Box>
  )
}
