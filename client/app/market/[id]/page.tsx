"use client";

import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { notFound, redirect, useParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import ApplyControls from "@/components/market/apply-controls";
import ApplicantActions from "@/components/market/applicant-actions";
import WithdrawButton from "../../../components/market/withdraw-button";
import { ListingDetailTracker } from "@/components/market/listing-detail-tracker";
import { createClient } from "@/lib/supabase/client";
import { GoogleMap, useJsApiLoader, Marker } from '@react-google-maps/api';
import { NotificationBell } from "@/components/notification-bell";

const mapContainerStyle = { width: "100%", height: "300px" };

function MarketDetailContent() {
  const params = useParams();
  const id = params?.id as string;
  
  const [listing, setListing] = useState<any>(null);
  const [posterDisplay, setPosterDisplay] = useState<string | null>(null);
  const [currentUid, setCurrentUid] = useState<string | null>(null);
  const [isPoster, setIsPoster] = useState(false);
  const [applicants, setApplicants] = useState<any[]>([]);
  const [myApplication, setMyApplication] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [tagNames, setTagNames] = useState<string[]>([]);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
  });

  useEffect(() => {
    async function loadData() {
      const supabase = createClient();
      const { data, error } = await supabase.auth.getUser();

      if (error || !data?.user) {
        window.location.href = "/auth/login";
        return;
      }

      const uid = data.user.id;
      setCurrentUid(uid);

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const res = await fetch(`${baseUrl}/api/v1/listings/${id}`, {
        cache: "no-store",
      });
      if (!res.ok) {
        notFound();
        return;
      }

      const listingData = await res.json();
      setListing(listingData);
      if (listingData.tags && Array.isArray(listingData.tags) && listingData.tags.length > 0) {
        try {
          const tagPromises = listingData.tags.map((tagId: number) =>
            fetch(`${baseUrl}/api/v1/tags/${tagId}`).then(async (r) => {
              if (r.ok) {
                const tag = await r.json();
                return tag.name;
              }
              return null;
            })
          );
          const names = await Promise.all(tagPromises);
          setTagNames(names.filter((name): name is string => name !== null));
        } catch (err) {
          console.error("Failed to fetch tag names:", err);
        }
      }

      // Fetch poster profile
      try {
        const posterUid = listingData.poster_uid ?? listingData.posterUid ?? listingData.poster ?? null;
        if (posterUid) {
          const profileRes = await fetch(`${baseUrl}/api/v1/users/${encodeURIComponent(posterUid)}`, { cache: "no-store" });
          if (profileRes.ok) {
            const profile = await profileRes.json();
            setPosterDisplay(profile.display_name ?? profile.full_name ?? profile.phone ?? String(profile.uid ?? profile.id ?? posterUid).slice(0, 8));
          } else {
            setPosterDisplay(String(posterUid).slice(0, 8));
          }
        }
      } catch (err) {
        setPosterDisplay(null);
      }

      // Determine if current user is the poster
      const isUserPoster = Boolean(uid && (listingData.poster_uid ?? listingData.posterUid ?? listingData.poster) && uid === (listingData.poster_uid ?? listingData.posterUid ?? listingData.poster));
      setIsPoster(isUserPoster);

      try {
        if (isUserPoster) {
          const applicantsRes = await fetch(`${baseUrl}/api/v1/listings/${id}/applicants`, { cache: "no-store" });
          if (applicantsRes.ok) {
            const apps = await applicantsRes.json();
            if (Array.isArray(apps) && apps.length > 0) {
              const uids = Array.from(new Set(apps.map((a: any) => a.applicant_uid).filter(Boolean)));
              const profilePromises = uids.map((uid) => fetch(`${baseUrl}/api/v1/users/${encodeURIComponent(uid)}`, { cache: "no-store" }).then(async (r) => (r.ok ? r.json() : null)));
              const profiles = await Promise.all(profilePromises);
              const nameByUid: Record<string, string> = {};
              profiles.forEach((p) => {
                if (!p) return;
                const uidVal = p.uid ?? p.id ?? null;
                if (!uidVal) return;
                nameByUid[String(uidVal)] = p.display_name ?? p.full_name ?? p.phone ?? String(uidVal).slice(0, 8);
              });

              setApplicants(apps.map((a: any) => ({
                ...a,
                display_name: nameByUid[a.applicant_uid] ?? String(a.applicant_uid).slice(0, 8),
              })));
            }
          }
        } else if (uid) {
          const myAppsRes = await fetch(`${baseUrl}/api/v1/listings/user/${encodeURIComponent(uid)}`, { cache: "no-store" });
          if (myAppsRes.ok) {
            const myApps = await myAppsRes.json();
            if (Array.isArray(myApps) && myApps.length > 0) {
              const found = myApps.find((a: any) => String(a.listing_id) === String(id) || String(a.listing_id) === String(listingData.id));
              if (found) {
                setMyApplication(found);
              }
            }
          }
        }
      } catch (err) {
        // ignore errors
      }

      setIsLoading(false);
    }

    loadData();
  }, [id]);

  if (isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </main>
    );
  }

  if (!listing) {
    return null;
  }

  const primaryImage =
    Array.isArray(listing.images) && listing.images.length > 0
      ? listing.images[0]
      : null;

  const hasLocation = listing.latitude && listing.longitude;

  return (
    <main className="min-h-screen flex flex-col items-center">
      {/* Track view interaction */}
      <ListingDetailTracker listingId={String(listing.id ?? id)} />
      
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-6xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href={"/"}>fora</Link>
              <Link href={"/market"}>marketplace</Link>
              <Link href={"/chats"}>my chats</Link>
            </div>
            <div className="flex items-center gap-4">
  <Suspense>
    <NotificationBell />
  </Suspense>

  <AuthButton />
</div>
          </div>
        </nav>
        <div className="flex-1 flex flex-col gap-8 w-full max-w-3xl p-5">
          <Link
            href="/market"
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            ← Back to marketplace
          </Link>

          <article className="flex flex-col gap-6">
            {primaryImage && typeof primaryImage === "string" ? (
              <div className="w-full h-56 rounded-lg overflow-hidden bg-muted border">
                <img
                  src={primaryImage}
                  alt={listing.name}
                  className="w-full h-full object-cover"
                />
              </div>
            ) : null}

            <header className="space-y-2">
              <h1 className="text-2xl font-semibold">{listing.name}</h1>
              {posterDisplay && (
                <p className="text-xs text-muted-foreground">Posted by {posterDisplay}</p>
              )}
                {!isPoster && currentUid && (!myApplication || myApplication.status === 'withdrawn' || myApplication.status === 'rejected') && (
                  <div className="pt-2">
                    <ApplyControls
                      listingId={String(listing.id ?? id)}
                      posterUid={listing.poster_uid ?? listing.posterUid ?? listing.poster ?? null}
                      currentUserId={currentUid}
                    />
                  </div>
                )}
              {typeof listing.compensation === "number" && (
                <p className="text-sm font-medium">
                  From {listing.currency ?? "USD"}{" "}
                  {listing.compensation.toLocaleString()}
                </p>
              )}
              {listing.deadline && (
                <p className="text-xs text-muted-foreground">
                  Deadline: {new Date(listing.deadline).toLocaleString()}
                </p>
              )}
              {listing.location_address && (
                <p className="text-xs text-muted-foreground">
                  {listing.location_address}
                </p>
              )}
              {tagNames.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2">
                  {tagNames.map((tagName, index) => (
                    <Badge key={index} variant="secondary">
                      {tagName}
                    </Badge>
                  ))}
                </div>
              )}
            </header>

            {listing.description && (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Description</h2>
                <p className="text-sm text-muted-foreground whitespace-pre-line">
                  {listing.description}
                </p>
              </section>
            )}

            {/* Map Section */}
            {hasLocation && (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Location</h2>
                <div className="w-full rounded-lg overflow-hidden border">
                  {!isLoaded ? (
                    <div className="w-full h-[300px] flex items-center justify-center bg-muted">
                      <p className="text-sm text-muted-foreground">Loading map...</p>
                    </div>
                  ) : (
                    <GoogleMap
                      mapContainerStyle={mapContainerStyle}
                      center={{ lat: listing.latitude, lng: listing.longitude }}
                      zoom={14}
                      options={{
                        streetViewControl: false,
                        mapTypeControl: false,
                        fullscreenControl: false,
                      }}
                    >
                      <Marker
                        position={{ lat: listing.latitude, lng: listing.longitude }}
                        icon={{
                          path: window.google?.maps?.SymbolPath?.CIRCLE,
                          scale: 10,
                          fillColor: "#3b82f6",
                          fillOpacity: 1,
                          strokeColor: "#ffffff",
                          strokeWeight: 2,
                        }}
                      />
                    </GoogleMap>
                  )}
                </div>
                {listing.location_address && (
                  <p className="text-xs text-muted-foreground">
                    📍 {listing.location_address}
                  </p>
                )}
              </section>
            )}

            {isPoster ? (
              applicants.length > 0 ? (
                <section className="space-y-2">
                  <h2 className="text-sm font-semibold">Applicants</h2>
                  <div className="space-y-2">
                    {applicants.map((a) => (
                      <div key={String(a.applicant_uid)} className="flex flex-col gap-1 p-3 border rounded">
                        <div className="flex items-center justify-between">
                          <div className="text-sm font-medium">{a.display_name}</div>
                          <div className="text-xs text-muted-foreground">{String(a.status)}</div>
                        </div>
                        {a.message && <div className="text-xs text-muted-foreground">{a.message}</div>}
                        {a.applied_at && (
                          <div className="text-xs text-muted-foreground">Applied: {new Date(a.applied_at).toLocaleString()}</div>
                        )}

                        {currentUid && listing.poster_uid && currentUid === listing.poster_uid && (
                          <ApplicantActions
                            listingId={String(listing.id ?? id)}
                            applicantUid={String(a.applicant_uid)}
                            currentUserId={currentUid}
                            initialStatus={String(a.status ?? "")}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              ) : null
            ) : (
              // Not the poster: show my application status and withdraw option if applied
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Your application</h2>
                <div>
                  {myApplication && myApplication.status !== 'withdrawn' && myApplication.status !== 'rejected' ? (
                    <div className="flex items-center gap-3">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-muted text-foreground">
                        {String(myApplication.status).toUpperCase()}
                      </span>
                      <div className="text-xs text-muted-foreground">Applied: {new Date(myApplication.applied_at).toLocaleString()}</div>
                      <div className="ml-auto">
                        <Suspense>
                          {/* WithdrawButton is client-side and will reload on success */}
                          {currentUid && <WithdrawButton listingId={String(listing.id ?? id)} currentUserId={currentUid} />}
                        </Suspense>
                      </div>
                    </div>
                  ) : myApplication && (myApplication.status === 'withdrawn' || myApplication.status === 'rejected') ? (
                    <div className="text-sm text-muted-foreground">
                      You previously {myApplication.status === 'withdrawn' ? 'withdrew your application' : 'were rejected'}. You can apply again if you wish.
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">You have not applied to this listing.</div>
                  )}
                </div>
              </section>
            )}
          </article>
        </div>

        <footer className="w-full flex items-center justify-center border-t mx-auto text-center text-xs gap-8 py-16">
          <p>
            Powered by{" "}
            <a
              href="https://supabase.com/?utm_source=create-next-app&utm_medium=template&utm_term=nextjs"
              target="_blank"
              className="font-bold hover:underline"
              rel="noreferrer"
            >
              Supabase
            </a>
          </p>
          <ThemeSwitcher />
        </footer>
      </div>
    </main>
  );
}

export default function Page() {
  return (
    <Suspense fallback={
      <main className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </main>
    }>
      <MarketDetailContent />
    </Suspense>
  );
}
