import { createClient } from '@/lib/supabase/server'
import { notFound, redirect } from 'next/navigation'
import ChatsApp from '@/components/chats/chats-app'

export default async function Page({ searchParams }: { searchParams?: { listing?: string } }) {
  const supabase = await createClient()
  const { data, error } = await supabase.auth.getClaims()

  if (error || !data?.claims) {
    redirect('/auth/login')
  }

  const currentUid = data?.claims?.sub ?? null
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

  if (!currentUid) return notFound()

  // Fetch user profile for display name
  const profileRes = await fetch(`${baseUrl}/api/v1/users/${encodeURIComponent(currentUid)}`, { cache: 'no-store' })
  const profile = profileRes.ok ? await profileRes.json() : null
  const displayName = profile?.display_name ?? profile?.full_name ?? String(currentUid).slice(0, 8)

  // Fetch listings where user is poster
  const posterRes = await fetch(`${baseUrl}/api/v1/listings?poster_uid=${encodeURIComponent(currentUid)}`, { cache: 'no-store' })
  const posterListings = posterRes.ok ? (await posterRes.json()) : []

  // Fetch listings where user is assignee
  const assigneeRes = await fetch(`${baseUrl}/api/v1/listings?assignee_uid=${encodeURIComponent(currentUid)}`, { cache: 'no-store' })
  const assigneeListings = assigneeRes.ok ? (await assigneeRes.json()) : []

  // Merge unique listings by id
  const all = [...posterListings, ...assigneeListings]
  const map = new Map<string, any>()
  for (const l of all) {
    map.set(String(l.id), l)
  }
  const listings = Array.from(map.values())

  const initialListingId = searchParams?.listing ?? null

  return (
    <div className="w-full max-w-6xl mx-auto h-[70vh]">
      {/* ChatsApp is a client component that renders the two-column UI */}
      <ChatsApp listings={listings} currentUid={String(currentUid)} currentDisplayName={displayName} initialListingId={initialListingId} />
    </div>
  )
}
