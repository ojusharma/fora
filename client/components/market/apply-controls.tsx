"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";

type Props = {
  listingId: string;
  posterUid?: string | null;
  currentUserId?: string | null;
};

export default function ApplyControls({ listingId, posterUid, currentUserId }: Props) {
  const [applied, setApplied] = useState(false);
  const [ignored, setIgnored] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  if (!currentUserId) {
    return null;
  }

  // don't render controls for the poster
  if (posterUid && posterUid === currentUserId) return null;

  async function handleApply() {
    setError(null);
    // Do not prompt the user for a message; always submit with no message.
    const message = null;
    setLoading(true);
    try {
      const res = await fetch(
        `${baseUrl}/api/v1/listings/${encodeURIComponent(listingId)}/apply?user_uid=${encodeURIComponent(currentUserId)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: null }),
        },
      );
      if (!res.ok) {
        let msg = "Failed to apply";
        try {
          const d = await res.json();
          if (d?.detail) msg = Array.isArray(d.detail) ? d.detail.map((x: any) => x.msg ?? String(x)).join(", ") : String(d.detail);
        } catch {}
        throw new Error(msg);
      }
      setApplied(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function handleIgnore() {
    setIgnored(true);
  }

  if (ignored) {
    return <div className="text-sm text-muted-foreground">You are not seeing this listing.</div>;
  }

  return (
    <div className="flex gap-2 items-center">
      <Button onClick={handleApply} disabled={applied || loading}>
        {applied ? "Applied" : loading ? "Applying..." : "Apply"}
      </Button>
      <Button variant="outline" onClick={handleIgnore} disabled={loading}>
        Ignore
      </Button>
      {error && <div className="text-xs text-red-500">{error}</div>}
    </div>
  );
}
