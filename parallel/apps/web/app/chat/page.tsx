"use client";

import { ArrowUp, LogOut, Sun } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Brand } from "@/components/brand";
import { ShimmerText } from "@/components/shimmer-text";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, type PendingAction } from "@/lib/api";
import { RequireAuth, useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const EXAMPLE_PROMPTS = [
  "Remind me to call mom tomorrow at 9am",
  "Help me build a habit of reading every night",
  "My goal is to run a half marathon this year",
];

// Small sun badge used beside assistant messages.
function AssistantMark() {
  return (
    <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
      <Sun className="size-4" strokeWidth={2.25} />
    </span>
  );
}

function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex animate-in fade-in flex-col items-center gap-6 py-16 text-center duration-500">
      <span className="flex size-14 items-center justify-center rounded-3xl bg-primary text-primary-foreground shadow-sm">
        <Sun className="size-7" strokeWidth={2.25} />
      </span>
      <div className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight">
          Hey, I&apos;m Parallel
        </h1>
        <p className="mx-auto max-w-sm text-muted-foreground">
          Tell me what&apos;s on your mind — a reminder, a habit, a goal. I&apos;ll
          keep track and gently nudge.
        </p>
      </div>
      <div className="flex w-full max-w-sm flex-col gap-2">
        {EXAMPLE_PROMPTS.map((p) => (
          <button
            key={p}
            onClick={() => onPick(p)}
            className="rounded-2xl border border-border/60 bg-card px-4 py-3 text-left text-sm text-foreground shadow-sm transition-colors hover:bg-accent"
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

function ChatSurface() {
  const { user, logout, sendMessage } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  // The confirm/clarify state to echo back on the next turn (null = no loop).
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);

  const idRef = useRef(0);
  const nextId = useCallback(() => String(++idRef.current), []);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const send = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || pending) return;
      setMessages((m) => [
        ...m,
        { id: nextId(), role: "user", content: text },
      ]);
      setInput("");
      setPending(true);
      const echo = pendingAction;
      try {
        const res = await sendMessage(text, echo);
        setMessages((m) => [
          ...m,
          { id: nextId(), role: "assistant", content: res.message },
        ]);
        // A terminal reply returns pending_action: null, closing the loop.
        setPendingAction(res.pending_action);
      } catch (err) {
        toast.error(
          err instanceof ApiError
            ? err.message
            : "Couldn't reach Parallel. Please try again.",
        );
      } finally {
        setPending(false);
      }
    },
    [pending, pendingAction, sendMessage, nextId],
  );

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send(input);
    }
  }

  const candidates = pendingAction?.slots?.candidates;
  const initial = user?.email?.[0]?.toUpperCase() ?? "?";
  const isEmpty = messages.length === 0 && !pending;

  return (
    <div className="flex h-dvh flex-col bg-background">
      <header className="flex-none border-b border-border/60 bg-background/80 backdrop-blur">
        <div className="mx-auto flex w-full max-w-2xl items-center justify-between px-4 py-3">
          <Brand />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="rounded-full outline-none ring-ring/40 focus-visible:ring-2">
                <Avatar className="size-9">
                  <AvatarFallback className="bg-secondary text-secondary-foreground">
                    {initial}
                  </AvatarFallback>
                </Avatar>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="truncate font-normal text-muted-foreground">
                {user?.email ?? "Signed in"}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => void logout()}>
                <LogOut />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-4 py-6">
          {isEmpty ? (
            <EmptyState onPick={(t) => void send(t)} />
          ) : (
            <div className="space-y-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "flex animate-in gap-3 fade-in slide-in-from-bottom-2 duration-300",
                    m.role === "user" && "justify-end",
                  )}
                >
                  {m.role === "assistant" && <AssistantMark />}
                  <div
                    className={cn(
                      "max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed",
                      m.role === "user"
                        ? "bg-primary/10 text-foreground"
                        : "border border-border/60 bg-card text-foreground shadow-sm",
                    )}
                  >
                    {m.content}
                  </div>
                </div>
              ))}
              {pending && (
                <div className="flex animate-in gap-3 fade-in duration-200">
                  <AssistantMark />
                  <div className="rounded-2xl border border-border/60 bg-card px-4 py-2.5 shadow-sm">
                    <ShimmerText className="text-[15px]">Thinking…</ShimmerText>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="flex-none border-t border-border/60 bg-background/80 backdrop-blur">
        <div className="mx-auto w-full max-w-2xl px-4 py-3">
          {Array.isArray(candidates) && candidates.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {candidates.map((c) => (
                <button
                  key={c}
                  onClick={() => void send(c)}
                  disabled={pending}
                  className="rounded-full border border-primary/30 bg-primary/5 px-3.5 py-1.5 text-sm text-foreground transition-colors hover:bg-primary/10 disabled:opacity-50"
                >
                  {c}
                </button>
              ))}
            </div>
          )}
          <div className="flex items-end gap-2 rounded-3xl border border-border/60 bg-card p-2 shadow-sm transition-shadow focus-within:ring-2 focus-within:ring-ring/40">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder="Message Parallel…"
              disabled={pending}
              className="max-h-40 min-h-0 resize-none border-0 bg-transparent px-2 py-2 shadow-none [field-sizing:content] focus-visible:ring-0"
            />
            <Button
              size="icon"
              className="size-9 shrink-0 rounded-2xl"
              onClick={() => void send(input)}
              disabled={pending || !input.trim()}
              aria-label="Send"
            >
              <ArrowUp />
            </Button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function ChatPage() {
  return (
    <RequireAuth>
      <ChatSurface />
    </RequireAuth>
  );
}
