"use client";

import { useState, type ChangeEvent } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

type ListingImage = {
  url: string;
  alt: string;
};

type Listing = {
  id: number;
  name: string;
  description: string;
  compensation: string;
  currency: string;
  deadline?: string;
  images?: ListingImage[];
  seller: string;
  rating?: number;
  reviewsCount?: number;
};

const featuredListings: Listing[] = [
  {
    id: 1,
    name: "I will design a modern landing page for your SaaS",
    compensation: "120",
    currency: "USD",
    description: "Conversion-focused, responsive, and on-brand.",
    seller: "studioflow",
    rating: 4.9,
    reviewsCount: 87,
  },
  {
    id: 2,
    name: "I will build a Supabase + Next.js MVP in a week",
    compensation: "950",
    currency: "USD",
    description: "Auth, database, and basic dashboard wired up.",
    seller: "shipfast",
    rating: 5.0,
    reviewsCount: 41,
  },
  {
    id: 3,
    name: "I will create a brand kit for your startup",
    compensation: "260",
    currency: "USD",
    description: "Logo, colors, and typography ready to use.",
    seller: "brandlab",
    rating: 4.8,
    reviewsCount: 132,
  },
  {
    id: 4,
    name: "I will audit your onboarding and suggest improvements",
    compensation: "180",
    currency: "USD",
    description: "Actionable UX review with a prioritized checklist.",
    seller: "uxclinic",
    rating: 4.9,
    reviewsCount: 59,
  },
];

