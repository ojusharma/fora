"use client";

import { useEffect, useState } from "react";
import { AdminGuard } from "@/components/admin/admin-guard";
import { AdminNav } from "@/components/admin/admin-nav";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Edit, Trash2, Gift } from "lucide-react";
import Link from "next/link";
import { createClient } from "@/lib/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Reward {
  id: string;
  title: string;
  description?: string;
  credits_required: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface RewardFormData {
  title: string;
  description: string;
  credits_required: number;
  is_active: boolean;
}

export default function AdminRewardsPage() {
  const supabase = createClient();
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingReward, setEditingReward] = useState<Reward | null>(null);
  const [formData, setFormData] = useState<RewardFormData>({
    title: "",
    description: "",
    credits_required: 0,
    is_active: true,
  });

  useEffect(() => {
    fetchRewards();
  }, []);

  const fetchRewards = async () => {
    try {
      setLoading(true);
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Not authenticated");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/rewards/admin/all?include_inactive=true`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch rewards");
      }

      const data = await response.json();
      setRewards(data);
      setError(null);
    } catch (err: any) {
      console.error("Error fetching rewards:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReward = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Not authenticated");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/rewards/admin`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create reward: ${response.status}`);
      }

      await fetchRewards();
      setIsCreateOpen(false);
      setFormData({
        title: "",
        description: "",
        credits_required: 0,
        is_active: true,
      });
    } catch (err: any) {
      console.error("Error creating reward:", err);
      setError(err.message);
    }
  };

  const handleEditReward = async () => {
    if (!editingReward) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Not authenticated");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/rewards/admin/${editingReward.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to update reward: ${response.status}`);
      }

      await fetchRewards();
      setIsEditOpen(false);
      setEditingReward(null);
      setFormData({
        title: "",
        description: "",
        credits_required: 0,
        is_active: true,
      });
    } catch (err: any) {
      console.error("Error updating reward:", err);
      setError(err.message);
    }
  };

  const handleDeleteReward = async (rewardId: string) => {
    if (!confirm("Are you sure you want to delete this reward?")) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Not authenticated");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/rewards/admin/${rewardId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete reward: ${response.status}`);
      }

      await fetchRewards();
    } catch (err: any) {
      console.error("Error deleting reward:", err);
      setError(err.message);
    }
  };

  const openCreateDialog = () => {
    setFormData({
      title: "",
      description: "",
      credits_required: 0,
      is_active: true,
    });
    setIsCreateOpen(true);
  };

  const openEditDialog = (reward: Reward) => {
    setEditingReward(reward);
    setFormData({
      title: reward.title,
      description: reward.description || "",
      credits_required: reward.credits_required,
      is_active: reward.is_active,
    });
    setIsEditOpen(true);
  };

  return (
    <AdminGuard>
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto py-8 px-4 max-w-7xl">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Reward Management</h1>
              <p className="text-gray-400">
                Create and manage rewards that users can claim with credits
              </p>
            </div>
            <Link href="/admin">
              <Button variant="outline" className="border-gray-700 text-white hover:bg-gray-800">
                Back to Dashboard
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

          <div className="mb-6 flex justify-end">
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
              <DialogTrigger asChild>
                <Button onClick={openCreateDialog} className="bg-primary hover:bg-primary/90">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Reward
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-gray-900 border-gray-800">
                <DialogHeader>
                  <DialogTitle>Create New Reward</DialogTitle>
                  <DialogDescription>
                    Add a new reward that users can claim with their credits.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Title *</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="e.g., $10 Gift Card"
                      className="bg-gray-800 border-gray-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Describe the reward..."
                      className="bg-gray-800 border-gray-700"
                      rows={3}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="credits">Credits Required *</Label>
                    <Input
                      id="credits"
                      type="number"
                      min="1"
                      value={formData.credits_required}
                      onChange={(e) => setFormData({ ...formData, credits_required: parseInt(e.target.value) || 0 })}
                      className="bg-gray-800 border-gray-700"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="is_active"
                      checked={formData.is_active}
                      onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                    />
                    <Label htmlFor="is_active">Active (visible to users)</Label>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateOpen(false)} className="border-gray-700">
                    Cancel
                  </Button>
                  <Button onClick={handleCreateReward} disabled={!formData.title || formData.credits_required <= 0}>
                    Create Reward
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
          ) : rewards.length === 0 ? (
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="py-12 text-center">
                <Gift className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No rewards yet</h3>
                <p className="text-gray-400 mb-4">
                  Create your first reward to get started
                </p>
                <Button onClick={openCreateDialog}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Reward
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {rewards.map((reward) => (
                <Card key={reward.id} className="bg-gray-900 border-gray-800">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{reward.title}</CardTitle>
                        <CardDescription className="mt-1">
                          {reward.credits_required} credits
                        </CardDescription>
                      </div>
                      <div className="flex items-center space-x-2">
                        {reward.is_active ? (
                          <span className="px-2 py-1 text-xs bg-green-500/10 text-green-400 rounded">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs bg-gray-500/10 text-gray-400 rounded">
                            Inactive
                          </span>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {reward.description && (
                      <p className="text-sm text-gray-400 mb-4">{reward.description}</p>
                    )}
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditDialog(reward)}
                        className="flex-1 border-gray-700"
                      >
                        <Edit className="mr-2 h-3 w-3" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteReward(reward.id)}
                        className="flex-1 border-red-700 text-red-400 hover:bg-red-900/10"
                      >
                        <Trash2 className="mr-2 h-3 w-3" />
                        Delete
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
            <DialogContent className="bg-gray-900 border-gray-800">
              <DialogHeader>
                <DialogTitle>Edit Reward</DialogTitle>
                <DialogDescription>
                  Update the reward details.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-title">Title *</Label>
                  <Input
                    id="edit-title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="bg-gray-800 border-gray-700"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-description">Description</Label>
                  <Textarea
                    id="edit-description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="bg-gray-800 border-gray-700"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-credits">Credits Required *</Label>
                  <Input
                    id="edit-credits"
                    type="number"
                    min="1"
                    value={formData.credits_required}
                    onChange={(e) => setFormData({ ...formData, credits_required: parseInt(e.target.value) || 0 })}
                    className="bg-gray-800 border-gray-700"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="edit-is_active"
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                  <Label htmlFor="edit-is_active">Active (visible to users)</Label>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsEditOpen(false)} className="border-gray-700">
                  Cancel
                </Button>
                <Button onClick={handleEditReward} disabled={!formData.title || formData.credits_required <= 0}>
                  Update Reward
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </AdminGuard>
  );
}
