"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { usePersonalizedFeed } from "@/hooks/use-personalized-feed";

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
    excludeApplied: false,
    autoFetch: isAuthenticated,
  });

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

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {listings.slice(0, 6).map((listing) => (
          <Link
            key={listing.id}
            href={`/market/${listing.id}`}
            onClick={() => trackClick(listing.id)}
            className="block"
          >
            <Card className="overflow-hidden hover:shadow-md transition-shadow cursor-pointer h-full">
              {listing.images && listing.images.length > 0 ? (
                <div className="h-32 bg-muted overflow-hidden">
                  <img
                    src={listing.images[0]}
                    alt={listing.name}
                    className="h-full w-full object-cover"
                  />
                </div>
              ) : (
                <div className="h-32 bg-gradient-to-br from-emerald-500/80 via-sky-500/80 to-indigo-500/80" />
              )}
              <CardContent className="p-4 space-y-2">
                <p className="text-sm font-semibold line-clamp-2">
                  {listing.name}
                </p>
                {listing.description && (
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {listing.description}
                  </p>
                )}
                {listing.recommendation_score !== undefined && (
                  <div className="pt-1">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{
                            width: `${Math.min(listing.recommendation_score * 100, 100)}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {Math.round(listing.recommendation_score * 100)}% match
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
              <CardFooter className="px-4 pb-4 pt-0 text-xs">
                {listing.compensation && (
                  <span className="text-sm font-semibold">
                    From {listing.currency || "USD"}{" "}
                    {Number(listing.compensation).toLocaleString()}
                  </span>
                )}
              </CardFooter>
            </Card>
          </Link>
        ))}
      </div>

      <div className="text-center pt-4">
        <Button asChild size="lg">
          <Link href="/market">See More Recommendations</Link>
        </Button>
      </div>
    </div>
  );
}
