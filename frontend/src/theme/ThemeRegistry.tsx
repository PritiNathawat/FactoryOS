'use client'

/**
 * FactoryOS Theme Registry
 * =========================
 * Solves the MUI + Next.js App Router SSR styling problem.
 *
 * Problem: MUI uses emotion for CSS-in-JS. In the App Router,
 * server-rendered HTML is sent before client JS executes. Without this
 * setup, MUI styles arrive late and cause a Flash of Unstyled Content (FOUC).
 *
 * Solution: Intercept the emotion cache's `insert` calls during SSR,
 * collect the generated style strings, and inject them into the server HTML
 * via `useServerInsertedHTML`. The client then hydrates with matching styles.
 *
 * Reference: https://mui.com/material-ui/integrations/nextjs/
 */

import createCache from '@emotion/cache'
import { useServerInsertedHTML } from 'next/navigation'
import { CacheProvider } from '@emotion/react'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { useState, type ReactNode } from 'react'
import theme from './theme'

interface ThemeRegistryProps {
  children: ReactNode
}

export default function ThemeRegistry({ children }: ThemeRegistryProps) {
  const [{ cache, flush }] = useState(() => {
    const cache = createCache({ key: 'mui' })
    cache.compat = true

    // Intercept cache.insert to track which styles have been inserted during SSR.
    // eslint-disable-next-line @typescript-eslint/unbound-method
    const prevInsert = cache.insert.bind(cache)
    let inserted: string[] = []

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    cache.insert = (...args: Parameters<typeof prevInsert>) => {
      const serialized = args[1]
      if (cache.inserted[serialized.name] === undefined) {
        inserted.push(serialized.name)
      }
      return prevInsert(...args)
    }

    /** Drain the collected style names and return them. */
    const flush = () => {
      const prev = inserted
      inserted = []
      return prev
    }

    return { cache, flush }
  })

  // Inject collected styles into the <head> during server rendering.
  // This runs once per response and provides all emotion styles upfront.
  useServerInsertedHTML(() => {
    const names = flush()
    if (names.length === 0) return null

    let styles = ''
    for (const name of names) {
      styles += cache.inserted[name]
    }

    return (
      <style
        key={cache.key}
        data-emotion={`${cache.key} ${names.join(' ')}`}
        dangerouslySetInnerHTML={{ __html: styles }}
      />
    )
  })

  return (
    <CacheProvider value={cache}>
      <ThemeProvider theme={theme}>
        {/* CssBaseline applies the global CSS reset and body defaults from our theme */}
        <CssBaseline />
        {children}
      </ThemeProvider>
    </CacheProvider>
  )
}
