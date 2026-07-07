/**
 * Root Route — /
 * Immediately redirects to /dashboard.
 * No user should ever see a blank root page.
 */
import { redirect } from 'next/navigation'

export default function RootPage() {
  redirect('/dashboard')
}
