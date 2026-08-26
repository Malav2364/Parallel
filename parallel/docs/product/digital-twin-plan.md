# Parallel — Product Plan v2: From Assistant to Digital Twin

*Author roles: Sr. Product Designer · Sr. Product Engineer · Sr. AI/ML Engineer. Status: **proposed, for review.** Date: 2026-08-26.*

---

## 0. Where we are (grounded in the current codebase)

**Solid foundation, thin product.** We have 9 FastAPI microservices (identity, gateway, projects, spaces, context, goals, habits, reminders + worker, notifications), a shared `pios_kernel` domain lib, per-service Postgres, and a **working understanding→execution loop** in `context`: a 3-tier cascade (deterministic rules → local semantic resolve → one Gemini call) that creates reminders/habits/goals/projects with idempotency + read-back, plus a deterministic Response Composer and a minimal Next.js chat.

**What a digital twin needs but we do NOT have yet:**
| Pillar | Today | Gap |
|---|---|---|
| **Memory** (knows the user) | flat versioned JSON per user | no unified, cross-domain, queryable model of the person |
| **Connectors** (sees real life) | none (only Gemini + SMTP) | no GitHub/Slack/Gmail/calendar/finance/health; no MCP |
| **Proactivity** (initiative) | hand-rolled reminder poller | no signal watcher, no nudge policy, no "act on behalf" |
| **Voice** (primary interface) | none | no STT/TTS/realtime |

Also foundational: goals/habits/reminders/notifications aren't exposed through the gateway or in docker-compose; there's no real scheduler/event bus (a `while True: sleep(5)` poller); the `X-User-Id` trust boundary is open. These block "real connector + proactive" work and must be closed early.

---

## 1. Product thesis — what makes this a twin, not a chatbot

A chatbot answers. A twin does three things a chatbot can't:

1. **Remembers & connects** — one persistent model of *you* across health, finance, career, habits, interests. (Pillar A: Memory)
2. **Takes initiative** — acts at the right moment without being asked, inside trust limits. (Pillar C: Proactivity/Autonomy)
3. **Reaches into your real life** — mail, code, calendar, money, body, via pluggable sources. (Pillar B: Connectors/MCP)

**Voice** (Pillar D) is the *interface* that makes all three feel effortless — but voice on an empty twin is a demo, not a product. The plan builds substance and voice together, substance leading by a step.

---

## 2. The four pillars (target architecture)

### Pillar A — Memory / Personal Intelligence Graph *(the spine)*
- **Why it's first:** "take decisions for the user" and "know all things" are impossible over a flat blob. Every other pillar reads Memory.
- **What:** a `memory` service holding **(1) typed entities** (Person, Goal, Habit, Project, HealthMetric, FinanceAccount, Interest, Contact, Event), **(2) an append-only episodic timeline** (what happened, when), **(3) semantic retrieval** (embeddings — reuse the existing Gemini-embeddings+cosine pattern, no new infra). Pragmatic entities+retrieval **before** a graph DB (per our agreed roadmap).
- **Context Planner:** a `UnifiedContext` assembler that builds a compact, token-budgeted context bundle per request (recent episodic + semantic hits + relevant entities) and feeds it to `/process`. This is the RAG of the twin.

### Pillar B — Connectors via MCP *(the senses)*
- **Why MCP:** it's the exact match for your "custom MCPs so users bring their own data." **Parallel becomes an MCP host.** Each source = an MCP server exposing tools (`list_review_requests`, `read_recent_emails`) + resources. We ship first-party servers (GitHub, Slack, Gmail, Google Calendar, Google Fit / Apple Health, Plaid for finance); third-party and user-provided servers plug in through the same interface. Future-proof and open by design.
- **Ingestion path:** connector → normalized events → Memory (episodic) **and** a signal stream for proactivity.
- **Requires:** OAuth + an encrypted token vault, per-connector consent/revoke, and a sync scheduler.

### Pillar C — Proactivity & Autonomy engine *(initiative + hands)*
- **Why:** "watch the whole day, know where to nudge, act on behalf" = the Observe→Reason→Decide→Execute→Reflect loop running *autonomously*, not request/response.
- **What:** a **watcher** over the signal stream + Memory that detects *moments* (bad-habit relapse risk, an important email, a PR needing review, a goal slipping); a **policy** that decides **nudge vs. act vs. stay silent** under an *attention budget* (proactive ≠ spammy); delivery reuses notifications + the reminders-worker pattern.
- **Autonomy = confidence × risk.** We already have a HIGH/MEDIUM/LOW confidence gate. Multiply it by an **action-risk tier**: read-only/low-risk → auto; reversible/medium → confirm; irreversible/high-stakes (send mail, move money) → **always confirm**. Every autonomous action is logged and undoable. This is "never silently wrong" scaled to the whole system.

