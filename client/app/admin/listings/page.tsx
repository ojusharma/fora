"use client";

import { useEffect, useState } from "react";
import { useAdmin, Listing } from "@/hooks/use-admin";
import { AdminGuard } from "@/components/admin/admin-guard";
import { AdminNav } from "@/components/admin/admin-nav";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";

export default function AdminListingsPage() {
  const { getListings, updateListing, deleteListing, loading, error } = useAdmin();
  const [listings, setListings] = useState<Listing[]>([]);
  const [filteredListings, setFilteredListings] = useState<Listing[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState<Partial<Listing>>({});

  useEffect(() => {
    fetchListings();
  }, []);

  useEffect(() => {
    filterListings();
  }, [listings, searchQuery, statusFilter]);

  const fetchListings = async () => {
    try {
      const data = await getListings();
      setListings(data);
    } catch (err) {
      console.error("Failed to fetch listings:", err);
    }
  };

  const filterListings = () => {
    let filtered = listings;

    // Filter by status
    if (statusFilter !== "all") {
      filtered = filtered.filter((listing) => listing.status === statusFilter);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(
        (listing) =>
          listing.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          listing.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          listing.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredListings(filtered);
  };

  const handleEditListing = (listing: Listing) => {
    setSelectedListing(listing);
    setEditFormData({
      name: listing.name,
      description: listing.description,
      status: listing.status,
      compensation: listing.compensation,
      location_address: listing.location_address,
    });
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedListing) return;

    try {
      await updateListing(selectedListing.id, editFormData);
      await fetchListings();
      setEditDialogOpen(false);
      setSelectedListing(null);
    } catch (err) {
      console.error("Failed to update listing:", err);
    }
  };

  const handleChangeStatus = async (
    listing: Listing,
    newStatus: "open" | "in_progress" | "completed" | "cancelled"
  ) => {
    try {
      await updateListing(listing.id, { status: newStatus });
      await fetchListings();
    } catch (err) {
      console.error("Failed to change status:", err);
    }
  };

  const handleDeleteListing = async () => {
    if (!selectedListing) return;

    try {
      await deleteListing(selectedListing.id);
      await fetchListings();
      setDeleteDialogOpen(false);
      setSelectedListing(null);
    } catch (err) {
      console.error("Failed to delete listing:", err);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case "open":
        return "bg-green-500 text-white";
      case "in_progress":
        return "bg-blue-500 text-white";
      case "completed":
        return "bg-gray-500 text-white";
      case "cancelled":
        return "bg-red-500 text-white";
      default:
        return "bg-gray-400 text-white";
    }
  };

  return (
    <AdminGuard>
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto py-8 px-4 max-w-7xl">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Listing Management</h1>
              <p className="text-gray-400">
                View and manage all platform listings
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
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Filters</CardTitle>
            <CardDescription>Search and filter listings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="search">Search</Label>
                <Input
                  id="search"
                  placeholder="Search by name, description, or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="statusFilter">Status Filter</Label>
                <select
                  id="statusFilter"
                  className="w-full px-3 py-2 border rounded-md"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>
            <div className="mt-4 text-sm text-muted-foreground">
              Showing {filteredListings.length} of {listings.length} listings
            </div>
          </CardContent>
        </Card>

        {loading && listings.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
          </div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Listings ({filteredListings.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium">Name</th>
                      <th className="text-left py-3 px-4 font-medium">Status</th>
                      <th className="text-left py-3 px-4 font-medium">Compensation</th>
                      <th className="text-left py-3 px-4 font-medium">Location</th>
                      <th className="text-left py-3 px-4 font-medium">Created</th>
                      <th className="text-right py-3 px-4 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredListings.map((listing) => (
                      <tr key={listing.id} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium max-w-xs truncate">
                              {listing.name}
                            </div>
                            <div className="text-xs text-muted-foreground truncate max-w-xs">
                              {listing.description || "No description"}
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge className={getStatusBadgeColor(listing.status)}>
                            {listing.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          {listing.compensation
                            ? `$${listing.compensation.toFixed(2)}`
                            : "—"}
                        </td>
                        <td className="py-3 px-4 text-sm max-w-xs truncate">
                          {listing.location_address || "—"}
                        </td>
                        <td className="py-3 px-4 text-sm">
                          {listing.created_at
                            ? new Date(listing.created_at).toLocaleDateString()
                            : "—"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                ⋮
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleEditListing(listing)}>
                                ✏️ Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleChangeStatus(listing, "open")}
                                disabled={listing.status === "open"}
                              >
                                🔓 Mark Open
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleChangeStatus(listing, "in_progress")}
                                disabled={listing.status === "in_progress"}
                              >
                                ⏳ Mark In Progress
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleChangeStatus(listing, "completed")}
                                disabled={listing.status === "completed"}
                              >
                                ✅ Mark Completed
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleChangeStatus(listing, "cancelled")}
                                disabled={listing.status === "cancelled"}
                              >
                                ❌ Mark Cancelled
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-red-600"
                                onClick={() => {
                                  setSelectedListing(listing);
                                  setDeleteDialogOpen(true);
                                }}
                              >
                                🗑️ Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredListings.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    No listings found
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Edit Listing Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit Listing</DialogTitle>
              <DialogDescription>
                Update listing information
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4 max-h-[60vh] overflow-y-auto">
              <div>
                <Label htmlFor="edit-name">Name</Label>
                <Input
                  id="edit-name"
                  value={editFormData.name || ""}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, name: e.target.value })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-description">Description</Label>
                <textarea
                  id="edit-description"
                  className="w-full px-3 py-2 border rounded-md min-h-[100px]"
                  value={editFormData.description || ""}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, description: e.target.value })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-status">Status</Label>
                <select
                  id="edit-status"
                  className="w-full px-3 py-2 border rounded-md"
                  value={editFormData.status || "open"}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, status: e.target.value })
                  }
                >
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div>
                <Label htmlFor="edit-compensation">Compensation</Label>
                <Input
                  id="edit-compensation"
                  type="number"
                  step="0.01"
                  value={editFormData.compensation || 0}
                  onChange={(e) =>
                    setEditFormData({
                      ...editFormData,
                      compensation: parseFloat(e.target.value),
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="edit-location">Location Address</Label>
                <Input
                  id="edit-location"
                  value={editFormData.location_address || ""}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, location_address: e.target.value })
                  }
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveEdit}>Save Changes</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Listing Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Listing</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this listing? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            {selectedListing && (
              <div className="py-4">
                <p className="font-medium">{selectedListing.name}</p>
                <p className="text-sm text-muted-foreground">{selectedListing.id}</p>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDeleteListing}>
                Delete Listing
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        </div>
      </div>
    </AdminGuard>
  );
}
