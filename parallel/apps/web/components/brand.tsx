import { Sun } from "lucide-react";

import { cn } from "@/lib/utils";

// The Parallel mark — a warm sun. Kept small and reusable across auth + chat.
export function Brand({
  className,
  size = "md",
}: {
  className?: string;
  size?: "md" | "lg";
}) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "flex items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm",
          size === "lg" ? "size-11" : "size-9",
        )}
      >
        <Sun className={size === "lg" ? "size-6" : "size-5"} strokeWidth={2.25} />
      </span>
      <span
        className={cn(
          "font-semibold tracking-tight text-foreground",
          size === "lg" ? "text-2xl" : "text-xl",
        )}
      >
        Parallel
      </span>
    </div>
  );
}
