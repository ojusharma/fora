"use client";
console.log("MAP PAGE MOUNTED");

import { AuthButton } from "@/components/auth-button";
import Link from "next/link";
import { useEffect, useState, useRef, useCallback, Suspense } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from '@react-google-maps/api';
import { NotificationBell } from "@/components/notification-bell";

type Listing = {
  id: string;
  name: string;
  description: string;
  latitude: number | null;
  longitude: number | null;
  location_address: string | null;
  compensation: number;
  status: string;
  tags?: number[];
};

const mapContainerStyle = { width: "100%", height: "100%" };

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

export default function MapPage() {
  const router = useRouter();

  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [listings, setListings] = useState<Listing[]>([]);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [hoveredListing, setHoveredListing] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState({ lat: 40.7128, lng: -74.0060 });
  
  const [nameFilter, setNameFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [locationRadius, setLocationRadius] = useState("50"); 
  const [radiusFilter, setRadiusFilter] = useState("");
  const [locationCenter, setLocationCenter] = useState<{ lat: number; lng: number } | null>(null);
  const [radiusCenter, setRadiusCenter] = useState<{ lat: number; lng: number } | null>(null);
  const [isGeocodingLocation, setIsGeocodingLocation] = useState(false);
  const [isGeocodingRadius, setIsGeocodingRadius] = useState(false);
  const [selectedFilterTags, setSelectedFilterTags] = useState<number[]>([]);
  const [availableTags, setAvailableTags] = useState<Array<{ id: number; name: string }>>([]);

  const cachedListings = useRef<Listing[] | null>(null);

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
  });

  const mapRef = useRef<google.maps.Map | null>(null);
  const onMapLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
  }, []);

  useEffect(() => {
    async function checkAuth() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.push("/auth/login");
      }
      setIsAuthChecked(true);
    }
    checkAuth();

    // Fetch available tags
    async function fetchTags() {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/v1/tags/`);
        if (response.ok) {
          const tags = await response.json();
          setAvailableTags(tags);
        }
      } catch (error) {
        console.error("Failed to fetch tags:", error);
      }
    }
    fetchTags();
  }, [router]);

  useEffect(() => {
    async function fetchListings() {
      try {
        const cached = localStorage.getItem('map_listings');
        if (cached) {
          const parsedListings = JSON.parse(cached);
          setListings(parsedListings);
          const withCoords = parsedListings.filter((l: Listing) => l.latitude && l.longitude);
          if (withCoords.length > 0) {
            setMapCenter({
              lat: withCoords[0].latitude!,
              lng: withCoords[0].longitude!,
            });
          }
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/v1/listings/`, { cache: "no-store" });
        const data = await response.json();

        console.log('Fetched listings:', data.length);
        localStorage.setItem('map_listings', JSON.stringify(data));
        setListings(data);

        const withCoords = data.filter((l: Listing) => l.latitude && l.longitude);
        if (withCoords.length > 0) {
          setMapCenter({
            lat: withCoords[0].latitude!,
            lng: withCoords[0].longitude!,
          });
        }
      } catch (error) {
        console.error("Failed to fetch listings:", error);
      }
    }

    if (isLoaded) {
      fetchListings();
    }
  }, [isLoaded]);

  useEffect(() => {
    async function geocodeLocation() {
      if (!locationFilter || !isLoaded || !window.google) {
        setLocationCenter(null);
        return;
      }
      
      setIsGeocodingLocation(true);
      const geocoder = new window.google.maps.Geocoder();
      
      try {
        const result = await geocoder.geocode({ address: locationFilter });
        if (result.results && result.results[0]) {
          const location = result.results[0].geometry.location;
          const center = {
            lat: location.lat(),
            lng: location.lng(),
          };
          setLocationCenter(center);
          setMapCenter(center); 
        } else {
          setLocationCenter(null);
        }
      } catch (error) {
        console.error("Location geocoding error:", error);
        setLocationCenter(null);
      } finally {
        setIsGeocodingLocation(false);
      }
    }

    const timer = setTimeout(() => {
      geocodeLocation();
    }, 500);

    return () => clearTimeout(timer);
  }, [locationFilter, isLoaded]);

  useEffect(() => {
    async function geocodeRadiusCenter() {
      if (!radiusFilter || !isLoaded || !window.google) return;
      
      setIsGeocodingRadius(true);
      const geocoder = new window.google.maps.Geocoder();
      
      try {
        const result = await geocoder.geocode({ address: radiusFilter });
        if (result.results && result.results[0]) {
          const location = result.results[0].geometry.location;
          setRadiusCenter({
            lat: location.lat(),
            lng: location.lng(),
          });
        } else {
          setRadiusCenter(null);
        }
      } catch (error) {
        console.error("Geocoding error:", error);
        setRadiusCenter(null);
      } finally {
        setIsGeocodingRadius(false);
      }
    }

    const timer = setTimeout(() => {
      geocodeRadiusCenter();
    }, 500);

    return () => clearTimeout(timer);
  }, [radiusFilter, isLoaded]);

  // Filter listings based on all filters
  const filteredListings = listings.filter((listing) => {
    // Must have coordinates
    if (!listing.latitude || !listing.longitude) return false;

    if (nameFilter && !listing.name.toLowerCase().includes(nameFilter.toLowerCase())) {
      return false;
    }

    // Location filter (geocoded location with radius)
    if (locationCenter && locationFilter) {
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

    // Radius filter
    if (radiusCenter && radiusFilter) {
      const [radiusValue, unit] = radiusFilter.split(' ').slice(-2);
      const radius = parseFloat(radiusValue);
      
      if (!isNaN(radius)) {
        const distance = calculateDistance(
          radiusCenter.lat,
          radiusCenter.lng,
          listing.latitude,
          listing.longitude
        );
        
        const distanceInUnit = unit?.toLowerCase() === 'mi' ? distance * 0.621371 : distance;
        
        if (distanceInUnit > radius) {
          return false;
        }
      }
    }

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
    setRadiusFilter("");
    setRadiusCenter(null);
    setSelectedFilterTags([]);
  };

  const toggleFilterTag = (tagId: number) => {
    setSelectedFilterTags(prev =>
      prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const hasActiveFilters = nameFilter || locationFilter || radiusFilter || selectedFilterTags.length > 0;

  useEffect(() => {
    if (filteredListings.length > 0 && (nameFilter || radiusFilter)) {
      const firstListing = filteredListings[0];
      if (firstListing.latitude && firstListing.longitude) {
        setMapCenter({
          lat: firstListing.latitude,
          lng: firstListing.longitude,
        });
      }
    }
  }, [filteredListings.length, nameFilter, radiusFilter]);

  if (!isAuthChecked) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </main>
    );
  }

  const listingsWithCoords = filteredListings;
  
  console.log('RENDER - listings:', listings.length, 'filtered:', filteredListings.length, 'isLoaded:', isLoaded);

  return (
    <div className="h-screen flex flex-col">
      {/* NAVBAR */}
      <nav className="w-full flex justify-center border-b h-16 flex-shrink-0">
        <div className="w-full max-w-none flex justify-between items-center p-3 px-5 text-sm">
          <div className="flex gap-5 items-center font-semibold">
            <Link href="/">fora</Link>
            <Link href="/market">marketplace</Link>
            <Link href="/map">map</Link>
            <Link href="/chats">chats</Link>
          </div>
          <div className="flex items-center gap-4">
            <Suspense>
              <NotificationBell />
            </Suspense>
          
            <AuthButton />
          </div>
        </div>
      </nav>

      {/* MAIN LAYOUT */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT LISTING PANEL */}
        <div className="w-[480px] flex-shrink-0 border-r overflow-y-auto">
          <div className="p-4">
            {/* FILTER SECTION */}
            <div className="mb-6 p-4 border rounded-lg bg-card space-y-4">
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
                  {isGeocodingLocation && (
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

            <h1 className="text-xl font-semibold mb-1">
              {listingsWithCoords.length} {listingsWithCoords.length === 1 ? "listing" : "listings"} found
            </h1>
            <p className="text-sm text-muted-foreground mb-4">
              Browse opportunities on the map
            </p>

            <div className="space-y-3">
              {filteredListings.map((listing) => (
                <Card
                  key={listing.id}
                  className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                    hoveredListing === listing.id ? "ring-2 ring-primary" : ""
                  } ${
                    selectedListing?.id === listing.id ? "ring-2 ring-primary bg-accent" : ""
                  }`}
                  onMouseEnter={() => setHoveredListing(listing.id)}
                  onMouseLeave={() => setHoveredListing(null)}
                  onClick={() => {
                    if (listing.latitude && listing.longitude) {
                      setSelectedListing(listing);
                      setMapCenter({ lat: listing.latitude, lng: listing.longitude });
                    } else {
                      router.push(`/market/${listing.id}`);
                    }
                  }}
                >
                  <div className="space-y-2">
                    <h3 className="font-semibold text-base line-clamp-1">{listing.name}</h3>

                    {listing.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {listing.description}
                      </p>
                    )}

                    {listing.compensation && (
                      <p className="text-sm font-semibold">
                        ${listing.compensation.toLocaleString()}
                      </p>
                    )}

                    {listing.location_address && (
                      <p className="text-xs text-muted-foreground line-clamp-1">
                        📍 {listing.location_address}
                      </p>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>

        {/* MAP */}
        <div className="flex-1 relative">
          {!isLoaded ? (
            <div className="w-full h-full flex items-center justify-center">
              <p>Loading map…</p>
            </div>
          ) : (
            <GoogleMap
              key={listingsWithCoords.length}
              mapContainerStyle={mapContainerStyle}
              center={mapCenter}
              zoom={12}
              onLoad={onMapLoad}
              options={{
                streetViewControl: false,
                mapTypeControl: false,
              }}
            >
              {/* MARKERS */}
              {listingsWithCoords.map((listing) => {
                console.log('Rendering marker:', listing.name, listing.latitude, listing.longitude);
                return (
                  <Marker
                    key={listing.id}
                    position={{ lat: listing.latitude!, lng: listing.longitude! }}
                    onClick={() => setSelectedListing(listing)}
                    icon={{
                      path: window.google?.maps?.SymbolPath?.CIRCLE,
                      scale:
                        hoveredListing === listing.id ||
                        selectedListing?.id === listing.id
                          ? 12
                          : 8,
                      fillColor: "#AA4A44",
                      fillOpacity: 1,
                      strokeColor: "#ffffff",
                      strokeWeight: 2,
                    }}
                  />
                );
              })}

              {/* Radius Center Marker */}
              {radiusCenter && (
                <Marker
                  position={radiusCenter}
                  icon={{
                    path: window.google?.maps?.SymbolPath?.CIRCLE,
                    scale: 10,
                    fillColor: "#ef4444",
                    fillOpacity: 0.8,
                    strokeColor: "#ffffff",
                    strokeWeight: 2,
                  }}
                />
              )}

              {locationCenter && (
                <Marker
                  position={locationCenter}
                  icon={{
                    path: window.google?.maps?.SymbolPath?.CIRCLE,
                    scale: 10,
                    fillColor: "#22c55e",
                    fillOpacity: 0.8,
                    strokeColor: "#ffffff",
                    strokeWeight: 2,
                  }}
                />
              )}

              {selectedListing && selectedListing.latitude && selectedListing.longitude && (
                <InfoWindow
                  position={{
                    lat: selectedListing.latitude,
                    lng: selectedListing.longitude,
                  }}
                  onCloseClick={() => setSelectedListing(null)}
                >
                  <div className="p-3 max-w-sm">
                    <h3 className="font-semibold text-base mb-2 text-black">{selectedListing.name}</h3>

                    {selectedListing.description && (
                      <p className="text-sm text-gray-700 mb-3">
                        {selectedListing.description}
                      </p>
                    )}

                    {selectedListing.compensation && (
                      <p className="text-sm font-semibold mb-2 text-black">
                        ${selectedListing.compensation.toLocaleString()}
                      </p>
                    )}

                    {selectedListing.location_address && (
                      <p className="text-sm text-gray-600 mb-3">
                        📍 {selectedListing.location_address}
                      </p>
                    )}
                  </div>
                </InfoWindow>
              )}
            </GoogleMap>
          )}
        </div>
      </div>
    </div>
  );
}
