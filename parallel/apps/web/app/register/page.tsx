"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, MailCheck } from "lucide-react";
import Link from "next/link";
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
import { ApiError, register as apiRegister, resendVerification } from "@/lib/api";

const registerSchema = z.object({
  first_name: z.string().trim().min(1, "Required"),
  last_name: z.string().trim().min(1, "Required"),
  email: z.email("Enter a valid email address"),
  password: z.string().min(8, "Use at least 8 characters"),
});
type RegisterValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  // Registration returns no tokens — on success we show a "check your inbox"
  // screen and hold the email so it can be resent from here.
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);
  const [resending, setResending] = useState(false);

  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { first_name: "", last_name: "", email: "", password: "" },
  });

  async function onSubmit(values: RegisterValues) {
    try {
      await apiRegister(values);
      setRegisteredEmail(values.email);
    } catch (err) {
      if (err instanceof ApiError && err.code === "AUTH_001") {
        form.setError("email", { message: "That email is already registered" });
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
    if (!registeredEmail) return;
    setResending(true);
    try {
      await resendVerification(registeredEmail);
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

  if (registeredEmail) {
    return (
      <AuthShell>
        <div className="mb-8 flex justify-center">
          <Brand size="lg" />
        </div>
        <Card className="border-border/60 shadow-sm">
          <CardHeader className="items-center space-y-2 text-center">
            <span className="flex size-11 items-center justify-center rounded-2xl bg-accent text-primary">
              <MailCheck className="size-6" />
            </span>
            <CardTitle className="text-xl">Check your inbox</CardTitle>
            <CardDescription>
              We sent a verification link to{" "}
              <span className="font-medium text-foreground">
                {registeredEmail}
              </span>
              . Click it to activate your account, then sign in.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button asChild className="w-full">
              <Link href="/login">Back to sign in</Link>
            </Button>
            <Button
              variant="ghost"
              className="w-full"
              onClick={handleResend}
              disabled={resending}
            >
              {resending && <Loader2 className="animate-spin" />}
              Resend email
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
          <CardTitle className="text-xl">Meet your parallel self</CardTitle>
          <CardDescription>
            Create an account to start the conversation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4"
              noValidate
            >
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="first_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First name</FormLabel>
                      <FormControl>
                        <Input
                          autoComplete="given-name"
                          placeholder="Ada"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="last_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Last name</FormLabel>
                      <FormControl>
                        <Input
                          autoComplete="family-name"
                          placeholder="Lovelace"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
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
                        autoComplete="new-password"
                        placeholder="At least 8 characters"
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
                Create account
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-primary hover:underline"
            >
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </AuthShell>
  );
}
