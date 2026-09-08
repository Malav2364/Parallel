import type { ReactNode } from "react";

// Centered warm layout for the auth screens: a soft glow behind a single card.
export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-dvh flex-col items-center justify-center overflow-hidden px-4 py-10">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-1/3 left-1/2 size-[44rem] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl"
      />
      <div className="relative w-full max-w-sm">{children}</div>
    </div>
  );
}
