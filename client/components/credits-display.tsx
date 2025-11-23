"use client";

import { Coins } from "lucide-react";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { RewardsModal } from "./rewards-modal";

export function CreditsDisplay() {
  const supabase = createClient();
  const [uid, setUid] = useState<string | null>(null);
  const [credits, setCredits] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [showRewards, setShowRewards] = useState(false);

  useEffect(() => {
    fetchUserCredits();
    
    // Subscribe to realtime updates for credits
    const channel = supabase
      .channel('credits-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'user_profiles',
          filter: `uid=eq.${uid}`,
        },
        (payload) => {
          if (payload.new && 'credits' in payload.new) {
            setCredits((payload.new as any).credits || 0);
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [uid]);

  const fetchUserCredits = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        setLoading(false);
        return;
      }

      setUid(user.id);

      // Fetch user profile with credits
      const { data, error } = await supabase
        .from('user_profiles')
        .select('credits')
        .eq('uid', user.id)
        .single();

      if (error) {
        console.error('Error fetching credits:', error);
        setLoading(false);
        return;
      }

      setCredits(data?.credits || 0);
      setLoading(false);
    } catch (err) {
      console.error('Error:', err);
      setLoading(false);
    }
  };

  if (!uid || loading) return null;

  return (
    <>
      <div
        onClick={() => setShowRewards(true)}
        className="relative cursor-pointer flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20 hover:border-yellow-500/40 transition-all"
      >
        <Coins className="w-5 h-5 text-yellow-500" />
        <span className="font-semibold text-yellow-500">{credits}</span>
      </div>

      <RewardsModal
        open={showRewards}
        onClose={() => setShowRewards(false)}
        userCredits={credits}
        onRewardClaimed={fetchUserCredits}
      />
    </>
  );
}
