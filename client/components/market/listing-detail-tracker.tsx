"use client";

import { useEffect, useRef } from "react";
import { usePersonalizedFeed } from "@/hooks/use-personalized-feed";

interface ListingDetailTrackerProps {
  listingId: string;
}

export function ListingDetailTracker({ listingId }: ListingDetailTrackerProps) {
  const { trackView } = usePersonalizedFeed({ autoFetch: false });
  const startTimeRef = useRef<number>(Date.now());
  const hasTrackedRef = useRef<boolean>(false);

  useEffect(() => {
    // Track view when component mounts
    if (!hasTrackedRef.current) {
      trackView(listingId);
      hasTrackedRef.current = true;
      startTimeRef.current = Date.now();
    }

    // Track view duration when component unmounts
    return () => {
      const timeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000);
      if (timeSpent > 1) {
        // Only track if they spent more than 1 second
        trackView(listingId, timeSpent);
      }
    };
  }, [listingId, trackView]);

  return null; // This component doesn't render anything
}
