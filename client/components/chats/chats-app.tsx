"use client"

import React, { useMemo, useState } from 'react'
import { RealtimeChat } from '@/components/realtime-chat'
import { Button } from '@/components/ui/button'

type Listing = {
  id: string
  name?: string
}

export default function ChatsApp({ listings = [], currentUid, currentDisplayName, initialListingId = null }: { listings: Listing[]; currentUid: string; currentDisplayName: string; initialListingId?: string | null }) {
  const [selectedId, setSelectedId] = useState<string | null>(initialListingId ?? (listings.length > 0 ? String(listings[0].id) : null))

  const items = useMemo(() => listings.map((l) => ({ id: String(l.id), name: l.name ?? `Listing ${String(l.id).slice(0, 8)}` })), [listings])

  return (
    <div className="h-full grid grid-cols-3 gap-4">
      <aside className="col-span-1 border rounded p-2 overflow-auto">
        <h3 className="font-semibold mb-2">Listings</h3>
        <div className="space-y-2">
          {items.map((it) => (
            <div key={it.id} className={`p-2 rounded hover:bg-accent cursor-pointer ${selectedId === it.id ? 'bg-accent/50' : ''}`} onClick={() => setSelectedId(it.id)}>
              <div className="text-sm font-medium">{it.name}</div>
              <div className="text-xs text-muted-foreground">{it.id}</div>
            </div>
          ))}
        </div>
      </aside>
      <section className="col-span-2 border rounded p-2 flex flex-col h-full">
        {selectedId ? (
          <div className="flex-1 flex flex-col">
            <div className="mb-2 flex items-center justify-between">
              <h4 className="font-semibold">Chat for listing {selectedId}</h4>
              <div className="text-xs text-muted-foreground">You: {currentDisplayName}</div>
            </div>
            <div className="flex-1 min-h-0">
              <RealtimeChat roomName={`listing-${selectedId}`} username={currentDisplayName} currentUserId={currentUid} />
            </div>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">Select a listing to start chatting.</div>
        )}
      </section>
    </div>
  )
}
