/**
 * Decision Center Page — /decisions
 *
 * Server component: exports page metadata.
 * All interactive logic lives in DecisionView (client component).
 */
import type { Metadata } from 'next'
import DecisionView from './DecisionView'

export const metadata: Metadata = {
  title: 'Decision Center',
  description: 'Review AI-generated recovery plans and approve the best course of action.',
}

export default function DecisionsPage() {
  return <DecisionView />
}
