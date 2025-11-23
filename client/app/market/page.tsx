import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { MarketContent } from "@/components/market/market-content";
import { MarketSkeleton } from "@/components/market/market-skeleton";
import Link from "next/link";
import { Suspense } from "react";
import { NotificationBell } from "@/components/notification-bell";
import { CreditsDisplay } from "@/components/credits-display";
import { AdminLink } from "@/components/admin-link";

export default function MarketPage() {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-6xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href={"/"}>fora</Link>
              <Link href={"/market"}>marketplace</Link>
              <Link href={"/map"}>map</Link>
              <AdminLink />
              <Link href="/chats">chats</Link>
            </div>
            <div className="flex items-center gap-4">
  <Suspense>
    <CreditsDisplay />
  </Suspense>
  <Suspense>
    <NotificationBell />
  </Suspense>

  <AuthButton />
</div>
          </div>
        </nav>

        <Suspense fallback={<MarketSkeleton />}>
          <MarketContent baseUrl={baseUrl} />
        </Suspense>

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
