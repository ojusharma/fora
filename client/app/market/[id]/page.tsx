"use client";

import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { notFound, redirect, useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type Listing = {
  id: string;
  name: string;
  description: string;
  images: string[];
  compensation: number;
  currency?: string;
  deadline?: string;
  location_address?: string;
};

export default function Page() {
  const params = useParams();
  const router = useRouter();
  const [listing, setListing] = useState<Listing | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function checkAuthAndFetch() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();

      if (!user) {
        router.push("/auth/login");
        return;
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const id = params.id as string;

      try {
        const res = await fetch(`${baseUrl}/api/v1/listings/${id}`, {
          cache: "no-store",
        });
        
        if (!res.ok) {
          notFound();
          return;
        }

        const data = await res.json();
        setListing(data);
      } catch (error) {
        console.error("Failed to fetch listing:", error);
      } finally {
        setIsLoading(false);
      }
    }

    checkAuthAndFetch();
  }, [params.id, router]);

  if (isLoading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center">
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

  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-6xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href={"/"}>fora</Link>
              <Link href={"/market"}>marketplace</Link>
              <Link href={"/map"}>map</Link>
            </div>
            <AuthButton />
          </div>
        </nav>
        <div className="flex-1 flex flex-col gap-8 w-full max-w-3xl p-5">
          <div className="flex items-center gap-4">
            <Link
              href="/map"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              ← Back to map
            </Link>
            <Link
              href="/market"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              ← Back to marketplace
            </Link>
          </div>

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
              {typeof listing.compensation === "number" && (
                <p className="text-sm font-medium">
                  ${listing.compensation.toLocaleString()}
                </p>
              )}
              {listing.deadline && (
                <p className="text-xs text-muted-foreground">
                  Deadline: {new Date(listing.deadline).toLocaleString()}
                </p>
              )}
              {listing.location_address && (
                <p className="text-xs text-muted-foreground">
                  📍 {listing.location_address}
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
