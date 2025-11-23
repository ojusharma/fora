"use client";

import React, { useState } from "react";
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
  currentUserId: string;
};

export default function WithdrawButton({ listingId, currentUserId }: Props) {
  const [loading, setLoading] = useState(false);

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  async function handleWithdraw() {
    setLoading(true);
    try {
      const res = await fetch(
        `${baseUrl}/api/v1/listings/${encodeURIComponent(listingId)}/applicants/${encodeURIComponent(currentUserId)}/withdraw`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Failed to withdraw application");
      }
      // Refresh the page to show updated status
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" disabled={loading}>
          Withdraw
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Withdraw application?</DialogTitle>
          <DialogDescription>Withdrawing will mark your application as withdrawn. You can re-apply later.</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" size="sm">Cancel</Button>
          </DialogClose>
          <DialogClose asChild>
            <Button size="sm" onClick={handleWithdraw} disabled={loading}>
              {loading ? "Withdrawing..." : "Confirm Withdraw"}
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
