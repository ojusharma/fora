"use client";

import Link from "next/link";
import { useIsAdmin } from "@/hooks/use-admin";

export function AdminLink() {
  const { isAdmin, loading } = useIsAdmin();

  if (loading || !isAdmin) {
    return null;
  }

  return (
    <Link
      href="/admin"
      className="text-xs px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded font-semibold"
    >
      Admin
    </Link>
  );
}
