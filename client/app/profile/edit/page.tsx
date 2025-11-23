import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import EditProfileForm from "@/components/profile/edit-profile-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Suspense } from "react";
import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { Button } from "@/components/ui/button";
import { NotificationBell } from "@/components/notification-bell";

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
}

async function EditProfileContent() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();

  if (error || !data?.claims) {
    redirect("/auth/login");
  }

  const userId = data.claims.sub;
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  // Fetch user profile
  let profile: UserProfile | null = null;
  try {
    const profileRes = await fetch(`${baseUrl}/api/v1/users/${userId}`, {
      cache: "no-store",
    });
    if (profileRes.ok) {
      profile = await profileRes.json();
    }
  } catch (e) {
    console.error("Failed to fetch profile:", e);
  }

  return (
    <div className="flex-1 flex flex-col gap-8 max-w-2xl w-full p-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Edit Profile</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Update your profile information
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <CardDescription>
            Update your personal information and contact details
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EditProfileForm profile={profile} userId={userId} />
        </CardContent>
      </Card>
    </div>
  );
}

export default function EditProfilePage() {

  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-6xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href={"/"}>fora</Link>
              <Link href={"/market"}>marketplace</Link>
              <Link href={"/map"}>map</Link>
              <Link href={"/chats"}>chats</Link>
              <Link href={"/profile"}>profile</Link>
            </div>
            <div className="flex items-center gap-4">
  <Suspense>
    <NotificationBell />
  </Suspense>

  <AuthButton />
</div>
          </div>
        </nav>

        <Suspense fallback={
          <div className="flex-1 flex flex-col gap-8 max-w-2xl w-full p-5">
            <div className="animate-pulse space-y-4">
              <div className="h-10 bg-muted rounded w-1/3"></div>
              <div className="h-64 bg-muted rounded"></div>
            </div>
          </div>
        }>
          <EditProfileContent />
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
