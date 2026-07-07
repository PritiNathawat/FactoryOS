import type { NextConfig } from 'next'

/**
 * FactoryOS — Next.js Configuration
 *
 * The /api/* rewrite is the key architectural decision here.
 * All frontend requests to /api/* are proxied server-side to the FastAPI backend.
 *
 * Benefits:
 *   - Eliminates CORS entirely in development
 *   - Frontend code uses relative URLs (/api/v1/health) — no hardcoded backend addresses
 *   - Mirrors production where a load balancer handles routing
 *   - Switching environments only requires changing BACKEND_INTERNAL_URL
 */

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL ?? 'http://localhost:8000'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
