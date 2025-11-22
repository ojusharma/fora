import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Suspense } from "react";
import ApplyControls from "@/components/market/apply-controls";
import ApplicantActions from "@/components/market/applicant-actions";
import WithdrawButton from "../../../components/market/withdraw-button";

export default async function Page({
  params,
}: {
  params: { id: string };
}) {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();

  if (error || !data?.claims) {
    redirect("/auth/login");
  }

  const currentUid = data?.claims?.sub ?? null;

  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

    const { id } = await params;

  const res = await fetch(`${baseUrl}/api/v1/listings/${id}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    notFound();
  }

  const listing = await res.json();

  // Fetch poster profile to show display name
  let posterDisplay: string | null = null;
  try {
    const posterUid = listing.poster_uid ?? listing.posterUid ?? listing.poster ?? null;
    if (posterUid) {
      const profileRes = await fetch(`${baseUrl}/api/v1/users/${encodeURIComponent(posterUid)}`, { cache: "no-store" });
      if (profileRes.ok) {
        const profile = await profileRes.json();
        posterDisplay = profile.display_name ?? profile.full_name ?? profile.phone ?? String(profile.uid ?? profile.id ?? posterUid).slice(0, 8);
      } else {
        posterDisplay = String(posterUid).slice(0, 8);
      }
    }
  } catch (err) {
    posterDisplay = null;
  }

  // Determine if current user is the poster
  const isPoster = Boolean(currentUid && (listing.poster_uid ?? listing.posterUid ?? listing.poster) && currentUid === (listing.poster_uid ?? listing.posterUid ?? listing.poster));

  // Fetch applicants only if I'm the poster; otherwise fetch my application status
  let applicants: any[] = [];
  let myApplication: any | null = null;
  try {
    if (isPoster) {
      const applicantsRes = await fetch(`${baseUrl}/api/v1/listings/${id}/applicants`, { cache: "no-store" });
      if (applicantsRes.ok) {
        const apps = await applicantsRes.json();
        if (Array.isArray(apps) && apps.length > 0) {
          // collect unique applicant uids
          const uids = Array.from(new Set(apps.map((a: any) => a.applicant_uid).filter(Boolean)));
          const profilePromises = uids.map((uid) => fetch(`${baseUrl}/api/v1/users/${encodeURIComponent(uid)}`, { cache: "no-store" }).then(async (r) => (r.ok ? r.json() : null)));
          const profiles = await Promise.all(profilePromises);
          const nameByUid: Record<string, string> = {};
          profiles.forEach((p) => {
            if (!p) return;
            const uid = p.uid ?? p.id ?? null;
            if (!uid) return;
            nameByUid[String(uid)] = p.display_name ?? p.full_name ?? p.phone ?? String(uid).slice(0, 8);
          });

          applicants = apps.map((a: any) => ({
            ...a,
            display_name: nameByUid[a.applicant_uid] ?? String(a.applicant_uid).slice(0, 8),
          }));
        }
      }
    } else if (currentUid) {
      // fetch my applications and find this listing
      const myAppsRes = await fetch(`${baseUrl}/api/v1/listings/users/${encodeURIComponent(currentUid)}/applications`, { cache: "no-store" });
      // Note: existing endpoint is `/api/v1/listings/users/{user_uid}/applications` per router definition
      if (myAppsRes.ok) {
        const myApps = await myAppsRes.json();
        if (Array.isArray(myApps) && myApps.length > 0) {
          const found = myApps.find((a: any) => String(a.listing_id) === String(id) || String(a.listing_id) === String(listing.id));
          if (found) {
            myApplication = found;
          }
        }
      }
    }
  } catch (err) {
    // ignore applicant loading errors
    applicants = [];
    myApplication = null;
  }

  const primaryImage =
    Array.isArray(listing.images) && listing.images.length > 0
      ? listing.images[0]
      : null;

  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-6xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href={"/"}>fora</Link>
              <Link href={"/market"}>marketplace</Link>
            </div>
            <Suspense>
              <AuthButton />
            </Suspense>
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
                {/* Apply/Ignore controls for users who are not the poster and who haven't applied */}
                {!isPoster && currentUid && !myApplication && (
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
            </header>

            {listing.description && (
              <section className="space-y-2">
                <h2 className="text-sm font-semibold">Description</h2>
                <p className="text-sm text-muted-foreground whitespace-pre-line">
                  {listing.description}
                </p>
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
                  {myApplication ? (
                    <div className="flex items-center gap-3">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-muted text-foreground">
                        {String(myApplication.status).toUpperCase()}
                      </span>
                      <div className="text-xs text-muted-foreground">Applied: {new Date(myApplication.applied_at).toLocaleString()}</div>
                      <div className="ml-auto">
                        <Suspense>
                          {/* WithdrawButton is client-side and will reload on success */}
                          <WithdrawButton listingId={String(listing.id ?? id)} currentUserId={currentUid} />
                        </Suspense>
                      </div>
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
