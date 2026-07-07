/**
 * FactoryOS Design System — Material UI Theme
 * =============================================
 * Google Cloud Console-inspired. Professional, clean, spacious.
 *
 * Color philosophy:
 *   Primary:    Google Blue (#1a73e8) — action, selection, active states
 *   Background: Cloud Gray (#f8f9fa) — page canvas, creates card depth
 *   Surface:    White (#ffffff)       — cards, panels, elevated content
 *   Text:       Google Dark (#202124) + Google Gray (#5f6368)
 *
 * Typography: Inter (loaded via next/font/google in layout.tsx)
 *
 * All colors are defined here. Components must NOT contain inline hex values.
 * Use theme.palette.* or MUI sx shortcuts (e.g., 'primary.main') instead.
 */

import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  // ─── Color Palette ──────────────────────────────────────────
  palette: {
    mode: 'light',
    primary: {
      main: '#1a73e8',      // Google Blue — links, buttons, active nav items
      light: '#4285f4',
      dark: '#1557b0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#5f6368',      // Google Gray — secondary actions, muted elements
      light: '#80868b',
      dark: '#3c4043',
      contrastText: '#ffffff',
    },
    error: {
      main: '#d93025',      // Google Red — critical status, destructive actions
      light: '#f28b82',
      dark: '#c5221f',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#f29900',      // Google Amber — warnings, attention required
      light: '#fdd663',
      dark: '#b06000',
      contrastText: '#ffffff',
    },
    success: {
      main: '#1e8e3e',      // Google Green — healthy status, confirmations
      light: '#81c995',
      dark: '#137333',
      contrastText: '#ffffff',
    },
    info: {
      main: '#1a73e8',      // Same as primary — informational, AI suggestions
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8f9fa',   // Very light gray — page canvas
      paper: '#ffffff',     // White — cards, drawers, dialogs
    },
    text: {
      primary: '#202124',   // Near-black — headings, primary content
      secondary: '#5f6368', // Medium gray — subtitles, metadata
      disabled: '#9aa0a6',
    },
    divider: 'rgba(0, 0, 0, 0.08)',
  },

  // ─── Typography ─────────────────────────────────────────────
  // Inter is loaded in layout.tsx via next/font/google.
  // The CSS variable --font-inter is set on the <html> element.
  typography: {
    fontFamily:
      'var(--font-inter), "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: { fontWeight: 600, fontSize: '2rem',    letterSpacing: '-0.5px',  lineHeight: 1.25 },
    h2: { fontWeight: 600, fontSize: '1.5rem',  letterSpacing: '-0.25px', lineHeight: 1.3  },
    h3: { fontWeight: 600, fontSize: '1.25rem', letterSpacing: '-0.15px', lineHeight: 1.35 },
    h4: { fontWeight: 600, fontSize: '1.125rem',letterSpacing: '-0.1px',  lineHeight: 1.4  },
    h5: { fontWeight: 600, fontSize: '1rem',    letterSpacing: '0',       lineHeight: 1.4  },
    h6: { fontWeight: 600, fontSize: '0.875rem',letterSpacing: '0',       lineHeight: 1.4  },
    body1: { fontSize: '0.875rem', lineHeight: 1.6 },
    body2: { fontSize: '0.8125rem', lineHeight: 1.6, color: '#5f6368' },
    caption: { fontSize: '0.75rem', lineHeight: 1.5, color: '#5f6368' },
    overline: {
      fontSize: '0.6875rem',
      fontWeight: 600,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      lineHeight: 1.5,
    },
    button: {
      fontWeight: 500,
      letterSpacing: '0.01em',
      textTransform: 'none', // Disable ALL CAPS default on buttons
    },
  },

  // ─── Shape ──────────────────────────────────────────────────
  shape: {
    borderRadius: 8, // Base radius — components override as needed
  },

  // ─── Spacing ────────────────────────────────────────────────
  spacing: 8, // 1 spacing unit = 8px (MUI default, explicitly stated)

  // ─── Component Overrides ────────────────────────────────────
  components: {
    // Global CSS reset and body defaults
    MuiCssBaseline: {
      styleOverrides: {
        '*, *::before, *::after': { boxSizing: 'border-box' },
        body: { backgroundColor: '#f8f9fa', color: '#202124' },
        // Remove browser default link underlines inside nav items
        a: { textDecoration: 'none', color: 'inherit' },
      },
    },

    // Cards — elevated surface with hover lift effect
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)',
          border: '1px solid rgba(0,0,0,0.06)',
          transition: 'box-shadow 0.2s ease',
          '&:hover': {
            boxShadow: '0 4px 16px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06)',
          },
        },
      },
    },

    // Buttons — no ALL CAPS, consistent padding, rounded corners
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 20px',
          fontSize: '0.875rem',
          fontWeight: 500,
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none' },
        },
        contained: {
          '&:active': { boxShadow: 'none' },
        },
      },
    },

    // Chips — compact status indicators
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 600,
          fontSize: '0.6875rem',
          height: 24,
        },
      },
    },

    // TopBar (AppBar) — white, no shadow, subtle border
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#202124',
          borderBottom: '1px solid rgba(0,0,0,0.08)',
        },
      },
    },

    // Sidebar (Drawer) — white, right border instead of shadow
    MuiDrawer: {
      styleOverrides: {
        paper: {
          border: 'none',
          borderRight: '1px solid rgba(0,0,0,0.08)',
          backgroundColor: '#ffffff',
        },
      },
    },

    // Navigation items — Google Cloud Console pill style
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 8px',
          width: 'calc(100% - 16px)',
          padding: '10px 12px',
          transition: 'background-color 0.15s ease',
          '&.Mui-selected': {
            backgroundColor: '#e8f0fe',
            color: '#1a73e8',
            '&:hover': { backgroundColor: '#d2e3fc' },
            '& .MuiListItemIcon-root': { color: '#1a73e8' },
            '& .MuiListItemText-primary': { fontWeight: 600, color: '#1a73e8' },
          },
          '&:hover:not(.Mui-selected)': { backgroundColor: '#f1f3f4' },
        },
      },
    },

    // Navigation icons
    MuiListItemIcon: {
      styleOverrides: {
        root: { minWidth: 38, color: '#5f6368' },
      },
    },

    // Navigation labels
    MuiListItemText: {
      styleOverrides: {
        primary: { fontSize: '0.875rem', fontWeight: 500 },
      },
    },

    // Toolbar height — consistent at 64px
    MuiToolbar: {
      styleOverrides: {
        root: { minHeight: '64px !important' },
      },
    },

    // Dividers — subtle
    MuiDivider: {
      styleOverrides: {
        root: { borderColor: 'rgba(0,0,0,0.08)' },
      },
    },
  },
})

export default theme
