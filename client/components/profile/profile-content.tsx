import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface UserProfile {
  uid: string;
  display_name?: string;
  phone?: string;
  dob?: string;
  role?: string;
  credits?: number;
  latitude?: number;
  longitude?: number;
  last_updated?: string;
  user_rating?: number;
  no_ratings?: number;
}

interface UserStats {
  uid: string;
  num_listings_posted: number;
  num_listings_applied: number;
  num_listings_assigned: number;
  num_listings_completed: number;
  avg_rating?: number;
  updated_at: string;
}

interface UserPreference {
  tag_id: number;
  tag_name: string;
  tag_description?: string;
}

interface Listing {
  id: string;
  name: string;
  description?: string;
  poster_uid: string;
  assignee_uid?: string | null;
  status: string;
  created_at: string;
  compensation?: number;
  location_address?: string;
}

interface ProfileContentProps {
  userId: string;
  baseUrl: string;
}

async function fetchProfileData(userId: string, baseUrl: string) {
  const [profileRes, statsRes, prefsRes, listingsRes, completedListingsRes, pendingListingsRes] = await Promise.all([
    fetch(`${baseUrl}/api/v1/users/${userId}`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/v1/users/${userId}/stats/or-create`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/v1/users/${userId}/preferences/with-tags`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/v1/listings?poster_uid=${userId}`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/v1/listings?assignee_uid=${userId}&status=completed`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/v1/listings?assignee_uid=${userId}&status=pending_confirmation`, { cache: "no-store" }),
  ]);

  const profile: UserProfile | null = profileRes.ok ? await profileRes.json() : null;
  const stats: UserStats | null = statsRes.ok ? await statsRes.json() : null;
  const preferences: UserPreference[] = prefsRes.ok ? await prefsRes.json() : [];
  const listings: Listing[] = listingsRes.ok ? await listingsRes.json() : [];
  
  // Get completed listings where user is assignee
  const completedListings: Listing[] = completedListingsRes.ok ? await completedListingsRes.json() : [];
  const completedTasks = completedListings.map(listing => ({
    ...listing,
    status: "completed"
  }));
  
  // Get pending confirmation listings where user is assignee
  const pendingListings: Listing[] = pendingListingsRes.ok ? await pendingListingsRes.json() : [];
  const pendingTasks = pendingListings.map(listing => ({
    ...listing,
    status: "pending_confirmation"
  }));

  // Combine pending and completed tasks
  const allTasks = [...pendingTasks, ...completedTasks];

  return { profile, stats, preferences, listings, completedTasks: allTasks };
}

export async function ProfileContent({ userId, baseUrl }: ProfileContentProps) {
  const { profile, stats, preferences, listings, completedTasks } = await fetchProfileData(userId, baseUrl);
  const displayName = profile?.display_name || "User";

  return (
    <div className="flex-1 flex flex-col gap-8 max-w-6xl w-full p-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{displayName}&apos;s Profile</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your profile and view your activity
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/profile/edit">Edit Profile</Link>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Profile Info Card */}
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>Your account details and settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Display Name</span>
              <span className="text-sm text-muted-foreground">
                {profile?.display_name || "Not set"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Role</span>
              <Badge variant="secondary">{profile?.role || "user"}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Phone</span>
              <span className="text-sm text-muted-foreground">
                {profile?.phone || "Not set"}
              </span>
            </div>
            {profile?.dob && (
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Date of Birth</span>
                <span className="text-sm text-muted-foreground">
                  {new Date(profile.dob).toLocaleDateString()}
                </span>
              </div>
            )}
            {profile?.user_rating !== null && profile?.user_rating !== undefined && profile?.no_ratings && profile.no_ratings > 0 && (
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">User Rating</span>
                <span className="text-sm font-semibold">
                  {parseFloat(String(profile.user_rating)).toFixed(2)} ⭐ ({profile.no_ratings} {profile.no_ratings === 1 ? 'rating' : 'ratings'})
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Stats Card */}
        <Card>
          <CardHeader>
            <CardTitle>Activity Stats</CardTitle>
            <CardDescription>Your platform activity overview</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Credits Balance</span>
              <span className="text-2xl font-bold">{profile?.credits || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Listings Posted</span>
              <span className="text-2xl font-bold">{stats?.num_listings_posted || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Listings Applied</span>
              <span className="text-2xl font-bold">{stats?.num_listings_applied || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Listings Assigned</span>
              <span className="text-2xl font-bold">{stats?.num_listings_assigned || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Listings Completed</span>
              <span className="text-2xl font-bold">{stats?.num_listings_completed || 0}</span>
            </div>
            {stats?.avg_rating && (
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Average Rating</span>
                <span className="text-2xl font-bold">
                  {parseFloat(String(stats.avg_rating)).toFixed(1)} ⭐
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Preferences Card */}
      {preferences.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Your Preferences</CardTitle>
            <CardDescription>Tags you&apos;re interested in</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {preferences.map((pref) => (
                <Badge key={pref.tag_id} variant="default">
                  {pref.tag_name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Listings Card */}
      <Card>
        <CardHeader>
          <CardTitle>Your Listings</CardTitle>
          <CardDescription>
            Listings you&apos;ve created ({listings.length})
          </CardDescription>
        </CardHeader>
        <CardContent>
          {listings.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">
                You haven&apos;t created any listings yet
              </p>
              <Button asChild>
                <Link href="/market">Create Your First Listing</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {listings.slice(0, 5).map((listing) => (
                <Link
                  key={listing.id}
                  href={`/market?listing=${listing.id}`}
                  className="flex justify-between items-center p-3 border rounded-lg hover:bg-accent transition-colors cursor-pointer"
                >
                  <div className="flex-1">
                    <h3 className="font-medium">{listing.name}</h3>
                    {listing.description && (
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {listing.description}
                      </p>
                    )}
                    <div className="flex gap-2 items-center mt-1">
                      <p className="text-xs text-muted-foreground">
                        Created {new Date(listing.created_at).toLocaleDateString()}
                      </p>
                      {listing.compensation && (
                        <>
                          <span className="text-xs text-muted-foreground">•</span>
                          <p className="text-xs text-muted-foreground">
                            ${listing.compensation.toFixed(2)}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={listing.status === "open" ? "default" : "secondary"}>
                      {listing.status}
                    </Badge>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M9 18l6-6-6-6" />
                    </svg>
                  </div>
                </Link>
              ))}
              {listings.length > 5 && (
                <Button asChild variant="outline" className="w-full">
                  <Link href="/market">View All Listings</Link>
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Completed Tasks Card */}
      <Card>
        <CardHeader>
          <CardTitle>Completed Tasks</CardTitle>
          <CardDescription>
            Tasks you&apos;ve completed ({completedTasks.length})
          </CardDescription>
        </CardHeader>
        <CardContent>
          {completedTasks.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                You haven&apos;t completed any tasks yet
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {completedTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex justify-between items-center p-3 border rounded-lg"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        #{task.id.slice(0, 8)}
                      </Badge>
                      <h3 className="font-medium">{task.name}</h3>
                    </div>
                    <div className="flex gap-3 items-center text-sm text-muted-foreground">
                      {task.location_address && (
                        <div className="flex items-center gap-1">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                            <circle cx="12" cy="10" r="3" />
                          </svg>
                          <span className="text-xs">{task.location_address}</span>
                        </div>
                      )}
                      {task.compensation && (
                        <div className="flex items-center gap-1">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <line x1="12" x2="12" y1="2" y2="22" />
                            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                          </svg>
                          <span className="text-xs font-semibold text-green-600">
                            +{task.compensation.toFixed(2)} credits {task.status === "completed" ? "earned" : "pending"}
                          </span>
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
                          <line x1="16" x2="16" y1="2" y2="6" />
                          <line x1="8" x2="8" y1="2" y2="6" />
                          <line x1="3" x2="21" y1="10" y2="10" />
                        </svg>
                        <span className="text-xs">
                          {new Date(task.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {task.status === "completed" ? (
                      <div className="flex items-center gap-1 text-green-600" title="Task completed">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                          <polyline points="22 4 12 14.01 9 11.01" />
                        </svg>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1 text-yellow-600" title="Poster must confirm completion">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" x2="12" y1="8" y2="12" />
                          <line x1="12" x2="12.01" y1="16" y2="16" />
                        </svg>
                      </div>
                    )}
                    <Badge 
                      variant="default" 
                      className={task.status === "completed" ? "bg-green-600" : "bg-yellow-600"}
                    >
                      {task.status === "completed" ? "Completed" : "Pending Confirmation"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
