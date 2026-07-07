'use client'

/**
 * AppShell
 * =========
 * Master layout wrapper that composes TopBar + SideNav + main content.
 *
 * Responsibilities:
 *   - Owns the mobile drawer open/close state
 *   - Passes drawerWidth to both TopBar (for offset) and SideNav (for width)
 *   - Wraps all page content in the correctly-padded main area
 *
 * The DRAWER_WIDTH constant is defined here — the single source of truth.
 * TopBar and SideNav receive it as a prop. No magic numbers elsewhere.
 *
 * Layout structure:
 *   <Box display="flex">       ← horizontal flex container
 *     <TopBar />               ← fixed AppBar (position: fixed, zIndex: drawer+1)
 *     <SideNav />              ← permanent or temporary Drawer
 *     <Box component="main">   ← flexible main content area
 *       <Toolbar />            ← spacer equal to TopBar height (64px)
 *       <Box p={4}>            ← page content padding
 *         {children}
 *       </Box>
 *     </Box>
 *   </Box>
 */

import { Box, Toolbar } from '@mui/material'
import { useState } from 'react'
import TopBar from './TopBar'
import SideNav from './SideNav'

const DRAWER_WIDTH = 256 // px — sidebar width on desktop

interface AppShellProps {
  children: React.ReactNode
  environment?: string
}

export default function AppShell({ children, environment }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Fixed top bar */}
      <TopBar
        drawerWidth={DRAWER_WIDTH}
        onMenuClick={() => setMobileOpen((prev) => !prev)}
        environment={environment}
      />

      {/* Sidebar navigation */}
      <SideNav
        drawerWidth={DRAWER_WIDTH}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      {/* Main content area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minHeight: '100vh',
          backgroundColor: 'background.default',
          // On desktop, the fixed sidebar takes up DRAWER_WIDTH
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          // Ensure content doesn't overflow under the sidebar on mobile
          overflow: 'hidden',
        }}
      >
        {/* Spacer — pushes content below the fixed TopBar */}
        <Toolbar />

        {/* Page content */}
        <Box
          sx={{
            p: { xs: 2.5, sm: 3, md: 4 },
            maxWidth: 1400,
            mx: 'auto',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  )
}