### Pillar D — Voice *(the primary interface)*
- **Brain stays modality-agnostic:** voice wraps the existing loop (STT → `/process` → spoken `message`). No second brain.
- **Constraint-driven design:** the agentrouter gateway **stalls on large streams** → start with a **pipeline** (discrete STT + non-streaming `/process` + TTS), which works today and degrades gracefully. Leave a clean seam to upgrade to a realtime speech-to-speech API later, once the gateway constraint is resolved.
- Wake word + barge-in + a short-utterance latency budget; voice handles input, spoken confirmations, and replies.

---

## 3. Cross-cutting tracks (run through every phase)

- **Trust & Autonomy:** risk tiers, confirmation UX, an audit log of twin actions, one-tap undo.
- **Privacy & Security:** encrypted token vault, per-connector consent & revoke, data minimization, and **close the `X-User-Id` trust boundary before any real connector goes live** — health + finance + mail make this non-negotiable.
- **Infra maturation:** a real job scheduler + a lightweight event stream to replace the poller — proactivity needs reliable scheduled *and* event-driven triggers.

---

## 4. Sequenced roadmap — "build the loop before the org chart," applied

**Principle:** don't build 4 pillars × 7 domains at once. Prove the twin on **one domain you live in — developer life (GitHub/Slack/Gmail)** — because (a) fastest dogfooding (you are the user), (b) that single vertical exercises **all four pillars**, (c) read/triage actions let autonomy start at low risk. Then replicate the *same* pattern to Health, Finance, Career.

| Milestone | Delivers | Pillars touched |
|---|---|---|
| **M-A · Memory spine** | `memory` service (entities+episodic+retrieval), UnifiedContext into `/process`, onboarding writes initial profile | A |
| **M-B · First connector** | Parallel as MCP host + first-party **GitHub** server (read: notifications, review requests, CI), OAuth + token vault, ingest → Memory | B |
| **M-C · First proactive behavior** | watcher: "PR needs review" / "important email" → nudge via notifications; attention budget; risk-tier = auto-surface (read-only) | C |
| **M-D · Voice slice (pipeline)** | STT → `/process` → TTS over the working loop; spoken confirms/replies; optional wake word | D |
| **M-E · Fan out** | + Gmail & Calendar; first non-dev department (**Health** or **Finance** — see decisions) with its connector; introduce Council routing once ≥2 domains justify a router | A–D + Council |
| **M-F · Deepen** | Reflect→Learn (twin improves from outcomes), richer generative-UI onboarding, more connectors, realtime-voice upgrade | all |

**M-A → M-D is the shortest path to a prototype that actually feels like a twin** (see §6).

---

## 5. AI/ML mechanism (how the intelligence actually works)

- **Keep the tiered cascade** (deterministic-first, LLM-last). It's cheap, fast, auditable, and already built. *Extend it, don't replace it.*
- **Memory retrieval = hybrid:** recency (episodic) + semantic (embeddings) + structured entity lookups → one compact, token-budgeted UnifiedContext.
- **Proactivity = rules + light ML:** start with deterministic triggers + per-user baselines (typical sleep/activity/focus windows → deviations = nudge triggers); add learned models (relapse prediction, email/notification importance ranking) only where rules plateau. Same "deterministic before LLM" philosophy.
- **Autonomy = confidence × risk:** LLM *proposes*, a deterministic policy *disposes* (auto / confirm / silent).
- **Cost & latency discipline:** keep LLM calls collapsed (the M5 work), cache, and push everything possible to deterministic tiers + local embeddings — essential behind the stalling gateway and for voice latency.

---

## 6. Definition of the first prototype (the demo we're driving toward)

> *You say, out loud:* "What's on my plate?"
> *Parallel replies, spoken:* "You've got 2 pull requests waiting on your review, and an important email from your co-founder about the demo. You also skipped your evening walk 3 days running — want me to move it to mornings?"
> *You:* "Draft a reply to the email and reschedule the walk."
> *Parallel:* reschedules the walk (low-risk → auto), **drafts** the email and reads it back for confirmation (send = high-risk → confirm).

That single interaction exercises Memory (walk habit, projects), a Connector (GitHub + Gmail), Proactivity (noticed the skipped walk + ranked the email), Autonomy (auto vs. confirm by risk), and Voice (in and out). Hitting it = the twin is real.

---

## 7. Open decisions (need your call before I lock the build order)

1. **Starting domain** — recommend **Developer (GitHub/Slack/Gmail)**: dogfood, low-risk, exercises all pillars. Alt: Health, or Finance.
2. **First milestone now** — recommend **M-A Memory spine** (the enabler). Alt: thin voice slice first (fastest "wow"), or first connector first.
3. **Voice architecture** — recommend **Pipeline (STT→/process→TTS)**: works behind the stalling gateway today. Alt: realtime speech-to-speech (better UX, needs gateway fix first), or defer voice.
4. **Autonomy posture** — recommend **confirm-then-act with risk-tiered auto** for read-only. Alt: suggest-only (safest), or auto-within-limits (boldest).
