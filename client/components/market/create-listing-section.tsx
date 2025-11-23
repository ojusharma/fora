"use client";

import React, { useState, type ChangeEvent } from "react";
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
import { Badge } from "@/components/ui/badge";
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
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";
import Link from "next/link";

// Helper function to calculate distance between two coordinates (Haversine formula)
function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) *
      Math.cos(lat2 * (Math.PI / 180)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // Distance in km
}

type ListingImage = {
  url: string;
  alt: string;
};

type Listing = {
  id: string;
  name: string;
  description: string;
  compensation: string;
  currency: string;
  deadline?: string;
  images?: ListingImage[];
  seller: string;
  poster_uid?: string;
  rating?: number;
  reviewsCount?: number;
  latitude?: number | null;
  longitude?: number | null;
  location_address?: string | null;
  tags?: number[];
};

type CreateListingSectionProps = {
  initialListings: any[];
};

function mapApiListing(item: any): Listing {
  return {
    id: String(item.id),
    name: item.name ?? "",
    description: item.description ?? "",
    compensation:
      item.compensation !== null && item.compensation !== undefined
        ? String(item.compensation)
        : "",
    currency: item.currency ?? "USD",
    deadline: item.deadline ?? undefined,
    images: Array.isArray(item.images)
      ? item.images.map((url: string) => ({
          url,
          alt: item.name ?? "",
        }))
      : undefined,
    seller: "Creator",
    poster_uid: item.poster_uid ?? item.posterUid ?? item.poster ?? undefined,
    rating:
      typeof item.poster_rating === "number" ? item.poster_rating : undefined,
    reviewsCount: undefined,
    latitude: item.latitude ?? item.location_latitude ?? null,
    longitude: item.longitude ?? item.location_longitude ?? null,
    location_address: item.location_address ?? null,
    tags: Array.isArray(item.tags) ? item.tags : [],
  };
}

