/**
 * Reports Page — /reports
 *
 * Server component: exports page metadata.
 * All display logic lives in ReportsView (client component).
 */
import type { Metadata } from 'next'
import ReportsView from './ReportsView'

export const metadata: Metadata = {
  title: 'Reports',
  description: 'Incident analysis reports, agent findings, and recovery outcomes.',
}

export default function ReportsPage() {
  return <ReportsView />
}
