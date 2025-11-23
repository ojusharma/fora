"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";

interface DeleteListingButtonProps {
  listingId: string;
  listingName: string;
  currentUserId: string;
}

export function DeleteListingButton({
  listingId,
  listingName,
  currentUserId,
}: DeleteListingButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleDelete = async () => {
    setError("");
    setIsDeleting(true);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      
      const response = await fetch(
        `${baseUrl}/api/v1/listings/${listingId}?user_uid=${currentUserId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete listing");
      }

      // Success - redirect to marketplace
      router.push("/market");
    } catch (err) {
      console.error("Error deleting listing:", err);
      setError(err instanceof Error ? err.message : "Failed to delete listing");
      setIsDeleting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="destructive" size="sm">
          <Trash2 className="h-4 w-4 mr-2" />
          Delete Listing
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Listing</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{listingName}"? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded p-2">
            {error}
          </div>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => setIsOpen(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