export function CreateListingSection({
  initialListings,
}: CreateListingSectionProps) {
  const [name, setName] = useState("");
  const [compensation, setCompensation] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [deadline, setDeadline] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [locationSuggestions, setLocationSuggestions] = useState<Array<{
    description: string;
    place_id: string;
    lat: number;
    lng: number;
  }>>([]);
  const [isGeocodingLocation, setIsGeocodingLocation] = useState(false);
  const [images, setImages] = useState<ListingImage[]>([
    { url: "", alt: "" },
  ]);
  const [tags, setTags] = useState<number[]>([])
  const [tagInput, setTagInput] = useState("");
  const [availableTags, setAvailableTags] = useState<Array<{ id: number; name: string }>>([]);
  const [filteredTags, setFilteredTags] = useState<Array<{ id: number; name: string }>>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [myListings, setMyListings] = useState<Listing[]>([]);
  const [marketListings, setMarketListings] = useState<Listing[]>(() =>
    Array.isArray(initialListings)
      ? initialListings.map((item) => mapApiListing(item))
      : [],
  );
  const [userId, setUserId] = useState<string | null>(null);
  
  // Filter states
  const [nameFilter, setNameFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [locationRadius, setLocationRadius] = useState("25");
  const [locationCenter, setLocationCenter] = useState<{ lat: number; lng: number } | null>(null);
  const [isGeocodingFilter, setIsGeocodingFilter] = useState(false);
  const [selectedFilterTags, setSelectedFilterTags] = useState<number[]>([]);

  // Merge incoming listings into existing list, keeping incoming first and
  // removing duplicates by `id`.
  function mergeUnique(incoming: Listing[], existing: Listing[]) {
    const seen = new Set<string>();
    const out: Listing[] = [];
    for (const l of incoming) {
      if (!seen.has(l.id)) {
        seen.add(l.id);
        out.push(l);
      }
    }
    for (const l of existing) {
      if (!seen.has(l.id)) {
        seen.add(l.id);
        out.push(l);
      }
    }
    return out;
  }

  // Fetch display names for poster_uids and populate seller + myListings
  React.useEffect(() => {
    let mounted = true;
    const supabase = createClient();

    async function fetchAvailableTags() {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/v1/tags`);
        if (response.ok) {
          const tagsData = await response.json();
          if (mounted) {
            setAvailableTags(tagsData);
          }
        }
      } catch (error) {
        console.error("Failed to fetch tags:", error);
      }
    }

    async function enrichListings() {
      // get current user id
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();
        const currentUid = user?.id ?? null;
        if (!mounted) return;
        setUserId(currentUid ?? null);

        // collect unique poster_uids
        const listings = marketListings.slice();
        const uids = Array.from(
          new Set(listings.map((l) => l.poster_uid).filter(Boolean)),
        ) as string[];

        if (uids.length === 0) return;

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

        // fetch profiles in parallel
        const profilePromises = uids.map((uid) =>
          fetch(`${baseUrl}/api/v1/users/${encodeURIComponent(uid)}`).then(async (r) => {
            if (!r.ok) return null;
            try {
              return await r.json();
            } catch {
              return null;
            }
          }),
        );

        const profiles = await Promise.all(profilePromises);
        if (!mounted) return;

        const nameByUid: Record<string, string> = {};
        profiles.forEach((p) => {
          if (!p) return;
          const uid = p.uid ?? p.id ?? null;
          if (!uid) return;
          // prefer a display field if present, fall back to phone or short uid
          const display = p.display_name ?? p.full_name ?? p.phone ?? String(uid).slice(0, 8);
          nameByUid[String(uid)] = display;
        });

        // update market listings and hide current user's listings from the marketplace
        const updatedMarket = listings.map((l) => ({
          ...l,
          seller: l.poster_uid && nameByUid[l.poster_uid] ? nameByUid[l.poster_uid] : l.seller,
        }));


        const mine = updatedMarket.filter((l) => currentUid && l.poster_uid === currentUid) as Listing[];

        const marketForViewer = updatedMarket.filter((l) => !(currentUid && l.poster_uid === currentUid));

        setMarketListings(marketForViewer);
        if (mine.length > 0) setMyListings((prev) => mergeUnique(mine, prev));
      } catch (err) {
        // ignore enrichment errors
        console.error("Failed to enrich listings with user profiles", err);
      }
    }

    fetchAvailableTags();
    enrichListings();

    return () => {
      mounted = false;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const [activeTab, setActiveTab] = useState<"marketplace" | "mine">(
    "marketplace",
  );
  const [dialogOpen, setDialogOpen] = useState(false);

  // Filter tags based on input
  React.useEffect(() => {
    if (tagInput.trim()) {
      const filtered = availableTags.filter(
        (tag) =>
          tag.name.toLowerCase().includes(tagInput.toLowerCase()) &&
          !tags.includes(tag.id)
      );
      setFilteredTags(filtered);
    } else {
      setFilteredTags([]);
    }
  }, [tagInput, availableTags, tags]);

  // Geocode location filter with debounce
  React.useEffect(() => {
    async function geocodeFilterLocation() {
      if (!locationFilter.trim()) {
        setLocationCenter(null);
        return;
      }

      setIsGeocodingFilter(true);
      try {
        const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
        const response = await fetch(
          `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(locationFilter)}&key=${apiKey}`
        );
        const data = await response.json();

        console.log('Geocoding response:', data);

        if (data.status === "OK" && data.results.length > 0) {
          const loc = data.results[0].geometry.location;
          const center = { lat: loc.lat, lng: loc.lng };
          console.log('Setting locationCenter to:', center);
          setLocationCenter(center);
        } else {
          console.log('Geocoding failed:', data.status);
          setLocationCenter(null);
        }
      } catch (error) {
        console.error("Geocoding error:", error);
        setLocationCenter(null);
      } finally {
        setIsGeocodingFilter(false);
      }
    }

    const timer = setTimeout(() => {
      geocodeFilterLocation();
    }, 500);

    return () => clearTimeout(timer);
  }, [locationFilter]);

  const addTag = (tagId: number) => {
    if (!tags.includes(tagId)) {
      setTags([...tags, tagId]);
      setTagInput("");
    }
  };

  const createAndAddTag = async (tagName: string) => {
    console.log('createAndAddTag called with:', tagName);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      
      // Check if tag already exists (case-insensitive)
      const existingTag = availableTags.find(
        (tag) => tag.name.toLowerCase() === tagName.toLowerCase()
      );
      
      console.log('Existing tag check:', existingTag);
      
      if (existingTag) {
        // Tag already exists, just add it
        if (!tags.includes(existingTag.id)) {
          setTags([...tags, existingTag.id]);
        }
        setTagInput("");
        return;
      }
      
      // Create new tag
      console.log('Creating new tag via API...');
      const response = await fetch(`${baseUrl}/api/v1/tags`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: tagName }),
      });

      console.log('API response status:', response.status);

      if (response.ok) {
        const newTag = await response.json();
        console.log('New tag created:', newTag);
        setAvailableTags([...availableTags, newTag]);
        setTags([...tags, newTag.id]);
        setTagInput("");
      } else if (response.status === 409) {
        // Tag exists, fetch it
        console.log('Tag exists (409), fetching...');
        const existingResponse = await fetch(`${baseUrl}/api/v1/tags/name/${encodeURIComponent(tagName)}`);
        if (existingResponse.ok) {
          const existingTag = await existingResponse.json();
          console.log('Fetched existing tag:', existingTag);
          setAvailableTags([...availableTags, existingTag]);
          setTags([...tags, existingTag.id]);
          setTagInput("");
        }
      }
    } catch (error) {
      console.error("Failed to create tag:", error);
    }
  };

  const removeTag = (tagId: number) => {
    setTags(tags.filter((id) => id !== tagId));
  };

  const getTagName = (tagId: number) => {
    return availableTags.find((tag) => tag.id === tagId)?.name || "";
  };

  // Fetch location suggestions from Google Places API
  const fetchLocationSuggestions = async (input: string) => {
    if (input.trim().length < 3) {
      setLocationSuggestions([]);
      return;
    }

    setIsGeocodingLocation(true);
    try {
      // Use Google Maps Geocoding API instead
      const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(input)}&key=${apiKey}`,
        { mode: 'cors' }
      );
      const data = await response.json();

      if (data.results && data.results.length > 0) {
        setLocationSuggestions(
          data.results.slice(0, 5).map((result: any) => ({
            description: result.formatted_address,
            place_id: result.place_id,
            lat: result.geometry.location.lat,
            lng: result.geometry.location.lng,
          }))
        );
      } else {
        setLocationSuggestions([]);
      }
    } catch (error) {
      console.error("Failed to fetch location suggestions:", error);
      setLocationSuggestions([]);
    } finally {
      setIsGeocodingLocation(false);
    }
  };

  // Select a location suggestion and set coordinates
  const selectLocation = async (description: string, lat: number, lng: number) => {
    setLocation(description);
    setLocationSuggestions([]);
    setLatitude(lat);
    setLongitude(lng);
  };

  // Debounce location input
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (location) {
        fetchLocationSuggestions(location);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [location]);

  const handleImageUpload = async (event: ChangeEvent<HTMLInputElement>) => {
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
        tags: tags,
        location_address: location.trim() || null,
        latitude: latitude,
        longitude: longitude,
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

      const created = await res.json();

      const newListing: Listing = {
        id: String(created.id ?? Date.now().toString()),
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
        poster_uid: user.id,
      };

      setMyListings((prev) => mergeUnique([newListing], prev));
      // Do not add the user's own new listing to the marketplace view for that user
      if (!user || newListing.poster_uid !== user.id) {
        setMarketListings((prev) => mergeUnique([newListing], prev));
      }
      setName("");
      setCompensation("");
      setCurrency("USD");
      setDeadline("");
      setDescription("");
      setLocation("");
      setLatitude(null);
      setLongitude(null);
      setLocationSuggestions([]);
      setImages([{ url: "", alt: "" }]);
      setTags([]);
      setTagInput("");
      setActiveTab("mine");
      setDialogOpen(false);
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "Failed to create listing",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Apply filters to marketplace listings
  const filteredMarketListings = marketListings.filter((listing) => {
    // Name filter
    if (nameFilter && !listing.name.toLowerCase().includes(nameFilter.toLowerCase())) {
      return false;
    }

    // Location filter (geocoded location with radius)
    if (locationCenter && locationFilter) {
      if (!listing.latitude || !listing.longitude) {
        return false; // Exclude listings without location data
      }
      
      const radius = parseFloat(locationRadius) || 25; // Default 25 km
      const distance = calculateDistance(
        locationCenter.lat,
        locationCenter.lng,
        listing.latitude,
        listing.longitude
      );
      
      if (distance > radius) {
        return false;
      }
    }

    // Tag filter - listing must have at least one of the selected tags
    if (selectedFilterTags.length > 0) {
      const listingTags = listing.tags || [];
      const hasMatchingTag = selectedFilterTags.some(tagId => listingTags.includes(tagId));
      if (!hasMatchingTag) {
        return false;
      }
    }

    return true;
  });

  const clearFilters = () => {
    setNameFilter("");
    setLocationFilter("");
    setLocationRadius("25");
    setLocationCenter(null);
    setSelectedFilterTags([]);
  };

  const toggleFilterTag = (tagId: number) => {
    setSelectedFilterTags(prev =>
      prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const hasActiveFilters = nameFilter || locationFilter || selectedFilterTags.length > 0;

  return (
    <div className="flex flex-col gap-4">
      {/* Filter Section - Only show on marketplace tab */}
      {activeTab === "marketplace" && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Filters</h2>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="text-xs"
              >
                Clear all
              </Button>
            )}
          </div>
          
          <div className="grid gap-4 md:grid-cols-3">
            {/* Name Filter */}
            <div className="space-y-2">
              <Label htmlFor="name-filter">Listing Name</Label>
              <Input
                id="name-filter"
                type="text"
                placeholder="Search by name..."
                value={nameFilter}
                onChange={(e) => setNameFilter(e.target.value)}
              />
            </div>

            {/* Location Filter */}
            <div className="space-y-2">
              <Label htmlFor="location-filter">
                Location
                {isGeocodingFilter && (
                  <span className="ml-2 text-xs text-muted-foreground">(searching...)</span>
                )}
              </Label>
              <Input
                id="location-filter"
                type="text"
                placeholder="e.g., New York, NY"
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
              />
              {locationFilter && (
                <div className="flex items-center gap-2">
                  <Label htmlFor="location-radius" className="text-xs whitespace-nowrap">
                    Within
                  </Label>
                  <Input
                    id="location-radius"
                    type="number"
                    placeholder="25"
                    value={locationRadius}
                    onChange={(e) => setLocationRadius(e.target.value)}
                    className="w-20 h-8 text-xs"
                    min="1"
                  />
                  <span className="text-xs text-muted-foreground">km</span>
                </div>
              )}
            </div>

            {/* Tags Filter */}
            {availableTags.length > 0 && (
              <div className="space-y-2">
                <Label>Tags</Label>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="w-full justify-between">
                      {selectedFilterTags.length === 0
                        ? "Select tags..."
                        : `${selectedFilterTags.length} tag${selectedFilterTags.length > 1 ? 's' : ''} selected`}
                      <span className="ml-2">▼</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-[400px] max-h-[300px] overflow-y-auto">
                    {availableTags.map((tag) => (
                      <DropdownMenuCheckboxItem
                        key={tag.id}
                        checked={selectedFilterTags.includes(tag.id)}
                        onCheckedChange={() => toggleFilterTag(tag.id)}
                      >
                        {tag.name}
                      </DropdownMenuCheckboxItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
                {selectedFilterTags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {selectedFilterTags.map((tagId) => {
                      const tag = availableTags.find((t) => t.id === tagId);
                      return tag ? (
                        <Badge
                          key={tag.id}
                          variant="default"
                          className="cursor-pointer"
                          onClick={() => toggleFilterTag(tag.id)}
                        >
                          {tag.name} ×
                        </Badge>
                      ) : null;
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
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
            <Button size="sm" onClick={() => setDialogOpen(true)}>
              New listing
            </Button>
          </DialogTrigger>
        </div>

        <DialogContent className="max-h-[90vh] overflow-y-auto">
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
              <Label htmlFor="location">
                Location
                {isGeocodingLocation && (
                  <span className="ml-2 text-xs text-muted-foreground">(searching...)</span>
                )}
              </Label>
              <div className="relative">
                <Input
                  id="location"
                  placeholder="Enter location (e.g., New York, NY)"
                  value={location}
                  onChange={(e) => {
                    setLocation(e.target.value);
                    if (!e.target.value.trim()) {
                      setLocationSuggestions([]);
                      setLatitude(null);
                      setLongitude(null);
                    }
                  }}
                />
                {locationSuggestions.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full rounded-md border bg-popover shadow-md max-h-48 overflow-y-auto">
                    {locationSuggestions.map((suggestion) => (
                      <button
                        key={suggestion.place_id}
                        type="button"
                        className="w-full px-3 py-2 text-left text-sm hover:bg-accent transition-colors"
                        onClick={() => selectLocation(suggestion.description, suggestion.lat, suggestion.lng)}
                      >
                        {suggestion.description}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {latitude && longitude && (
                <p className="text-[11px] text-muted-foreground">
                  📍 {latitude.toFixed(4)}, {longitude.toFixed(4)}
                </p>
              )}
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
                <p className="text-[11px] text-red-500">
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
                            alt={
                              image.alt ||
                              name ||
                              `Listing image ${index + 1}`
                            }
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
            <div className="space-y-2">
              <Label htmlFor="tags">Tags</Label>
              <div className="relative">
                <Input
                  id="tags"
                  placeholder="Add tags (e.g., design, development, marketing)"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={async (e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      e.stopPropagation();
                      const trimmedInput = tagInput.trim();
                      if (!trimmedInput) return;
                      
                      console.log('Enter pressed, input:', trimmedInput);
                      console.log('Filtered tags:', filteredTags);
                      
                      if (filteredTags.length > 0) {
                        addTag(filteredTags[0].id);
                      } else {
                        // Create new tag if it doesn't exist
                        await createAndAddTag(trimmedInput);
                      }
                    }
                  }}
                />
                {tagInput.trim() && (
                  <div className="absolute z-10 mt-1 w-full rounded-md border bg-popover shadow-md max-h-48 overflow-y-auto">
                    {filteredTags.length > 0 ? (
                      filteredTags.map((tag) => (
                        <button
                          key={tag.id}
                          type="button"
                          className="w-full px-3 py-2 text-left text-sm hover:bg-accent transition-colors"
                          onClick={(e) => {
                            e.preventDefault();
                            addTag(tag.id);
                          }}
                        >
                          {tag.name}
                        </button>
                      ))
                    ) : (
                      <button
                        type="button"
                        className="w-full px-3 py-2 text-left text-sm hover:bg-accent transition-colors text-primary"
                        onClick={async (e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          console.log('Create button clicked, tag:', tagInput.trim());
                          await createAndAddTag(tagInput.trim());
                        }}
                      >
                        Create "{tagInput.trim()}"
                      </button>
                    )}
                  </div>
                )}
              </div>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tagId) => (
                    <Badge
                      key={tagId}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() => removeTag(tagId)}
                    >
                      {getTagName(tagId)}
                      <span className="ml-1 text-xs">×</span>
                    </Badge>
                  ))}
                </div>
              )}
              <p className="text-[11px] text-muted-foreground">
                Type to search tags or press Enter to create a new one. Click a tag to remove it.
              </p>
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
        filteredMarketListings.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {hasActiveFilters ? "No listings match your filters." : "No listings yet. Be the first to create one."}
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredMarketListings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )
      ) : myListings.length === 0 ? (
        <Card className="flex items-center justify-center">
          <CardContent className="text-sm text-muted-foreground">
            You haven&apos;t created any listings yet.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {myListings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      )}
    </div>
  );
}

function ListingCard({ listing }: { listing: Listing }) {
  return (
    <Link href={`/market/${listing.id}`} className="block">
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
    </Link>
  );
}

