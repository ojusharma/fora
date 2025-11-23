"use client"

import React, { useMemo, useState, useEffect } from 'react'
import { RealtimeChat } from '@/components/realtime-chat'
import { Button } from '@/components/ui/button'
import type { ChatMessage } from '@/hooks/use-realtime-chat'

type Listing = {
  id: string
  name?: string
  assignee_display_name?: string | null
}

export default function ChatsApp({ myListings = [], assignedListings = [], currentUid, currentDisplayName, initialListingId = null }: { myListings?: Listing[]; assignedListings?: Listing[]; currentUid: string; currentDisplayName: string; initialListingId?: string | null }) {
  const [tab, setTab] = useState<'assigned' | 'mine'>('assigned')
  const initial = initialListingId ?? (assignedListings.length > 0 ? String(assignedListings[0].id) : (myListings.length > 0 ? String(myListings[0].id) : null))
  const [selectedId, setSelectedId] = useState<string | null>(initial)

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loadingMessages, setLoadingMessages] = useState(false)

  const displayedListings = tab === 'assigned' ? assignedListings : myListings

  useEffect(() => {
    // when tab changes, default-select the first item from that tab
    if (displayedListings && displayedListings.length > 0) {
      setSelectedId(String(displayedListings[0].id))
    } else {
      setSelectedId(null)
    }
  }, [tab, assignedListings, myListings])

  const items = useMemo(
    () =>
      (displayedListings || []).map((l) => ({
        id: String(l.id),
        name: l.name ?? `Listing ${String(l.id).slice(0, 8)}`,
        subtitle: (l as any).assignee_display_name ?? 'Unassigned',
      })),
    [displayedListings]
  )

  useEffect(() => {
    let mounted = true
    async function loadMessages(listingId: string) {
      setLoadingMessages(true)
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
        const res = await fetch(`${baseUrl}/api/v1/chats/${encodeURIComponent(listingId)}/messages`)
        if (!res.ok) {
          console.error('Failed to load messages for listing', listingId, res.status)
          if (mounted) setMessages([])
          return
        }
        const data = await res.json()
        if (!mounted) return
        const adapted: ChatMessage[] = (data || []).map((m: any) => ({
          id: String(m.id),
          content: m.content,
          user: { name: m.sender_display_name ?? m.sender_uid ?? 'system' },
          createdAt: m.created_at,
        }))
        setMessages(adapted)
      } catch (err) {
        console.error('Error loading messages', err)
        if (mounted) setMessages([])
      } finally {
        if (mounted) setLoadingMessages(false)
      }
    }

    if (selectedId) {
      loadMessages(selectedId)
    } else {
      setMessages([])
    }

    return () => {
      mounted = false
    }
  }, [selectedId])

  return (
    <div className="h-full grid grid-cols-3 gap-4">
      <aside className="col-span-1 border rounded p-2 overflow-auto">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold">Listings</h3>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              className={`${tab === 'mine' ? 'bg-accent/10' : ''} rounded-md px-2 py-1 text-sm`}
              onClick={() => setTab('mine')}
            >
              <span className="mr-2">My listings</span>
              <span className="inline-flex items-center justify-center rounded-full bg-muted px-2 py-0.5 text-xs">{myListings?.length ?? 0}</span>
            </Button>

            <Button
              size="sm"
              variant="ghost"
              className={`${tab === 'assigned' ? 'bg-accent/10' : ''} rounded-md px-2 py-1 text-sm`}
              onClick={() => setTab('assigned')}
            >
              <span className="mr-2">Assigned</span>
              <span className="inline-flex items-center justify-center rounded-full bg-muted px-2 py-0.5 text-xs">{assignedListings?.length ?? 0}</span>
            </Button>
          </div>
        </div>
        <div className="space-y-2">
          {items.map((it) => (
            <div key={it.id} className={`p-2 rounded hover:bg-accent cursor-pointer ${selectedId === it.id ? 'bg-accent/50' : ''}`} onClick={() => setSelectedId(it.id)}>
              <div className="text-sm font-medium">{it.name}</div>
              <div className="text-xs text-muted-foreground">{it.subtitle}</div>
            </div>
          ))}
        </div>
      </aside>
      <section className="col-span-2 border rounded p-2 flex flex-col h-full">
        {selectedId ? (
          <div className="flex-1 flex flex-col">
            <div className="mb-2 border-b pb-2 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Button size="sm" variant="ghost" onClick={() => setSelectedId(null)}>Back</Button>
                <div className="text-lg font-semibold">
                  {items.find((it) => it.id === selectedId)?.name ?? `Listing ${String(selectedId).slice(0, 8)}`}
                </div>
              </div>
              <div className="text-xs text-muted-foreground">You: {currentDisplayName}</div>
            </div>
            <div className="flex-1 min-h-0">
              <RealtimeChat roomName={`listing-${selectedId}`} username={currentDisplayName} currentUserId={currentUid} messages={messages} />
            </div>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">Select a listing to start chatting.</div>
        )}
      </section>
    </div>
  )
}
