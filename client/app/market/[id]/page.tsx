import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Suspense } from "react";

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
