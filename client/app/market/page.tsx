import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { createClient } from "@/lib/supabase/server";
import { CreateListingSection } from "@/components/market/create-listing-section";
import Link from "next/link";
import { Suspense } from "react";
import { redirect } from "next/navigation";

export default async function MarketPage() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();

  if (error || !data?.claims) {
    redirect("/auth/login");
  }

  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  let initialListings: any[] = [];

  try {
    const res = await fetch(`${baseUrl}/api/v1/listings`, {
      cache: "no-store",
    });
    if (res.ok) {
      initialListings = await res.json();
    }
  } catch {
    initialListings = [];
  }

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
            <Suspense>
              <AuthButton />
            </Suspense>
          </div>
        </nav>
        <div className="flex-1 flex flex-col gap-20 max-w-6xl w-full p-5">
          <main className="flex-1 flex flex-col gap-6 px-0">
            <h1 className="text-2xl font-semibold">Marketplace</h1>
            <p className="text-sm text-muted-foreground">
              Create a new listing and then manage it from the &quot;My
              listings&quot; tab.
            </p>
            <CreateListingSection initialListings={initialListings} />
          </main>
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