export function CreateListingSection() {
  const [name, setName] = useState("");
  const [compensation, setCompensation] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [deadline, setDeadline] = useState("");
  const [description, setDescription] = useState("");
  const [images, setImages] = useState<ListingImage[]>([
    { url: "", alt: "" },
  ]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [activeTab, setActiveTab] = useState<"marketplace" | "mine">(
    "marketplace",
  );

  const handleImageUpload = async (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const supabase = createClient();
    setIsUploading(true);
    setUploadError(null);

    try {
      const uploaded: ListingImage[] = [];

      for (const file of Array.from(files)) {
        const ext = file.name.split(".").pop() ?? "jpg";
        const fileName = `${Date.now()}-${Math.random()
          .toString(36)
          .slice(2)}.${ext}`;

        const { error } = await supabase.storage
          .from("listing-images")
          .upload(fileName, file);

        if (error) {
          throw error;
        }

        const { data: publicData } = supabase.storage
          .from("listing-images")
          .getPublicUrl(fileName);

        if (publicData?.publicUrl) {
          uploaded.push({
            url: publicData.publicUrl,
            alt: file.name,
          });
        }
      }

      setImages((prev) => {
        const existing = prev.filter((img) => img.url || img.alt);
        return [...existing, ...uploaded];
      });

      event.target.value = "";
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : "Failed to upload images",
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) return;
    if (isUploading) {
      setSubmitError("Please wait for images to finish uploading.");
      return;
    }

    const supabase = createClient();
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        throw new Error("You must be signed in to create a listing.");
      }

      const payload = {
        name: name.trim(),
        description: description.trim() || null,
        images: images
          .map((image) => image.url.trim())
          .filter((url) => url.length > 0),
        tags: [] as number[],
        latitude: null as number | null,
        longitude: null as number | null,
        deadline: deadline ? new Date(deadline).toISOString() : null,
        compensation: compensation ? Number(compensation) : null,
      };

      const baseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const res = await fetch(
        `${baseUrl}/api/v1/listings?user_uid=${encodeURIComponent(user.id)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        },
      );

      if (!res.ok) {
        let message = "Failed to create listing";
        try {
          const data = await res.json();
          if (data?.detail) {
            message = Array.isArray(data.detail)
              ? data.detail.map((d: any) => d.msg ?? String(d)).join(", ")
              : String(data.detail);
          }
        } catch {
          // ignore JSON parse errors
        }
        throw new Error(message);
      }

      const newListing: Listing = {
        id: Date.now(),
        name: name.trim(),
        compensation: compensation.trim(),
        currency: currency.trim() || "USD",
        deadline: deadline || undefined,
        description: description.trim(),
        images: images
          .map((image) => ({
            url: image.url.trim(),
            alt: image.alt.trim(),
          }))
          .filter((image) => image.url.length > 0),
        seller: "You",
      };

      setListings((prev) => [newListing, ...prev]);
      setName("");
      setCompensation("");
      setCurrency("USD");
      setDeadline("");
      setDescription("");
      setImages([{ url: "", alt: "" }]);
      setActiveTab("mine");
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Failed to create listing",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <Dialog>
        <div className="flex items-center justify-between gap-4">
          <div className="inline-flex items-center rounded-md bg-muted p-1 text-xs">
            <button
              type="button"
              onClick={() => setActiveTab("marketplace")}
              className={cn(
                "rounded-sm px-3 py-1.5 transition-colors",
                activeTab === "marketplace"
                  ? "bg-background text-foreground shadow"
                  : "text-muted-foreground",
              )}
            >
              Marketplace
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("mine")}
              className={cn(
                "rounded-sm px-3 py-1.5 transition-colors",
                activeTab === "mine"
                  ? "bg-background text-foreground shadow"
                  : "text-muted-foreground",
              )}
            >
              My listings
            </button>
          </div>
          <DialogTrigger asChild>
            <Button size="sm">New listing</Button>
          </DialogTrigger>
        </div>

        <DialogContent>
          <DialogHeader>
            <DialogTitle>New listing</DialogTitle>
            <DialogDescription>
              Describe what you&apos;re offering and set a starting price.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Title</Label>
              <Input
                id="name"
                placeholder="I will help you ship your MVP"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="compensation">Compensation</Label>
              <div className="flex gap-2">
                <Input
                  id="compensation"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="99"
                  value={compensation}
                  onChange={(e) => setCompensation(e.target.value)}
                  className="flex-1"
                />
                <Input
                  id="currency"
                  className="w-20 uppercase"
                  maxLength={3}
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="deadline">Deadline</Label>
              <Input
                id="deadline"
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="images">Images</Label>
              <p className="text-[11px] text-muted-foreground">
                Upload one or more images. The first will be used as the card
                cover.
              </p>
              <Input
                id="images"
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageUpload}
                disabled={isUploading}
              />
              {isUploading && (
                <p className="text-[11px] text-muted-foreground">
                  Uploading images...
                </p>
              )}
              {uploadError && (
                <p className="text-[11px] text-red-500 text-[11px]">
                  {uploadError}
                </p>
              )}
              {images.length > 0 &&
                images.some((image) => image.url) && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {images
                      .filter((image) => image.url)
                      .map((image, index) => (
                        <div
                          key={index}
                          className="h-16 w-16 rounded-md overflow-hidden border bg-muted"
                        >
                          <img
                            src={image.url}
                            alt={image.alt || name || `Listing image ${index + 1}`}
                            className="h-full w-full object-cover"
                          />
                        </div>
                      ))}
                  </div>
                )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Explain what you do, what the buyer gets, and any requirements."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            {submitError && (
              <p className="text-[11px] text-red-500">{submitError}</p>
            )}
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </DialogClose>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Publishing..." : "Publish"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {activeTab === "marketplace" ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {featuredListings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      ) : listings.length === 0 ? (
        <Card className="flex items-center justify-center">
          <CardContent className="text-sm text-muted-foreground">
            You haven&apos;t created any listings yet.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      )}
    </div>
  );
}

function ListingCard({ listing }: { listing: Listing }) {
  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow cursor-pointer">
      {listing.images && listing.images.length > 0 && listing.images[0].url ? (
        <div className="h-24 bg-muted overflow-hidden">
          <img
            src={listing.images[0].url}
            alt={listing.images[0].alt || listing.name}
            className="h-full w-full object-cover"
          />
        </div>
      ) : (
        <div className="h-20 bg-gradient-to-br from-emerald-500/80 via-sky-500/80 to-indigo-500/80" />
      )}
      <CardContent className="p-4 space-y-2">
        <p className="text-xs text-muted-foreground">{listing.seller}</p>
        <p className="text-sm font-semibold">{listing.name}</p>
        {listing.description && (
          <p className="text-xs text-muted-foreground">
            {listing.description}
          </p>
        )}
      </CardContent>
      <CardFooter className="flex items-center justify-between px-4 pb-4 pt-0 text-xs">
        {listing.rating ? (
          <span className="flex items-center gap-1 text-foreground">
            <span>★</span>
            <span>
              {listing.rating.toFixed(1)}
              {listing.reviewsCount
                ? ` (${listing.reviewsCount.toLocaleString()})`
                : ""}
            </span>
          </span>
        ) : (
          <span className="text-muted-foreground">New</span>
        )}
        {listing.compensation && (
          <span className="text-sm font-semibold">
            From {listing.currency || "USD"}{" "}
            {Number(listing.compensation).toLocaleString()}
          </span>
        )}
      </CardFooter>
    </Card>
  );
}
