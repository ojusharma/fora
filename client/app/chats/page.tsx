import { AuthButton } from '@/components/auth-button'
import { ThemeSwitcher } from '@/components/theme-switcher'
import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import { notFound, redirect } from 'next/navigation'
import { Suspense } from 'react'
import ChatsApp from '@/components/chats/chats-app'
import { NotificationBell } from '@/components/notification-bell'

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

  // Attach assignee display names to listings (batch fetch user profiles)
  const allListings = [...posterListings, ...assigneeListings]
  const assigneeUids = Array.from(new Set(allListings.map((l: any) => l.assignee_uid).filter(Boolean)))
  const assigneeNameByUid: Record<string, string> = {}
  if (assigneeUids.length > 0) {
    try {
      const profilePromises = assigneeUids.map((uid) => fetch(`${baseUrl}/api/v1/users/${encodeURIComponent(uid)}`, { cache: 'no-store' }).then(async (r) => (r.ok ? r.json() : null)))
      const profiles = await Promise.all(profilePromises)
      profiles.forEach((p) => {
        if (!p) return
        const uid = p.uid ?? p.id
        if (!uid) return
        assigneeNameByUid[String(uid)] = p.display_name ?? p.full_name ?? p.phone ?? String(uid).slice(0, 8)
      })
    } catch (err) {
      // ignore
    }
  }

  // attach assignee_display_name to listings
  for (const l of allListings) {
    const au = l.assignee_uid ?? l.assignee ?? null
    l.assignee_display_name = au ? assigneeNameByUid[String(au)] ?? String(au).slice(0, 8) : null
  }

  const myListings = posterListings
  const assignedListings = assigneeListings

  const params = await searchParams;

  const initialListingId = params?.listing ?? null

  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-5xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href={'/'}>fora</Link>
              <Link href={'/market'}>marketplace</Link>
              <Link href={'/map'}>map</Link>
              <Link href={'/chats'}>my chats</Link>
            </div>
            <div className="flex items-center gap-4">
  <Suspense>
    <NotificationBell />
  </Suspense>

  <AuthButton />
</div>
          </div>
        </nav>

        <div className="flex-1 flex flex-col gap-20 max-w-5xl p-5">
          <div className="w-full max-w-6xl mx-auto h-[70vh]">
            {/* ChatsApp is a client component that renders the two-column UI */}
            <ChatsApp myListings={myListings} assignedListings={assignedListings} currentUid={String(currentUid)} currentDisplayName={displayName} initialListingId={initialListingId} />
          </div>
        </div>

        <footer className="w-full flex items-center justify-center border-t mx-auto text-center text-xs gap-8 py-16">
          <p>
            Powered by{' '}
            <a
              href="https://supabase.com/?utm_source=create-next-app&utm_medium=template&utm_term=nextjs"
              target="_blank"
              className="font-bold hover:underline"
              rel="noreferrer"
            >
              Supabase
            </a>
          </p>
          <ThemeSwitcher />
        </footer>
      </div>
    </main>
  )
}
