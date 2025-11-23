"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { MessageSquare, AlertCircle, Star } from "lucide-react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

interface Listing {
  id: string;
  name: string;
  description?: string;
  compensation?: number;
  deadline?: string;
  location_address?: string;
  status: string;
  assignee_uid?: string;
  created_at: string;
}

interface AssigneeProfile {
  uid: string;
  display_name?: string;
  phone?: string;
}

export function PostedTasksInProgress() {
  const [tasks, setTasks] = useState<Listing[]>([]);
  const [assigneeProfiles, setAssigneeProfiles] = useState<Record<string, AssigneeProfile>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [showRatingDialog, setShowRatingDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Listing | null>(null);
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);

  useEffect(() => {
    async function loadPostedTasks() {
      try {
        const supabase = createClient();
        const { data, error } = await supabase.auth.getUser();

        if (error || !data?.user) {
          setIsLoading(false);
          return;
        }

        const uid = data.user.id;
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

        // Fetch listings posted by user with status "in_progress" and "pending_confirmation"
        const [inProgressRes, pendingRes] = await Promise.all([
          fetch(`${baseUrl}/api/v1/listings?poster_uid=${uid}&status=in_progress`, { cache: "no-store" }),
          fetch(`${baseUrl}/api/v1/listings?poster_uid=${uid}&status=pending_confirmation`, { cache: "no-store" })
        ]);

        const inProgress = inProgressRes.ok ? await inProgressRes.json() : [];
        const pending = pendingRes.ok ? await pendingRes.json() : [];
        const allTasks = [...inProgress, ...pending];

        setTasks(allTasks);

        // Fetch assignee profiles
        const assigneeIds = allTasks
          .map((listing: Listing) => listing.assignee_uid)
          .filter((id): id is string => !!id);

        if (assigneeIds.length > 0) {
          const uniqueIds = [...new Set(assigneeIds)];
          const profilePromises = uniqueIds.map((assigneeId: string) =>
            fetch(`${baseUrl}/api/v1/users/${assigneeId}`, { cache: "no-store" })
          );

          const profileResponses = await Promise.all(profilePromises);
          const profiles = await Promise.all(
            profileResponses.map((res) => (res.ok ? res.json() : null))
          );

          const profileMap: Record<string, AssigneeProfile> = {};
          profiles.forEach((profile, index) => {
            if (profile) {
              profileMap[uniqueIds[index]] = profile;
            }
          });

          setAssigneeProfiles(profileMap);
        }
      } catch (err) {
        console.error("Failed to load posted tasks:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadPostedTasks();
  }, []);

  const handleReviewClick = (task: Listing) => {
    setSelectedTask(task);
    setShowReviewDialog(true);
  };

  const handleReviewResponse = async (isComplete: boolean) => {
    if (!selectedTask) return;

    setShowReviewDialog(false);

    if (isComplete) {
      // Show rating dialog
      setShowRatingDialog(true);
    } else {
      // Task not complete - revert to in_progress
      try {
        const supabase = createClient();
        const { data: userData } = await supabase.auth.getUser();
        if (!userData?.user) return;

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        const response = await fetch(
          `${baseUrl}/api/v1/listings/${selectedTask.id}?user_uid=${userData.user.id}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: "in_progress" })
          }
        );

        if (response.ok) {
          // Update local state
          setTasks(prev => prev.map(t => 
            t.id === selectedTask.id ? { ...t, status: "in_progress" } : t
          ));
        } else {
          const errorData = await response.json().catch(() => ({}));
          console.error("Failed to revert status:", errorData);
        }
      } catch (err) {
        console.error("Failed to update task status:", err);
      }

      setSelectedTask(null);
    }
  };

const handleRatingSubmit = async () => {
    if (!selectedTask || !selectedTask.assignee_uid || rating === 0) {
      console.log("Rating submit validation failed:", { 
        hasTask: !!selectedTask, 
        hasAssignee: !!selectedTask?.assignee_uid, 
        rating 
      });
      return;
    }

    console.log("Starting rating submission for task:", selectedTask.id);

    try {
      const supabase = createClient();
      const { data: userData } = await supabase.auth.getUser();
      if (!userData?.user) {
        console.error("No user data found");
        return;
      }

      console.log("User authenticated:", userData.user.id);

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      
      // Submit rating for assignee
      console.log("Submitting rating...", { 
        listing_id: selectedTask.id, 
        assignee_uid: selectedTask.assignee_uid, 
        rating 
      });

      const ratingResponse = await fetch(
        `${baseUrl}/api/v1/ratings/assignee`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            listing_id: selectedTask.id,
            assignee_uid: selectedTask.assignee_uid,
            rating: rating
          })
        }
      );

      console.log("Rating response status:", ratingResponse.status);

      if (ratingResponse.ok) {
        const ratingData = await ratingResponse.json();
        console.log("Rating submitted successfully:", ratingData);
      } else {
        const ratingError = await ratingResponse.json().catch(() => ({}));
        console.error("Failed to submit rating:", ratingError);
      }

      // Confirm completion - update listing status to completed
      console.log("Confirming completion...");
      const response = await fetch(
        `${baseUrl}/api/v1/listings/${selectedTask.id}/confirm-completion?user_uid=${userData.user.id}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        }
      );

      console.log("Confirm completion response status:", response.status);

      if (response.ok) {
        const confirmData = await response.json();
        console.log("Completion confirmed successfully:", confirmData);
        // Remove from local state
        setTasks(prev => prev.filter(t => t.id !== selectedTask.id));
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error("Failed to confirm completion:", errorData);
      }
    } catch (err) {
      console.error("Failed to complete task:", err);
    }

    setShowRatingDialog(false);
    setSelectedTask(null);
    setRating(0);
  };

  const handleCancelRating = () => {
    setShowRatingDialog(false);
    setSelectedTask(null);
    setRating(0);
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-muted rounded w-1/4"></div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-40 bg-muted rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return null;
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold tracking-tight">Posted Tasks in Progress</h2>
        <Badge variant="secondary" className="text-xs">
          {tasks.length} {tasks.length === 1 ? "task" : "tasks"}
        </Badge>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tasks.map((task) => {
          const assignee = task.assignee_uid ? assigneeProfiles[task.assignee_uid] : null;
          const assigneeName = assignee?.display_name || assignee?.phone || "Unassigned";
          const isPendingConfirmation = task.status === "pending_confirmation";

          return (
            <Card key={task.id} className="flex flex-col">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg line-clamp-1">
                    {task.name}
                  </CardTitle>
                  <Badge variant={isPendingConfirmation ? "default" : "outline"} className="shrink-0 text-xs">
                    {isPendingConfirmation ? "Pending Review" : "In Progress"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-4">
                {isPendingConfirmation && (
                  <div className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-md">
                    <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                        {assigneeName} marked as complete
                      </p>
                      <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                        Please review and confirm completion
                      </p>
                    </div>
                  </div>
                )}

                <p className="text-sm text-muted-foreground line-clamp-2">
                  {task.description || "No description available"}
                </p>

                {task.location_address && (
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    📍 {task.location_address}
                  </p>
                )}

                {task.assignee_uid && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Assigned to:</span>
                    <span className="text-xs font-semibold">{assigneeName}</span>
                  </div>
                )}

                {task.deadline && (
                  <p className="text-xs text-muted-foreground">
                    ⏰ Due: {new Date(task.deadline).toLocaleDateString()}
                  </p>
                )}

                <div className="flex gap-2 mt-auto pt-2">
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <Link href={`/market/${task.id}`}>
                      View Details
                    </Link>
                  </Button>
                  <Button
                    asChild
                    size="sm"
                    className="flex items-center gap-1"
                  >
                    <Link href="/chats">
                      <MessageSquare className="h-4 w-4" />
                      Chat
                    </Link>
                  </Button>
                </div>

                {isPendingConfirmation && (
                  <Button
                    variant="default"
                    size="sm"
                    className="w-full mt-2"
                    onClick={() => handleReviewClick(task)}
                  >
                    Review Completion
                  </Button>
                )}

                <p className="text-xs text-muted-foreground mt-2">
                  Posted {new Date(task.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Review Dialog */}
      <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review Task Completion</DialogTitle>
            <DialogDescription>
              Has the assignee completed the task successfully?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => handleReviewResponse(false)}>
              No
            </Button>
            <Button onClick={() => handleReviewResponse(true)}>
              Yes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rating Dialog */}
      <Dialog open={showRatingDialog} onOpenChange={setShowRatingDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rate the Assignee</DialogTitle>
            <DialogDescription>
              How would you rate {selectedTask && selectedTask.assignee_uid ? assigneeProfiles[selectedTask.assignee_uid]?.display_name || assigneeProfiles[selectedTask.assignee_uid]?.phone || "the assignee" : "the assignee"}'s work?
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm font-medium mb-3">Rate the assignee:</p>
            <div className="flex gap-2 justify-center">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  onMouseEnter={() => setHoveredRating(star)}
                  onMouseLeave={() => setHoveredRating(0)}
                  className="focus:outline-none transition-transform hover:scale-110"
                >
                  <Star
                    className={`h-8 w-8 ${
                      star <= (hoveredRating || rating)
                        ? "fill-yellow-400 text-yellow-400"
                        : "text-gray-300"
                    }`}
                  />
                </button>
              ))}
            </div>
            {rating > 0 && (
              <p className="text-center text-sm text-muted-foreground mt-2">
                {rating} {rating === 1 ? "star" : "stars"}
              </p>
            )}
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={handleCancelRating}>
              Cancel
            </Button>
            <Button onClick={handleRatingSubmit} disabled={rating === 0}>
              Submit Rating
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
