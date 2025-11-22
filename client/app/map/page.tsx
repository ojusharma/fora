"use client";

import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import Link from "next/link";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api';

type Listing = {
  id: string;
  name: string;
  description: string;
  latitude: number | null;
  longitude: number | null;
  location_address: string | null;
  compensation: number;
  status: string;
};

const mapContainerStyle = {
  width: '100%',
  height: '100%'
};

export default function MapPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [listings, setListings] = useState<Listing[]>([]);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [hoveredListing, setHoveredListing] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState({ lat: 40.7128, lng: -74.0060 });
  const router = useRouter();

  useEffect(() => {
    async function checkAuth() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        router.push("/auth/login");
        return;
      }
      
      setIsLoading(false);
    }
    
    checkAuth();
  }, [router]);

  useEffect(() => {
    const fetchListings = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/v1/listings`);
        const data = await response.json();
        
        setListings(data);
        const firstWithCoords = data.find((l: Listing) => l.latitude && l.longitude);
        if (firstWithCoords) {
          setMapCenter({
            lat: firstWithCoords.latitude!,
            lng: firstWithCoords.longitude!,
          });
        }
      } catch (error) {
        console.error('Failed to fetch listings:', error);
      }
    };

    if (!isLoading) {
      fetchListings();
    }
  }, [isLoading]);

  if (isLoading) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center">
        <p>Loading...</p>
      </main>
    );
  }

  const listingsWithCoords = listings.filter(l => l.latitude && l.longitude);

  return (
    <div className="h-screen flex flex-col">
      <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16 flex-shrink-0">
        <div className="w-full max-w-none flex justify-between items-center p-3 px-5 text-sm">
          <div className="flex gap-5 items-center font-semibold">
            <Link href={"/"}>fora</Link>
            <Link href={"/market"}>marketplace</Link>
            <Link href={"/map"}>map</Link>
          </div>
          <AuthButton />
        </div>
      </nav>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-[480px] flex-shrink-0 border-r overflow-y-auto">
          <div className="p-4">
            <div className="mb-4">
              <h1 className="text-xl font-semibold mb-1">
                {listings.length} {listings.length === 1 ? 'listing' : 'listings'} found
              </h1>
              <p className="text-sm text-muted-foreground">
                Browse opportunities on the map
              </p>
            </div>

            <div className="space-y-3">
              {listings.map((listing) => (
                <Card
                  key={listing.id}
                  className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                    hoveredListing === listing.id ? 'ring-2 ring-primary' : ''
                  } ${
                    selectedListing?.id === listing.id ? 'ring-2 ring-primary bg-accent' : ''
                  }`}
                  onClick={() => {
                    if (listing.latitude && listing.longitude) {
                      setSelectedListing(listing);
                      setMapCenter({ lat: listing.latitude, lng: listing.longitude });
                    } else {
                      router.push(`/market/${listing.id}`);
                    }
                  }}
                  onMouseEnter={() => setHoveredListing(listing.id)}
                  onMouseLeave={() => setHoveredListing(null)}
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-base line-clamp-1">{listing.name}</h3>
                      <Badge variant="secondary" className="flex-shrink-0">
                        {listing.status}
                      </Badge>
                    </div>
                    
                    {listing.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {listing.description} 
                      </p>
                    )}
                    
                    {listing.compensation && (
                      <div className="text-sm font-semibold">
                        ${listing.compensation.toLocaleString()}
                      </div>
                    )}
                    
                    {listing.location_address && (
                      <div className="flex items-start gap-1 text-xs text-muted-foreground">
                        <span>📍</span>
                        <span className="line-clamp-1">{listing.location_address}</span>
                      </div>
                    )}
                    {!listing.latitude && !listing.longitude && (
                      <div className="text-xs text-muted-foreground italic">
                        No map location
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
        <div className="flex-1 relative">
          <LoadScript googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || ''}>
            <GoogleMap
              mapContainerStyle={mapContainerStyle}
              center={mapCenter}
              zoom={12}
              options={{
                streetViewControl: false,
                mapTypeControl: false,
              }}
            >
              {listingsWithCoords.map((listing) => (
                <Marker
                  key={listing.id}
                  position={{ lat: listing.latitude!, lng: listing.longitude! }}
                  onClick={() => setSelectedListing(listing)}
                  icon={{
                    path: window.google?.maps?.SymbolPath?.CIRCLE,
                    scale: hoveredListing === listing.id || selectedListing?.id === listing.id ? 12 : 8,
                    fillColor: selectedListing?.id === listing.id ? '#2563eb' : '#3b82f6',
                    fillOpacity: 1,
                    strokeColor: '#ffffff',
                    strokeWeight: 2,
                  }}
                />
              ))}
              
              {selectedListing && selectedListing.latitude && selectedListing.longitude && (
                <InfoWindow
                  position={{ lat: selectedListing.latitude, lng: selectedListing.longitude }}
                  onCloseClick={() => setSelectedListing(null)}
                >
                  <div className="p-2 max-w-xs">
                    <h3 className="font-semibold text-sm mb-1">{selectedListing.name}</h3>
                    {selectedListing.description && (
                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                        {selectedListing.description}
                      </p>
                    )}
                    {selectedListing.compensation && (
                      <p className="text-xs font-medium mb-2">
                        ${selectedListing.compensation.toLocaleString()}
                      </p>
                    )}
                    {selectedListing.location_address && (
                      <p className="text-xs text-gray-600 mb-2 line-clamp-1">
                        📍 {selectedListing.location_address}
                      </p>
                    )}
                    <Link 
                      href={`/market/${selectedListing.id}`}
                      className="text-xs text-blue-600 hover:underline font-medium"
                    >
                      View details →
                    </Link>
                  </div>
                </InfoWindow>
              )}
            </GoogleMap>
          </LoadScript>
        </div>
      </div>
    </div>
  );
}
