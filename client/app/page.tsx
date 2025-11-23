import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { createClient } from "@/lib/supabase/server";
import { HomeRecommendations } from "@/components/home-recommendations";
import Link from "next/link";
import { Suspense } from "react";

export default async function Home() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();

  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-6xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href={"/"}>fora</Link>
              <Link href={"/market"}>marketplace</Link>
              <Link href={"/map"}>map</Link>
              {process.env.NODE_ENV === "development" && (
                <Link
                  href={"/ml-admin"}
                  className="text-xs px-2 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 rounded"
                >
                  🔧 ML Admin
                </Link>
              )}
            </div>
            <Suspense>
              <AuthButton />
            </Suspense>
          </div>
        </nav>
        <div className="flex-1 flex flex-col gap-12 max-w-6xl w-full p-5">
          <main className="flex-1 flex flex-col gap-8">
            <section className="text-center space-y-4 py-12">
              <h1 className="text-4xl font-bold tracking-tight">
                Welcome to Fora
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Discover opportunities tailored to your interests with our
                AI-powered recommendation engine
              </p>
            </section>

            <Suspense
              fallback={
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
              }
            >
              <HomeRecommendations />
            </Suspense>

            <section className="py-12 border-t">
              <div className="grid gap-8 md:grid-cols-3">
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">🎯 Personalized</h3>
                  <p className="text-sm text-muted-foreground">
                    Our ML algorithm learns your preferences and shows you the
                    most relevant opportunities
                  </p>
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">📍 Location-Aware</h3>
                  <p className="text-sm text-muted-foreground">
                    Discover opportunities near you with intelligent geographic
                    matching
                  </p>
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">🚀 Always Learning</h3>
                  <p className="text-sm text-muted-foreground">
                    The more you interact, the better our recommendations become
                  </p>
                </div>
              </div>
            </section>
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
