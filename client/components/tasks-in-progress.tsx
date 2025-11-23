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
import { MessageSquare, CheckCircle, Star } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

interface Task {
  listing_id: string;
  status: string;
  applied_at: string;
  listing?: {
    id: string;
    name: string;
    description: string;
    compensation?: number;
    deadline?: string;
    location_address?: string;
    poster_uid?: string;
  };
}

export function TasksInProgress() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showThankYouDialog, setShowThankYouDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [posterName, setPosterName] = useState<string>("the poster");
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);

  useEffect(() => {
    async function loadShortlistedTasks() {
      try {
        const supabase = createClient();
        const { data, error } = await supabase.auth.getUser();

        if (error || !data?.user) {
          setIsLoading(false);
          return;
        }

        const uid = data.user.id;
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

        // Fetch listings where user is assignee with status "in_progress" and "pending_confirmation"
        const [inProgressRes, pendingRes] = await Promise.all([
          fetch(`${baseUrl}/api/v1/listings?assignee_uid=${uid}&status=in_progress`, { cache: "no-store" }),
          fetch(`${baseUrl}/api/v1/listings?assignee_uid=${uid}&status=pending_confirmation`, { cache: "no-store" })
        ]);

        const inProgressListings = inProgressRes.ok ? await inProgressRes.json() : [];
        const pendingListings = pendingRes.ok ? await pendingRes.json() : [];
        const allListings = [...inProgressListings, ...pendingListings];
        
        // Convert to Task format
        const normalizedTasks = allListings.map((listing: any) => ({
          listing_id: listing.id,
          status: listing.status,
          applied_at: listing.created_at,
          listing: listing
        }));
        
        setTasks(normalizedTasks);
      } catch (err) {
        console.error("Failed to load tasks in progress:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadShortlistedTasks();
  }, []);

  const handleMarkComplete = async (task: Task) => {
    setSelectedTask(task);
    
    // Fetch poster's name
    if (task.listing?.poster_uid) {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/v1/users/${task.listing.poster_uid}`, {
          cache: "no-store"
        });
        
        if (response.ok) {
          const profile = await response.json();
          setPosterName(profile.display_name || profile.phone || "the poster");
        }
      } catch (err) {
        console.error("Failed to fetch poster name:", err);
        setPosterName("the poster");
      }
    }
    
    setShowConfirmDialog(true);
  };

  const handleConfirmYes = () => {
    setShowConfirmDialog(false);
    setShowThankYouDialog(true);
  };

  const handleConfirmNo = () => {
    setShowConfirmDialog(false);
    setSelectedTask(null);
  };

  const handleRatingSubmit = async () => {
    if (!selectedTask?.listing_id) return;

    try {
      const supabase = createClient();
      const { data: userData } = await supabase.auth.getUser();
      if (!userData?.user) return;

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      
      // Submit rating to backend 
      if (rating > 0) {
        const ratingResponse = await fetch(
          `${baseUrl}/api/v1/ratings/poster`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              listing_id: selectedTask.listing_id,
              applicant_uid: userData.user.id,
              rating: rating
            })
          }
        );

        if (ratingResponse.ok) {
          console.log("Rating submitted successfully");
        }
      }
      
      // Update applicant status to pending_confirmation
      const statusResponse = await fetch(
        `${baseUrl}/api/v1/listings/${selectedTask.listing_id}/applicants/${userData.user.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "pending_confirmation" })
        }
      );

      if (statusResponse.ok) {
        // Update the task in the local state
        setTasks(prev => prev.map(t => 
          t.listing_id === selectedTask.listing_id 
            ? { ...t, status: "pending_confirmation" }
            : t
        ));
        
        // Navigate to profile page
        router.push("/profile");
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    }
    
    setShowThankYouDialog(false);
    setSelectedTask(null);
    setRating(0);
  };

  const handleExit = () => {
    setShowThankYouDialog(false);
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
        <h2 className="text-2xl font-semibold tracking-tight">Tasks in Progress</h2>
        <Badge variant="secondary" className="text-xs">
          {tasks.length} {tasks.length === 1 ? "task" : "tasks"}
        </Badge>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tasks.map((task) => {
          const listing = task.listing;
          if (!listing) return null;
          
          const isPendingConfirmation = task.status === "pending_confirmation";

          return (
            <Card key={task.listing_id} className={`flex flex-col ${isPendingConfirmation ? 'opacity-50' : ''}`}>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg line-clamp-1">
                    {listing.name}
                  </CardTitle>
                  <Badge variant={isPendingConfirmation ? "secondary" : "outline"} className="shrink-0 text-xs">
                    {isPendingConfirmation ? "Pending Confirmation" : "Shortlisted"}
                  </Badge>
                </div>
                {listing.compensation && (
                  <CardDescription className="font-medium">
                    ${listing.compensation.toLocaleString()}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-4">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {listing.description || "No description available"}
                </p>
                
                {listing.deadline && (
                  <p className="text-xs text-muted-foreground">
                    ⏰ Due: {new Date(listing.deadline).toLocaleDateString()}
                  </p>
                )}

                {listing.location_address && (
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    📍 {listing.location_address}
                  </p>
                )}

                <div className="flex gap-2 mt-auto pt-2">
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <Link href={`/market/${listing.id}`}>
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

                {isPendingConfirmation ? (
                  <div className="w-full p-3 mt-2 bg-muted rounded-md text-center">
                    <p className="text-sm font-medium text-muted-foreground">
                      Waiting for poster confirmation
                    </p>
                  </div>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    className="w-full flex items-center gap-2 mt-2"
                    onClick={() => handleMarkComplete(task)}
                  >
                    <CheckCircle className="h-4 w-4" />
                    Mark as Complete
                  </Button>
                )}

                <p className="text-xs text-muted-foreground mt-2">
                  Applied {new Date(task.applied_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Mark Task as Complete?</DialogTitle>
            <DialogDescription>
              Are you sure you want to mark this task as complete?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={handleConfirmNo}>
              No
            </Button>
            <Button onClick={handleConfirmYes}>
              Yes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showThankYouDialog} onOpenChange={setShowThankYouDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thank You!</DialogTitle>
            <DialogDescription>
              The poster will confirm completion. Please rate your experience working with {posterName}.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm font-medium mb-3">Rate the poster:</p>
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
            <Button variant="outline" onClick={handleExit}>
              Exit
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
