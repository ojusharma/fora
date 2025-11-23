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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Pencil } from "lucide-react";

interface EditListingButtonProps {
  listingId: string;
  currentName: string;
  currentDescription?: string;
  currentDeadline?: string;
  currentCompensation?: number;
  currentUserId: string;
}

export function EditListingButton({
  listingId,
  currentName,
  currentDescription,
  currentDeadline,
  currentCompensation,
  currentUserId,
}: EditListingButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState(currentName);
  const [description, setDescription] = useState(currentDescription || "");
  const [deadline, setDeadline] = useState(
    currentDeadline ? new Date(currentDeadline).toISOString().slice(0, 16) : ""
  );
  const [compensation, setCompensation] = useState(
    currentCompensation?.toString() || ""
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      
      const updateData: any = {
        name,
        description: description || null,
      };

      if (deadline) {
        updateData.deadline = new Date(deadline).toISOString();
      }

      if (compensation) {
        const compensationNum = parseFloat(compensation);
        if (!isNaN(compensationNum) && compensationNum >= 0) {
          updateData.compensation = compensationNum;
        }
      }

      const response = await fetch(
        `${baseUrl}/api/v1/listings/${listingId}?user_uid=${currentUserId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updateData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update listing");
      }

      // Success - reload the page to show updated data
      window.location.reload();
    } catch (err) {
      console.error("Error updating listing:", err);
      setError(err instanceof Error ? err.message : "Failed to update listing");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Pencil className="h-4 w-4 mr-2" />
          Edit Listing
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Edit Listing</DialogTitle>
          <DialogDescription>
            Update your listing details. Changes will be visible immediately.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Title *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter listing title"
                required
                maxLength={200}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your listing"
                className="w-full min-h-[100px] px-3 py-2 text-sm rounded-md border border-input bg-background"
                maxLength={2000}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="compensation">Credits</Label>
              <Input
                id="compensation"
                type="number"
                value={compensation}
                onChange={(e) => setCompensation(e.target.value)}
                placeholder="0"
                min="0"
                step="1"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="deadline">Deadline</Label>
              <Input
                id="deadline"
                type="datetime-local"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>

            {error && (
              <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded p-2">
                {error}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !name.trim()}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
