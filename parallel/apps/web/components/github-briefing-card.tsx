"use client";

import { GitPullRequest } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { ShimmerText } from "@/components/shimmer-text";
import { type BriefingItem, type BriefingResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth";

function BriefingRow({ item }: { item: BriefingItem }) {
  const label =
    item.repo && item.number
      ? `${item.repo} #${item.number}`
      : (item.repo ?? "Pull request");
  return (
    <a
      href={item.url ?? "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-xl px-3 py-2 text-left transition-colors hover:bg-accent"
    >
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className="block truncate text-sm text-foreground">
        {item.title ?? "Untitled"}
      </span>
    </a>
  );
}

function BriefingGroup({
  heading,
  items,
}: {
  heading: string;
  items: BriefingItem[];
}) {
  if (items.length === 0) return null;
  return (
    <div className="mt-3">
      <span className="px-1 text-xs font-medium text-muted-foreground">
        {heading}
      </span>
      <div className="mt-1 flex flex-col gap-1">
        {items.map((item, i) => (
          <BriefingRow
            key={item.url ?? `${item.repo}#${item.number}#${i}`}
            item={item}
          />
        ))}
      </div>
    </div>
  );
}

// The twin's arrival briefing: what it currently sees on GitHub. Fetched once on
// mount. The backend degrades a down connector to connected:false (a valid,
// rendered state), so a thrown error here is a gateway/auth failure — this
// ambient widget simply hides itself and leaves chat fully usable.
export function GithubBriefingCard() {
  const { getBriefing } = useAuth();
  const [data, setData] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true; // guard React's dev double-mount
    getBriefing()
      .then(setData)
      .catch(() => {
        // Non-critical widget — leave data null so the card is omitted.
      })
      .finally(() => setLoading(false));
  }, [getBriefing]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 rounded-2xl border border-border/60 bg-card p-4 text-left shadow-sm">
        <GitPullRequest className="size-4 text-muted-foreground" />
        <ShimmerText className="text-sm">Checking GitHub…</ShimmerText>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 rounded-2xl border border-border/60 bg-card p-4 text-left shadow-sm duration-300">
      <div className="flex items-center gap-2">
        <GitPullRequest className="size-4 text-muted-foreground" />
        <span className="text-sm font-medium text-foreground">GitHub</span>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{data.message}</p>
      <BriefingGroup
        heading="Waiting on your review"
        items={data.review_requests_items}
      />
      <BriefingGroup heading="Your open PRs" items={data.my_pr_items} />
    </div>
  );
}
