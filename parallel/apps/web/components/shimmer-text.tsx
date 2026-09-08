import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

// Animated shimmering text. The gradient sweep is defined by `.shimmer-text`
// in globals.css (masked onto the text via background-clip). Used as the
// assistant's "Thinking…" affordance while a reply is in flight.
export function ShimmerText({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <span className={cn("shimmer-text", className)}>{children}</span>;
}
