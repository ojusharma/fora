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
      className="font-semibold"
    >
      admin
    </Link>
  );
}
