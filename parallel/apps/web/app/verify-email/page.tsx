"use client";

import { CheckCircle2, Loader2, MailWarning } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { AuthShell } from "@/components/auth-shell";
import { Brand } from "@/components/brand";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError, resendVerification, verifyEmail } from "@/lib/api";

type Status = "verifying" | "success" | "already" | "error" | "missing";

function VerifyEmailInner() {
  const token = useSearchParams().get("token");
  const [status, setStatus] = useState<Status>(token ? "verifying" : "missing");
  const [email, setEmail] = useState("");
  const [resending, setResending] = useState(false);
  const ran = useRef(false);

  useEffect(() => {
    if (!token || ran.current) return;
    ran.current = true; // guard React's dev double-mount
    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err) => {
        // "Already verified" is a benign outcome — send them to sign in.
        if (
          err instanceof ApiError &&
          (err.code === "AUTH_007" || err.code === "AUTH_010")
        ) {
          setStatus("already");
        } else {
          setStatus("error");
        }
      });
  }, [token]);

  async function handleResend(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setResending(true);
    try {
      await resendVerification(email);
      toast.success("Verification email sent — check your inbox.");
    } catch (err) {
      toast.error(
        err instanceof ApiError
          ? err.message
          : "Could not resend right now. Try again.",
      );
    } finally {
      setResending(false);
    }
  }

  if (status === "verifying") {
    return (
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="items-center space-y-2 text-center">
          <Loader2 className="size-6 animate-spin text-primary" />
          <CardTitle className="text-xl">Verifying your email…</CardTitle>
          <CardDescription>This will only take a moment.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (status === "success" || status === "already") {
    return (
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="items-center space-y-2 text-center">
          <span className="flex size-11 items-center justify-center rounded-2xl bg-accent text-primary">
            <CheckCircle2 className="size-6" />
          </span>
          <CardTitle className="text-xl">
            {status === "already" ? "Already verified" : "You're all set"}
          </CardTitle>
          <CardDescription>
            {status === "already"
              ? "Your email is already confirmed. Just sign in."
              : "Your email is confirmed. Sign in to meet your parallel self."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full">
            <Link href="/login">Continue to sign in</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  // error | missing — offer a fresh link.
  return (
    <Card className="border-border/60 shadow-sm">
      <CardHeader className="items-center space-y-2 text-center">
        <span className="flex size-11 items-center justify-center rounded-2xl bg-accent text-primary">
          <MailWarning className="size-6" />
        </span>
        <CardTitle className="text-xl">This link didn&apos;t work</CardTitle>
        <CardDescription>
          {status === "missing"
            ? "The verification link is missing its token."
            : "It may have expired or already been used."}{" "}
          Enter your email to get a fresh one.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleResend} className="space-y-3" noValidate>
          <Input
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Button type="submit" className="w-full" disabled={resending}>
            {resending && <Loader2 className="animate-spin" />}
            Send a new link
          </Button>
          <Button asChild variant="ghost" className="w-full">
            <Link href="/login">Back to sign in</Link>
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <AuthShell>
      <div className="mb-8 flex justify-center">
        <Brand size="lg" />
      </div>
      <Suspense
        fallback={
          <div className="flex justify-center py-10">
            <Loader2 className="size-6 animate-spin text-primary" />
          </div>
        }
      >
        <VerifyEmailInner />
      </Suspense>
    </AuthShell>
  );
}
