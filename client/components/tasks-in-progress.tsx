"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, CheckCircle } from "lucide-react";
import Link from "next/link";
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
  };
}

export function TasksInProgress() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

        // Fetch user's applications with status "shortlisted"
        const response = await fetch(
          `${baseUrl}/api/v1/listings/user/${uid}/with-listings?status=shortlisted`,
          { cache: "no-store" }
        );

        console.log("Tasks in Progress API response status:", response.status);

        if (response.ok) {
          const applications = await response.json();
          console.log("Tasks in Progress data:", applications);
          
          // Filter to ensure we have the listing data
          const validTasks = applications.filter((app: any) => app.listing || app.listings);
          
          // Normalize the data structure
          const normalizedTasks = validTasks.map((app: any) => ({
            ...app,
            listing: app.listing || app.listings,
          }));
          
          console.log("Normalized tasks:", normalizedTasks);
          setTasks(normalizedTasks);
        } else {
          console.error("Failed to fetch tasks:", response.status, await response.text());
        }
      } catch (err) {
        console.error("Failed to load tasks in progress:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadShortlistedTasks();
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
        <h2 className="text-2xl font-semibold tracking-tight">Tasks in Progress</h2>
        <Badge variant="secondary" className="text-xs">
          {tasks.length} {tasks.length === 1 ? "task" : "tasks"}
        </Badge>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tasks.map((task) => {
          const listing = task.listing;
          if (!listing) return null;

          return (
            <Card key={task.listing_id} className="flex flex-col">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg line-clamp-1">
                    {listing.name}
                  </CardTitle>
                  <Badge variant="outline" className="shrink-0 text-xs">
                    Shortlisted
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
                    <Link href={`/chat/${listing.id}`}>
                      <MessageSquare className="h-4 w-4" />
                      Chat
                    </Link>
                  </Button>
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full flex items-center gap-2 mt-2"
                  onClick={() => {
                    console.log("Mark as complete:", listing.id);
                  }}
                >
                  <CheckCircle className="h-4 w-4" />
                  Mark as Complete
                </Button>

                <p className="text-xs text-muted-foreground mt-2">
                  Applied {new Date(task.applied_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
