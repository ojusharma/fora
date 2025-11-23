"use client";

import { useEffect, useState } from "react";
import { useAdmin, PlatformStats } from "@/hooks/use-admin";
import { AdminGuard } from "@/components/admin/admin-guard";
import { AdminNav } from "@/components/admin/admin-nav";
import { StatCard } from "@/components/admin/stat-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function AdminDashboard() {
  const { getPlatformStats, loading, error } = useAdmin();
  const [stats, setStats] = useState<PlatformStats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getPlatformStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to fetch stats:", err);
      }
    };

    fetchStats();
  }, []);

  return (
    <AdminGuard>
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto py-8 px-4 max-w-7xl">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
              <p className="text-gray-400">
                Manage users, listings, and platform settings
              </p>
            </div>
            <Link href="/">
              <Button variant="outline" className="border-gray-700 text-white hover:bg-gray-800">
                Back to Home
              </Button>
            </Link>
          </div>

          <AdminNav />

        {error && (
          <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded mb-6">
            <p className="font-medium">Error loading dashboard</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {loading && !stats ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
          </div>
        ) : stats ? (
          <>
            {/* Platform Statistics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
              <StatCard
                title="Total Users"
                value={stats.total_users}
                description="All registered users"
              />
              <StatCard
                title="Total Listings"
                value={stats.total_listings}
                description="All created listings"
              />
              <StatCard
                title="Open Listings"
                value={stats.open_listings}
                description="Currently available"
              />
              <StatCard
                title="Applications"
                value={stats.total_applications}
                description="Total applications"
              />
            </div>

            {/* User Role Distribution */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-8">
              <StatCard
                title="Admin Users"
                value={stats.admin_users}
                description="Platform administrators"
              />
              <StatCard
                title="Moderators"
                value={stats.moderator_users}
                description="Content moderators"
              />
              <StatCard
                title="Regular Users"
                value={stats.regular_users}
                description="Standard users"
              />
            </div>

            {/* Listing Status Distribution */}
            <div className="grid gap-4 md:grid-cols-2 mb-8">
              <Card className="bg-gray-900 border-gray-800">
                <CardHeader>
                  <CardTitle className="text-white">Listing Completion Rate</CardTitle>
                  <CardDescription className="text-gray-400">Completed vs Total Listings</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-white">
                    {stats.total_listings > 0
                      ? Math.round((stats.completed_listings / stats.total_listings) * 100)
                      : 0}
                    %
                  </div>
                  <p className="text-sm text-gray-400 mt-2">
                    {stats.completed_listings} completed out of {stats.total_listings} total
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-800">
                <CardHeader>
                  <CardTitle className="text-white">Applications Per Listing</CardTitle>
                  <CardDescription className="text-gray-400">Average application rate</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-white">
                    {stats.open_listings > 0
                      ? (stats.total_applications / stats.open_listings).toFixed(1)
                      : 0}
                  </div>
                  <p className="text-sm text-gray-400 mt-2">
                    Average applications per open listing
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Quick Actions</CardTitle>
                <CardDescription className="text-gray-400">Common administrative tasks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                  <Link href="/admin/users">
                    <Button variant="outline" className="w-full border-gray-700 text-white hover:bg-gray-800">
                      Manage Users
                    </Button>
                  </Link>
                  <Link href="/admin/listings">
                    <Button variant="outline" className="w-full border-gray-700 text-white hover:bg-gray-800">
                      Manage Listings
                    </Button>
                  </Link>
                  <Link href="/admin/ml">
                    <Button variant="outline" className="w-full border-gray-700 text-white hover:bg-gray-800">
                      ML Training
                    </Button>
                  </Link>
                  <Link href="/market">
                    <Button variant="outline" className="w-full border-gray-700 text-white hover:bg-gray-800">
                      View Market
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </>
        ) : null}
        </div>
      </div>
    </AdminGuard>
  );
}
