"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    router.replace(isAuthenticated ? "/chat" : "/login");
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="flex min-h-dvh items-center justify-center">
      <div className="size-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
    </div>
  );
}
