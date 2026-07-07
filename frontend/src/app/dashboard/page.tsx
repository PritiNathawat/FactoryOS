/**
 * Dashboard Page — /dashboard
 *
 * Primary page for Sprint 1. Shows the four manufacturing metric cards.
 * This is a server component — it renders client components (PageHeader, DashboardGrid)
 * which is correct App Router usage. No 'use client' needed here.
 */
import type { Metadata } from 'next'
import PageHeader from '@/components/ui/PageHeader'
import DashboardGrid from '@/components/dashboard/DashboardGrid'

export const metadata: Metadata = {
  title: 'Dashboard',
}

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Live overview of your manufacturing operations"
      />
      <DashboardGrid />
    </>
  )
}
