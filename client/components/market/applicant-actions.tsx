"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

type Props = {
  listingId: string;
  applicantUid: string;
  currentUserId: string | null;
  initialStatus?: string | null;
};

export default function ApplicantActions({ listingId, applicantUid, currentUserId, initialStatus }: Props) {
  const [status, setStatus] = useState<string | null>(initialStatus ?? null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  if (!currentUserId) return null;

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  async function updateStatus(newStatus: "shortlisted" | "rejected") {
    setLoading(true);
    try {
      const endpoint = newStatus === "shortlisted" ? "shortlist" : "reject";
      const res = await fetch(
        `${baseUrl}/api/v1/listings/${encodeURIComponent(listingId)}/applicants/${encodeURIComponent(applicantUid)}/${endpoint}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? `Failed to set status ${newStatus}`);
      }
      setStatus(newStatus);
      if (newStatus === "shortlisted") {
        // navigate to chats and open the listing's chat
        try {
          router.push(`/chats?listing=${encodeURIComponent(listingId)}`)
        } catch (e) {
          // ignore navigation errors
        }
      }
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex gap-2 pt-2">
      <button
        className="px-3 py-1 rounded bg-emerald-600 text-white text-sm"
        onClick={() => updateStatus("shortlisted")}
        disabled={loading || status === "shortlisted"}
      >
        {status === "shortlisted" ? "Shortlisted" : loading ? "Working..." : "Shortlist"}
      </button>

      <Dialog>
        <DialogTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={loading || status === "rejected"}
          >
            {status === "rejected" ? "Rejected" : "Reject"}
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject applicant?</DialogTitle>
            <DialogDescription>
              This action will mark the applicant as rejected. This cannot be undone from the UI.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" size="sm">
                Cancel
              </Button>
            </DialogClose>
            <DialogClose asChild>
              <Button
                size="sm"
                className="ml-2"
                onClick={() => {
                  updateStatus("rejected");
                }}
                disabled={loading || status === "rejected"}
              >
                {status === "rejected" ? "Rejected" : loading ? "Working..." : "Confirm Reject"}
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
