"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { usePersonalizedFeed } from "@/hooks/use-personalized-feed";
import { TaskCardStack } from "./task-card-stack";

type RecommendedListing = {
  id: string;
  name: string;
  description?: string;
  compensation?: number;
  currency?: string;
  images?: string[];
  recommendation_score?: number;
  poster_uid?: string;
};

export function HomeRecommendations() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const supabase = createClient();

  const {
    listings,
    loading: feedLoading,
    error: feedError,
    trackClick,
  } = usePersonalizedFeed({
    limit: 6,
    excludeSeen: false,
    excludeApplied: true,
    autoFetch: isAuthenticated,
  });

    const [posterNames, setPosterNames] = useState<Record<string, string>>({});

  useEffect(() => {
    async function loadPosterNames() {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const uids = Array.from(
        new Set(listings.map((l) => l.poster_uid).filter(Boolean))
      );

      if (uids.length === 0) return;
      console.log(uids);
      const results = await Promise.all(
        uids.map((uid) =>
          fetch(`${baseUrl}/api/v1/users/${uid}`)
            .then((r) => (r.ok ? r.json() : null))
            .catch(() => null)
        )
      );

      const nameMap: Record<string, string> = {};
      results.forEach((profile) => {
        if (!profile) return;
        const uid = profile.uid ?? profile.id;
        nameMap[uid] =
          profile.display_name ??
          profile.full_name ??
          profile.phone ??
          String(uid).slice(0, 8);
      });

      setPosterNames(nameMap);
      console.log(nameMap);
    }

    loadPosterNames();
  }, [listings]);

  useEffect(() => {
    async function checkAuth() {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      setIsAuthenticated(!!user);
      setLoading(false);
    }
    checkAuth();
  }, [supabase]);

  if (loading) {
    return (
      <div className="w-full py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3"></div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-muted rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="w-full py-12 text-center space-y-4">
        <h2 className="text-2xl font-bold">Discover Opportunities</h2>
        <p className="text-muted-foreground max-w-md mx-auto">
          Sign in to get personalized recommendations powered by machine learning
        </p>
        <div className="flex gap-2 justify-center">
          <Button asChild>
            <Link href="/auth/login">Sign In</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/market">Browse Marketplace</Link>
          </Button>
        </div>
      </div>
    );
  }

  if (feedError) {
    return (
      <div className="w-full py-8 space-y-4">
        <h2 className="text-2xl font-bold">Recommended for You</h2>
        <Card>
          <CardContent className="py-8 text-center space-y-4">
            <p className="text-sm text-muted-foreground mb-2">
              Recommendations aren&apos;t available yet. This happens when:
            </p>
            <ul className="text-xs text-muted-foreground space-y-1 max-w-md mx-auto text-left">
              <li>• The ML model needs to be trained with initial data</li>
              <li>• There aren&apos;t enough listings in the system yet</li>
              <li>• You haven&apos;t interacted with any listings yet</li>
            </ul>
            <p className="text-xs text-muted-foreground pt-2">
              Browse the marketplace to help train the recommendation engine!
            </p>
            <Button asChild>
              <Link href="/market">Browse All Listings</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (feedLoading && listings.length === 0) {
    return (
      <div className="w-full py-8 space-y-4">
        <h2 className="text-2xl font-bold">Recommended for You</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-48 bg-muted rounded animate-pulse"
            ></div>
          ))}
        </div>
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <div className="w-full py-8 space-y-4">
        <h2 className="text-2xl font-bold">Recommended for You</h2>
        <Card>
          <CardContent className="py-8 text-center space-y-4">
            <p className="text-muted-foreground">
              No recommendations yet. Browse listings to help us learn your preferences!
            </p>
            <Button asChild>
              <Link href="/market">Explore Marketplace</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }


  async function handleApply(listingId: string | number) {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  const supabase = createClient();
  const { data } = await supabase.auth.getUser();
  if (!data?.user) return;

  const uid = data.user.id;

  // 1. Call your real apply endpoint
  await fetch(
    `${baseUrl}/api/v1/listings/${listingId}/applicants/${uid}/apply`,
    {
      method: "POST",
    }
  );

  // 2. Track interaction (optional but recommended)
  await fetch(
    `${baseUrl}/api/v1/feed/interactions/${listingId}?user_uid=${uid}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ interaction_type: "apply" }),
    }
  );
}


async function handleIgnore(listingId: string | number) {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  const { data } = await supabase.auth.getUser();
  if (!data?.user) return;

  const uid = data.user.id;

  // Track "dismiss"
  await fetch(`${baseUrl}/api/v1/feed/interactions/${listingId}?user_uid=${uid}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ interaction_type: "dismiss" }),
  });

  // Removing from stack happens automatically inside TaskCardStack
}

  return (
    <div className="w-full py-8 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Recommended for You</h2>
          <p className="text-sm text-muted-foreground">
            Powered by machine learning • Personalized to your interests
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/market">View All</Link>
        </Button>
      </div>

      <div>
        <TaskCardStack
  tasks={listings.map(l => ({
    id: l.id,                     // the actual UUID
    title: l.name,
    description: l.description,
    reward: `${l.currency} ${l.compensation ?? ""}`,
    location: l.location_address,
    postedBy: l.poster_uid ? posterNames[l.poster_uid] : "Unknown",
    coverImage: l.images?.[0] ?? "/placeholder.svg",
  }))}
  onApply={handleApply}
  onIgnore={handleIgnore}
/>
      </div>

      <div className="text-center pt-4">
        <Button asChild size="lg">
          <Link href="/market">See More Recommendations</Link>
        </Button>
      </div>
    </div>
  );
}
