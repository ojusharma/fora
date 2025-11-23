"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";

type InteractionType = "view" | "click" | "apply" | "save" | "share" | "dismiss";

type ListingWithScore = {
  id: string;
  name: string;
  description: string;
  compensation: number | null;
  currency: string;
  deadline?: string;
  images?: string[];
  tags?: number[];
  location_address?: string;
  latitude?: number;
  longitude?: number;
  poster_uid?: string;
  poster_rating?: number;
  created_at: string;
  status: string;
  recommendation_score?: number;
  score_components?: {
    location?: number;
    tags?: number;
    engagement?: number;
    recency?: number;
    poster_quality?: number;
    collaborative?: number;
    content?: number;
  };
};

type UsePersonalizedFeedOptions = {
  limit?: number;
  excludeSeen?: boolean;
  excludeApplied?: boolean;
  autoFetch?: boolean;
};

export function usePersonalizedFeed(options: UsePersonalizedFeedOptions = {}) {
  const {
    limit = 50,
    excludeSeen = true,
    excludeApplied = true,
    autoFetch = true,
  } = options;

  const [listings, setListings] = useState<ListingWithScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);

  const supabase = createClient();
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  // Get current user
  useEffect(() => {
    async function fetchUser() {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      setUserId(user?.id ?? null);
    }
    fetchUser();
  }, [supabase]);

  // Fetch personalized feed
  const fetchFeed = useCallback(
    async (loadMore = false) => {
      if (!userId) return;

      setLoading(true);
      setError(null);

      try {
        const currentOffset = loadMore ? offset : 0;
        const url = `${baseUrl}/api/v1/feed?user_uid=${encodeURIComponent(
          userId
        )}&limit=${limit}&offset=${currentOffset}&exclude_seen=${excludeSeen}&exclude_applied=${excludeApplied}`;

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch feed: ${response.statusText}`);
        }

        const data: ListingWithScore[] = await response.json();

        if (loadMore) {
          setListings((prev) => [...prev, ...data]);
        } else {
          setListings(data);
        }

        setHasMore(data.length === limit);
        setOffset(currentOffset + data.length);
      } catch (err) {
        console.error("Error fetching personalized feed:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch feed");
      } finally {
        setLoading(false);
      }
    },
    [userId, limit, offset, excludeSeen, excludeApplied, baseUrl]
  );

  // Track interaction with a listing
  const trackInteraction = useCallback(
    async (
      listingId: string,
      interactionType: InteractionType,
      metadata?: Record<string, any>
    ) => {
      if (!userId) return;

      try {
        const url = `${baseUrl}/api/v1/feed/interactions/${encodeURIComponent(
          listingId
        )}?user_uid=${encodeURIComponent(userId)}`;

        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            interaction_type: interactionType,
            metadata: metadata || {},
          }),
        });

        if (!response.ok) {
          console.error("Failed to track interaction:", response.statusText);
        }
      } catch (err) {
        console.error("Error tracking interaction:", err);
      }
    },
    [userId, baseUrl]
  );

  // Convenience methods for common interactions
  const trackView = useCallback(
    (listingId: string, timeSpentSeconds?: number) => {
      return trackInteraction(listingId, "view", {
        time_spent_seconds: timeSpentSeconds,
      });
    },
    [trackInteraction]
  );

  const trackClick = useCallback(
    (listingId: string) => {
      return trackInteraction(listingId, "click");
    },
    [trackInteraction]
  );

  const trackApply = useCallback(
    (listingId: string) => {
      return trackInteraction(listingId, "apply");
    },
    [trackInteraction]
  );

  const trackSave = useCallback(
    (listingId: string) => {
      return trackInteraction(listingId, "save");
    },
    [trackInteraction]
  );

  const trackShare = useCallback(
    (listingId: string) => {
      return trackInteraction(listingId, "share");
    },
    [trackInteraction]
  );

  const trackDismiss = useCallback(
    (listingId: string) => {
      return trackInteraction(listingId, "dismiss");
      // Also remove from current feed
      setListings((prev) => prev.filter((l) => l.id !== listingId));
    },
    [trackInteraction]
  );

  // Load more listings
  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      fetchFeed(true);
    }
  }, [loading, hasMore, fetchFeed]);

  // Refresh feed
  const refresh = useCallback(() => {
    setOffset(0);
    fetchFeed(false);
  }, [fetchFeed]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch && userId && listings.length === 0) {
      fetchFeed(false);
    }
  }, [autoFetch, userId, listings.length, fetchFeed]);

  return {
    listings,
    loading,
    error,
    hasMore,
    userId,
    trackInteraction,
    trackView,
    trackClick,
    trackApply,
    trackSave,
    trackShare,
    trackDismiss,
    loadMore,
    refresh,
  };
}

// Hook for fetching trending listings
export function useTrendingListings(limit = 20, hours = 24) {
  const [listings, setListings] = useState<ListingWithScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  useEffect(() => {
    async function fetchTrending() {
      setLoading(true);
      setError(null);

      try {
        const url = `${baseUrl}/api/v1/feed/trending?limit=${limit}&hours=${hours}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch trending: ${response.statusText}`);
        }

        const data = await response.json();
        setListings(data);
      } catch (err) {
        console.error("Error fetching trending listings:", err);
        setError(
          err instanceof Error ? err.message : "Failed to fetch trending"
        );
      } finally {
        setLoading(false);
      }
    }

    fetchTrending();
  }, [limit, hours, baseUrl]);

  return { listings, loading, error };
}

// Hook for fetching similar listings
export function useSimilarListings(listingId: string | null, limit = 10) {
  const [listings, setListings] = useState<ListingWithScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  useEffect(() => {
    if (!listingId) {
      setListings([]);
      return;
    }

    async function fetchSimilar() {
      setLoading(true);
      setError(null);

      try {
        const url = `${baseUrl}/api/v1/feed/similar/${encodeURIComponent(
          listingId as string
        )}?limit=${limit}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch similar: ${response.statusText}`);
        }

        const data = await response.json();
        setListings(data);
      } catch (err) {
        console.error("Error fetching similar listings:", err);
        setError(
          err instanceof Error ? err.message : "Failed to fetch similar"
        );
      } finally {
        setLoading(false);
      }
    }

    fetchSimilar();
  }, [listingId, limit, baseUrl]);

  return { listings, loading, error };
}
