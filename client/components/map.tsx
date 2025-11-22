'use client'
import React, { useEffect, useState } from 'react';
import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api';
import Link from 'next/link';

const containerStyle = {
  width: '100%',
  height: '600px'
};

const center = {
  lat: 19.118942598534247,
  lng: 72.90893209845882
};

type Listing = {
  id: string;
  name: string;
  description: string;
  latitude: number;
  longitude: number;
  compensation: number;
  currency: string;
};

const GoogleMapComponent = () => {
  const [listings, setListings] = useState<Listing[]>([]);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [mapCenter, setMapCenter] = useState(center);

  useEffect(() => {
    const fetchListings = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/v1/listings`);
        const data = await response.json();
        
        // Filter listings that have coordinates
        const listingsWithCoords = data.filter(
          (listing: any) => listing.latitude && listing.longitude
        ).map((listing: any) => ({
          id: listing.id,
          name: listing.name,
          description: listing.description,
          latitude: listing.latitude,
          longitude: listing.longitude,
          compensation: listing.compensation,
          currency: listing.currency || 'USD',
        }));
        
        setListings(listingsWithCoords);
        
        // Center map on first listing if available
        if (listingsWithCoords.length > 0) {
          setMapCenter({
            lat: listingsWithCoords[0].latitude,
            lng: listingsWithCoords[0].longitude,
          });
        }
      } catch (error) {
        console.error('Failed to fetch listings:', error);
      }
    };

    fetchListings();
  }, []);

  return (
    <LoadScript googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || ''}>
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={mapCenter}
        zoom={listings.length > 0 ? 12 : 3}
      >
        {listings.map((listing) => (
          <Marker
            key={listing.id}
            position={{ lat: listing.latitude, lng: listing.longitude }}
            onClick={() => setSelectedListing(listing)}
          />
        ))}
        
        {selectedListing && (
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
                  From {selectedListing.currency} {selectedListing.compensation.toLocaleString()}
                </p>
              )}
              <Link 
                href={`/market/${selectedListing.id}`}
                className="text-xs text-blue-600 hover:underline"
              >
                View details →
              </Link>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
    </LoadScript>
  );
};

export default GoogleMapComponent;