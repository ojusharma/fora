"use client";

import { Bell } from "lucide-react";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useNotifications } from "@/hooks/use-notifications";
import Link from "next/link";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover"; // <-- shadcn

export function NotificationBell() {
  const supabase = createClient();
  const [uid, setUid] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUid(data?.user?.id ?? null);
    });
  }, []);

  const { notifications, unreadCount, markAsRead } =
    useNotifications(uid ?? undefined);

  if (!uid) return null;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <div className="relative cursor-pointer">
          <Bell className="w-6 h-6 text-foreground" />

          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">
              {unreadCount}
            </span>
          )}
        </div>
      </PopoverTrigger>

      <PopoverContent
        align="end"
        className="w-80 p-4 shadow-lg rounded-lg border bg-popover"
      >
        <h3 className="text-sm font-semibold mb-3">Notifications</h3>

        {notifications.length === 0 && (
          <p className="text-xs text-muted-foreground">No notifications</p>
        )}

        <ul className="max-h-72 overflow-y-auto space-y-2">
          {notifications.map((n) => (
            <li
              key={n.id}
              className={`p-3 rounded border cursor-pointer transition ${
                n.is_read ? "bg-gray-50" : "bg-blue-50 border-blue-200"
              }`}
              onClick={() => markAsRead(n.id)}
            >
              <p className="text-sm mb-1">{n.body}</p>

              <p className="text-[10px] text-muted-foreground mb-2">
                {new Date(n.created_at).toLocaleString()}
              </p>

              {/** Redirect URL */}
              {n.metadata?.redirect_url && (
                <Link
                  href={n.metadata.redirect_url}
                  className="text-xs font-medium text-blue-600 hover:underline"
                >
                  View listing →
                </Link>
              )}
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
