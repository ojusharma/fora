"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MessageSquare } from "lucide-react";
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

        // Fetch listings posted by user with status "in_progress"
        const response = await fetch(
          `${baseUrl}/api/v1/listings?poster_uid=${uid}&status=in_progress`,
          { cache: "no-store" }
        );

        console.log("Posted Tasks API response status:", response.status);

        if (response.ok) {
          const listings = await response.json();
          console.log("Posted tasks data:", listings);
          console.log("Number of posted tasks:", listings.length);
          setTasks(listings);

          // Fetch assignee profiles
          const assigneeIds = listings
            .map((listing: Listing) => listing.assignee_uid)
            .filter((id: string | undefined) => id);

          console.log("Assignee IDs to fetch:", assigneeIds);

          if (assigneeIds.length > 0) {
            const profilePromises = assigneeIds.map((assigneeId: string) =>
              fetch(`${baseUrl}/api/v1/users/${assigneeId}`, { cache: "no-store" })
            );

            const profileResponses = await Promise.all(profilePromises);
            const profiles = await Promise.all(
              profileResponses.map((res) => (res.ok ? res.json() : null))
            );

            const profileMap: Record<string, AssigneeProfile> = {};
            profiles.forEach((profile, index) => {
              if (profile) {
                profileMap[assigneeIds[index]] = profile;
              }
            });

            setAssigneeProfiles(profileMap);
          }
        } else {
          console.error("Failed to fetch posted tasks");
        }
      } catch (err) {
        console.error("Failed to load posted tasks:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadPostedTasks();
  }, []);

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

          return (
            <Card key={task.id} className="flex flex-col">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg line-clamp-1">
                    {task.name}
                  </CardTitle>
                  <Badge variant="outline" className="shrink-0 text-xs">
                    In Progress
                  </Badge>
                </div>
                {task.compensation && (
                  <CardDescription className="font-medium text-red-600">
                    -{task.compensation.toLocaleString()} credits
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-4">
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

                <p className="text-xs text-muted-foreground mt-2">
                  Posted {new Date(task.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
