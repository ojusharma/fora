"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Gift, Loader2, Coins, CheckCircle2 } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

interface Reward {
  id: string;
  title: string;
  description?: string;
  credits_required: number;
  is_active: boolean;
}

interface RewardsModalProps {
  open: boolean;
  onClose: () => void;
  userCredits: number;
  onRewardClaimed?: () => void;
}

export function RewardsModal({ open, onClose, userCredits, onRewardClaimed }: RewardsModalProps) {
  const supabase = createClient();
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      fetchRewards();
    }
  }, [open]);

  const fetchRewards = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/rewards/`);

      if (!response.ok) {
        throw new Error("Failed to fetch rewards");
      }

      const data = await response.json();
      setRewards(data);
    } catch (err: any) {
      console.error("Error fetching rewards:", err);
      setError("Failed to load rewards. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleClaimReward = async (rewardId: string, rewardTitle: string) => {
    try {
      setClaiming(rewardId);
      setError(null);
      setSuccess(null);

      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        setError("You must be logged in to claim rewards");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/rewards/${rewardId}/claim`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to claim reward");
      }

      setSuccess(`Successfully claimed ${rewardTitle}! Check your email for details.`);
      
      // Refresh rewards list
      await fetchRewards();
      
      // Notify parent to refresh credits
      if (onRewardClaimed) {
        onRewardClaimed();
      }

      // Close modal after 2 seconds
      setTimeout(() => {
        setSuccess(null);
        onClose();
      }, 2000);
    } catch (err: any) {
      console.error("Error claiming reward:", err);
      setError(err.message || "Failed to claim reward. Please try again.");
    } finally {
      setClaiming(null);
    }
  };

  const canAfford = (creditsRequired: number) => userCredits >= creditsRequired;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Gift className="w-6 h-6" />
            Available Rewards
          </DialogTitle>
          <DialogDescription>
            Redeem your credits for exciting rewards
          </DialogDescription>
        </DialogHeader>

        <div className="mb-4 p-4 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20 rounded-lg">
          <div className="flex items-center gap-2">
            <Coins className="w-5 h-5 text-yellow-500" />
            <span className="font-semibold">Your Credits:</span>
            <span className="text-2xl font-bold text-yellow-500">{userCredits}</span>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded mb-4">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 px-4 py-3 rounded mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            <p className="text-sm">{success}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : rewards.length === 0 ? (
          <div className="py-12 text-center">
            <Gift className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No rewards available</h3>
            <p className="text-muted-foreground">
              Check back later for new rewards!
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {rewards.map((reward) => {
              const affordable = canAfford(reward.credits_required);
              const isClaiming = claiming === reward.id;

              return (
                <Card key={reward.id} className={!affordable ? "opacity-60" : ""}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{reward.title}</CardTitle>
                        {reward.description && (
                          <CardDescription className="mt-2">
                            {reward.description}
                          </CardDescription>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Coins className="w-5 h-5 text-yellow-500" />
                        <span className="font-semibold text-lg">
                          {reward.credits_required} credits
                        </span>
                      </div>
                      <Button
                        onClick={() => handleClaimReward(reward.id, reward.title)}
                        disabled={!affordable || isClaiming}
                        className={affordable ? "" : "opacity-50"}
                      >
                        {isClaiming ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Claiming...
                          </>
                        ) : affordable ? (
                          "Claim Reward"
                        ) : (
                          `Need ${reward.credits_required - userCredits} more credits`
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
