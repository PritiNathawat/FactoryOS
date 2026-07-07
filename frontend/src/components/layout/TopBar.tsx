'use client'

/**
 * TopBar
 * =======
 * Fixed application bar at the top of every page.
 *
 * Desktop: Right-side only (logo lives in the persistent sidebar)
 * Mobile:  Hamburger menu + FactoryOS wordmark + right content
 *
 * The environment badge ("DEVELOPMENT") is shown in non-production environments
 * to make it immediately obvious which environment is being used.
 * This is a production safety feature — prevents acting on staging data.
 */

import {
  AppBar,
  Box,
  Chip,
  IconButton,
  Toolbar,
  Typography,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import PrecisionManufacturingIcon from '@mui/icons-material/PrecisionManufacturing'

interface TopBarProps {
  drawerWidth: number
  onMenuClick: () => void
  environment?: string
}

export default function TopBar({
  drawerWidth,
  onMenuClick,
  environment = 'development',
}: TopBarProps) {
  const isProduction = environment === 'production'

  return (
    <AppBar
      position="fixed"
      sx={{
        // On desktop, offset the AppBar to sit beside the persistent drawer.
        // On mobile, span the full width.
        zIndex: (theme) => theme.zIndex.drawer + 1,
        width: { md: `calc(100% - ${drawerWidth}px)` },
        ml: { md: `${drawerWidth}px` },
      }}
    >
      <Toolbar>
        {/* Hamburger — mobile only */}
        <IconButton
          color="inherit"
          aria-label="Open navigation menu"
          edge="start"
          onClick={onMenuClick}
          sx={{ mr: 1, display: { md: 'none' } }}
        >
          <MenuIcon sx={{ color: 'text.secondary' }} />
        </IconButton>

        {/* Logo + wordmark — mobile only (desktop shows this in SideNav) */}
        <Box
          sx={{
            display: { xs: 'flex', md: 'none' },
            alignItems: 'center',
            gap: 1,
          }}
        >
          <PrecisionManufacturingIcon sx={{ color: 'primary.main', fontSize: 20 }} />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              color: 'text.primary',
              fontSize: '0.9375rem',
              letterSpacing: '-0.2px',
            }}
          >
            FactoryOS
          </Typography>
        </Box>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Environment badge — hidden in production */}
        {!isProduction && (
          <Chip
            label={environment.toUpperCase()}
            size="small"
            sx={{
              backgroundColor: '#fef3e2',
              color: '#b06000',
              fontWeight: 700,
              fontSize: '0.625rem',
              height: 20,
              letterSpacing: '0.07em',
              border: '1px solid rgba(176, 96, 0, 0.2)',
              '& .MuiChip-label': { px: '8px' },
            }}
          />
        )}
      </Toolbar>
    </AppBar>
  )
}
