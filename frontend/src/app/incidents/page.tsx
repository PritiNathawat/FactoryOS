/**
 * Incidents Page — /incidents
 *
 * Server component: exports page metadata.
 * All interactive logic lives in IncidentView (client component).
 */
import type { Metadata } from 'next'
import IncidentView from './IncidentView'

export const metadata: Metadata = {
  title: 'Report Incident',
  description: 'Submit a manufacturing incident for AI-powered multi-agent analysis.',
}

export default function IncidentsPage() {
  return <IncidentView />
}
