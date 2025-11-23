"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";

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

interface EditProfileFormProps {
  profile: UserProfile | null;
  userId: string;
}

export default function EditProfileForm({ profile, userId }: EditProfileFormProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSaved, setShowSaved] = useState(false);

  // Form state
  const [displayName, setDisplayName] = useState(profile?.display_name || "");
  const [phone, setPhone] = useState(profile?.phone || "");
  const [dob, setDob] = useState(
    profile?.dob ? new Date(profile.dob).toISOString().split("T")[0] : ""
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setShowSaved(false);

    try {
      const baseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      // Prepare update payload - only include changed fields
      const updateData: Record<string, string> = {};
      
      if (displayName !== (profile?.display_name || "")) {
        updateData.display_name = displayName;
      }
      if (phone !== (profile?.phone || "")) {
        updateData.phone = phone;
      }
      if (dob !== (profile?.dob ? new Date(profile.dob).toISOString().split("T")[0] : "")) {
        updateData.dob = dob;
      }

      // If no changes, just redirect
      if (Object.keys(updateData).length === 0) {
        router.push("/profile");
        return;
      }

      const response = await fetch(`${baseUrl}/api/v1/users/${userId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update profile");
      }

      // Update Supabase auth user metadata if display name changed
      if (displayName !== (profile?.display_name || "")) {
        const supabase = createClient();
        await supabase.auth.updateUser({
          data: {
            display_name: displayName,
          },
        });
      }

      setShowSaved(true);
      
      // Hide the "Saved" message after 3 seconds
      setTimeout(() => {
        setShowSaved(false);
      }, 3000);
      
      // Redirect to profile page after a short delay
      setTimeout(() => {
        router.push("/profile");
        router.refresh();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">
          {error}
        </div>
      )}

      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="display-name">Display Name</Label>
          <Input
            id="display-name"
            type="text"
            placeholder="Your display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            disabled={isLoading}
          />
          <p className="text-xs text-muted-foreground">
            This is how others will see your name on the platform
          </p>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="phone">Phone Number</Label>
          <Input
            id="phone"
            type="tel"
            placeholder="+1 (555) 000-0000"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            disabled={isLoading}
          />
          <p className="text-xs text-muted-foreground">
            Your contact number (optional)
          </p>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="dob">Date of Birth</Label>
          <Input
            id="dob"
            type="date"
            value={dob}
            onChange={(e) => setDob(e.target.value)}
            disabled={isLoading}
          />
          <p className="text-xs text-muted-foreground">
            Your date of birth (optional)
          </p>
        </div>
      </div>

      <div className="flex gap-3 items-center">
        <Button type="submit" disabled={isLoading} className="flex-1">
          {isLoading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-2 h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Saving...
            </>
          ) : (
            "Save Changes"
          )}
        </Button>
        {showSaved && (
          <span className="text-sm text-green-600 dark:text-green-400 font-medium">
            Saved
          </span>
        )}
        <Button
          type="button"
          variant="outline"
          onClick={() => router.push("/profile")}
          disabled={isLoading}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
