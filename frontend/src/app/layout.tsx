/**
 * FactoryOS — Root Layout
 * ========================
 * This is a Next.js App Router Server Component.
 *
 * Responsibilities:
 *   1. Load the Inter font via next/font/google (optimized, no CLS)
 *   2. Set the CSS variable --font-inter on the <html> element
 *      (consumed by the MUI theme's fontFamily definition)
 *   3. Wrap all pages in ThemeRegistry (MUI theme + SSR emotion cache)
 *   4. Wrap all pages in AppShell (persistent TopBar + SideNav)
 *   5. Export page metadata for the SEO baseline
 *
 * Why this is a server component (no 'use client'):
 *   - next/font must be used in a server component
 *   - metadata export only works in server components
 *   - ThemeRegistry and AppShell are client components — server components
 *     can import and render client components, which is correct App Router usage
 */

import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import ThemeRegistry from '@/theme/ThemeRegistry'
import AppShell from '@/components/layout/AppShell'
import './globals.css'

// ─── Font ──────────────────────────────────────────────────────
// next/font/google downloads Inter at build time, self-hosts it,
// and generates a --font-inter CSS custom property on the html element.
// No external font requests at runtime = faster LCP, no FOUT.
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  weight: ['300', '400', '500', '600', '700'],
})

// ─── Metadata ─────────────────────────────────────────────────
export const metadata: Metadata = {
  title: {
    default: 'FactoryOS — AI Manufacturing Operations',
    template: '%s | FactoryOS',
  },
  description:
    'Production-grade Multi-Agent Manufacturing Operations Platform. Powered by Google ADK, Gemini, and MCP.',
  // Internal tool — do not index in search engines
  robots: { index: false, follow: false },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

// ─── Root Layout ──────────────────────────────────────────────
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        {/*
          ThemeRegistry: provides MUI theme + SSR-safe emotion cache
          AppShell: persistent TopBar + SideNav shell around all pages
          process.env.NODE_ENV is read server-side and passed as a prop
          to the client component — this is the correct pattern
        */}
        <ThemeRegistry>
          <AppShell environment={process.env.NODE_ENV}>
            {children}
          </AppShell>
        </ThemeRegistry>
      </body>
    </html>
  )
}
