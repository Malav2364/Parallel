"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, MailWarning } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { AuthShell } from "@/components/auth-shell";
import { Brand } from "@/components/brand";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ApiError, resendVerification } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const loginSchema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password"),
});
type LoginValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  // Set when login is rejected because the email isn't verified (403 AUTH_009):
  // we switch to a dedicated "verify your email" panel instead of navigating.
  const [unverifiedEmail, setUnverifiedEmail] = useState<string | null>(null);
  const [resending, setResending] = useState(false);

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function onSubmit(values: LoginValues) {
    try {
      await login(values.email, values.password);
      router.push("/chat");
    } catch (err) {
      if (
        err instanceof ApiError &&
        (err.code === "AUTH_009" || err.status === 403)
      ) {
        setUnverifiedEmail(values.email);
        return;
      }
      toast.error(
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again.",
      );
    }
  }

  async function handleResend() {
    if (!unverifiedEmail) return;
    setResending(true);
    try {
      await resendVerification(unverifiedEmail);
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

  if (unverifiedEmail) {
    return (
      <AuthShell>
        <div className="mb-8 flex justify-center">
          <Brand size="lg" />
        </div>
        <Card className="border-border/60 shadow-sm">
          <CardHeader className="items-center space-y-2 text-center">
            <span className="flex size-11 items-center justify-center rounded-2xl bg-accent text-primary">
              <MailWarning className="size-6" />
            </span>
            <CardTitle className="text-xl">Verify your email first</CardTitle>
            <CardDescription>
              We sent a verification link to{" "}
              <span className="font-medium text-foreground">
                {unverifiedEmail}
              </span>
              . Please confirm it before signing in.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              className="w-full"
              onClick={handleResend}
              disabled={resending}
            >
              {resending && <Loader2 className="animate-spin" />}
              Resend verification email
            </Button>
            <Button
              variant="ghost"
              className="w-full"
              onClick={() => setUnverifiedEmail(null)}
            >
              Back to sign in
            </Button>
          </CardContent>
        </Card>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <div className="mb-8 flex justify-center">
        <Brand size="lg" />
      </div>
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="space-y-1.5 text-center">
          <CardTitle className="text-xl">Welcome back</CardTitle>
          <CardDescription>
            Sign in to pick up where you left off.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4"
              noValidate
            >
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        autoComplete="email"
                        placeholder="you@example.com"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        autoComplete="current-password"
                        placeholder="••••••••"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button
                type="submit"
                className="w-full"
                disabled={form.formState.isSubmitting}
              >
                {form.formState.isSubmitting && (
                  <Loader2 className="animate-spin" />
                )}
                Sign in
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-muted-foreground">
            New here?{" "}
            <Link
              href="/register"
              className="font-medium text-primary hover:underline"
            >
              Create an account
            </Link>
          </p>
        </CardFooter>
      </Card>
    </AuthShell>
  );
}
