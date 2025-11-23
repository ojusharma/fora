"use client";

import { createClient } from "@/lib/client";
import { useState, useEffect } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Types
export interface User {
  uid: string;
  dob?: string;
  phone?: string;
  role?: string;
  credits?: number;
  last_updated?: string;
  latitude?: number;
  longitude?: number;
  display_name?: string;
  user_rating?: number;
}

export interface Listing {
  id: string;
  name: string;
  description?: string;
  images?: any;
  poster_uid: string;
  assignee_uid?: string;
  status: string;
  location_address?: string;
  latitude?: number;
  longitude?: number;
  deadline?: string;
  compensation?: number;
  last_posted?: string;
  created_at?: string;
  updated_at?: string;
  poster_rating?: number;
  assignee_rating?: number;
  tags?: number[];
}

export interface PlatformStats {
  total_users: number;
  total_listings: number;
  open_listings: number;
  completed_listings: number;
  total_applications: number;
  admin_users: number;
  moderator_users: number;
  regular_users: number;
}

export interface UserStats {
  uid: string;
  display_name?: string;
  email?: string;
  role: string;
  credits: number;
  total_listings_posted: number;
  total_listings_completed: number;
  total_applications: number;
  average_rating?: number;
  account_created?: string;
}

export function useAdmin() {
  const supabase = createClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const makeAdminRequest = async (
    endpoint: string,
    options?: RequestInit
  ): Promise<any> => {
    setLoading(true);
    setError(null);

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${API_BASE_URL}/admin${endpoint}`, {
        ...options,
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.detail || `Request failed with status ${response.status}: ${response.statusText}`;
        console.error("Admin API Error:", {
          status: response.status,
          statusText: response.statusText,
          endpoint,
          error: errorData
        });
        throw new Error(errorMsg);
      }

      return await response.json();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // User Management
  const getUsers = async (params?: {
    skip?: number;
    limit?: number;
    role?: string;
  }): Promise<User[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
    if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));
    if (params?.role) queryParams.append("role", params.role);

    const query = queryParams.toString();
    return makeAdminRequest(`/users${query ? `?${query}` : ""}`);
  };

  const getUser = async (uid: string): Promise<User> => {
    return makeAdminRequest(`/users/${uid}`);
  };

  const updateUser = async (
    uid: string,
    data: Partial<User>
  ): Promise<User> => {
    return makeAdminRequest(`/users/${uid}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  };

  const changeUserRole = async (
    uid: string,
    newRole: "user" | "moderator" | "admin"
  ): Promise<User> => {
    return makeAdminRequest(`/users/${uid}/role`, {
      method: "PATCH",
      body: JSON.stringify({ new_role: newRole }),
    });
  };

  const deleteUser = async (uid: string): Promise<any> => {
    return makeAdminRequest(`/users/${uid}`, {
      method: "DELETE",
    });
  };

  // Listing Management
  const getListings = async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<Listing[]> => {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append("skip", String(params.skip));
    if (params?.limit !== undefined) queryParams.append("limit", String(params.limit));
    if (params?.status) queryParams.append("status", params.status);

    const query = queryParams.toString();
    return makeAdminRequest(`/listings${query ? `?${query}` : ""}`);
  };

  const getListing = async (id: string): Promise<Listing> => {
    return makeAdminRequest(`/listings/${id}`);
  };

  const createListing = async (data: any): Promise<Listing> => {
    return makeAdminRequest(`/listings`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  };

  const updateListing = async (
    id: string,
    data: Partial<Listing>
  ): Promise<Listing> => {
    return makeAdminRequest(`/listings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  };

  const deleteListing = async (id: string): Promise<any> => {
    return makeAdminRequest(`/listings/${id}`, {
      method: "DELETE",
    });
  };

  // Statistics
  const getPlatformStats = async (): Promise<PlatformStats> => {
    return makeAdminRequest(`/stats`);
  };

  const getUserStats = async (uid: string): Promise<UserStats> => {
    return makeAdminRequest(`/stats/users/${uid}`);
  };

  // ML Management
  const triggerMLTraining = async (
    taskType: "daily" | "hourly" | "frequent"
  ): Promise<any> => {
    return makeAdminRequest(`/train-ml`, {
      method: "POST",
      body: JSON.stringify({ task_type: taskType }),
    });
  };

  const generateSampleData = async (): Promise<any> => {
    return makeAdminRequest(`/generate-sample-data`, {
      method: "POST",
    });
  };

  return {
    loading,
    error,
    // User management
    getUsers,
    getUser,
    updateUser,
    changeUserRole,
    deleteUser,
    // Listing management
    getListings,
    getListing,
    createListing,
    updateListing,
    deleteListing,
    // Statistics
    getPlatformStats,
    getUserStats,
    // ML management
    triggerMLTraining,
    generateSampleData,
  };
}

// Hook to check if current user is admin
export function useIsAdmin() {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  useEffect(() => {
    const checkAdmin = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
          setIsAdmin(false);
          setLoading(false);
          return;
        }

        // Fetch user profile to check role
        const { data: profile } = await supabase
          .from("user_profiles")
          .select("role")
          .eq("uid", user.id)
          .single();

        setIsAdmin(profile?.role === "admin");
      } catch (error) {
        console.error("Error checking admin status:", error);
        setIsAdmin(false);
      } finally {
        setLoading(false);
      }
    };

    checkAdmin();
  }, [supabase]);

  return { isAdmin, loading };
}
