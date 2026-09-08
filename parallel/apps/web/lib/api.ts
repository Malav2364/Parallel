// Typed client for the Parallel API gateway.
// All calls go through the gateway (http://localhost:8000 by default), which
// validates the Bearer token and proxies to the identity / context services.
// This module is intentionally stateless: token storage and the
// refresh-on-401 retry live in lib/auth.tsx.

export const GATEWAY_URL =
  process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000";

const IDENTITY = "/api/identity/auth";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface UserResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_verified: boolean;
}

export type ProcessType =
  | "new_intent"
  | "context_only"
  | "existing_project"
  | "multi_intent"
  | "needs_confirmation"
  | "needs_clarification";

export interface PendingAction {
  action: string;
  source?: string;
  confidence?: number;
  slots?: Record<string, unknown> & { candidates?: string[] };
  [key: string]: unknown;
}

export interface ProcessResponse {
  message: string;
  type: ProcessType;
  tier?: string | null;
  pending_action: PendingAction | null;
  prompt?: string | null;
  [key: string]: unknown;
}

// Carries the identity service's error code (e.g. "AUTH_009" = email not
// verified) so screens can react to specific failures, plus the HTTP status.
export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

// The gateway returns either the identity error envelope
// ({ error: { code, message } }) or a FastAPI { detail } body.
async function toError(res: Response): Promise<ApiError> {
  let message = res.statusText || "Request failed";
  let code: string | undefined;
  try {
    const body = (await res.json()) as {
      error?: { code?: string; message?: string };
      detail?: unknown;
    };
    if (body?.error?.message) {
      message = body.error.message;
      code = body.error.code;
    } else if (typeof body?.detail === "string") {
      message = body.detail;
    } else if (
      Array.isArray(body?.detail) &&
      typeof (body.detail[0] as { msg?: string })?.msg === "string"
    ) {
      message = (body.detail[0] as { msg: string }).msg;
    }
  } catch {
    // Non-JSON body — keep the status text.
  }
  return new ApiError(message, res.status, code);
}

async function jsonPost<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${GATEWAY_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await toError(res);
  return res.json() as Promise<T>;
}

export function register(input: RegisterInput): Promise<UserResponse> {
  return jsonPost<UserResponse>(`${IDENTITY}/register`, input);
}

// Login is OAuth2PasswordRequestForm: x-www-form-urlencoded with a `username`
// field (= email), NOT JSON. Unverified users are rejected here with 403 AUTH_009.
export async function login(
  email: string,
  password: string,
): Promise<AuthTokens> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const res = await fetch(`${GATEWAY_URL}${IDENTITY}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw await toError(res);
  return res.json() as Promise<AuthTokens>;
}

export function refresh(refreshToken: string): Promise<AuthTokens> {
  return jsonPost<AuthTokens>(`${IDENTITY}/refresh`, {
    refresh_token: refreshToken,
  });
}

// Revokes the refresh token server-side. A 401 (already-invalid token) is fine
// on logout — the client discards its tokens regardless.
export async function logout(refreshToken: string): Promise<void> {
  const res = await fetch(`${GATEWAY_URL}${IDENTITY}/logout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok && res.status !== 401) throw await toError(res);
}

export async function verifyEmail(token: string): Promise<{ message: string }> {
  const res = await fetch(
    `${GATEWAY_URL}${IDENTITY}/verify-email?token=${encodeURIComponent(token)}`,
    { method: "GET" },
  );
  if (!res.ok) throw await toError(res);
  return res.json() as Promise<{ message: string }>;
}

export function resendVerification(email: string): Promise<{ message: string }> {
  return jsonPost<{ message: string }>(`${IDENTITY}/resend-verification`, {
    email,
  });
}

// The chat call. user_id is derived by the gateway from the Bearer token and
// injected downstream as X-User-Id, so it is not part of the body.
export async function processMessage(
  accessToken: string,
  message: string,
  pendingAction: PendingAction | null,
): Promise<ProcessResponse> {
  const res = await fetch(`${GATEWAY_URL}/api/context/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ message, pending_action: pendingAction }),
  });
  if (!res.ok) throw await toError(res);
  return res.json() as Promise<ProcessResponse>;
}

// A single pull request in a briefing. Any field may be null upstream.
export interface BriefingItem {
  repo: string | null;
  number: number | null;
  title: string | null;
  url: string | null;
}

export interface BriefingResponse {
  connected: boolean;
  review_requests: number;
  my_open_prs: number;
  message: string;
  review_requests_items: BriefingItem[];
  my_pr_items: BriefingItem[];
}

// The twin's GitHub briefing. Like processMessage, user_id is derived by the
// gateway from the Bearer token. A down connector still returns 200 with
// connected:false, so callers never need to treat that as an error.
export async function getBriefing(
  accessToken: string,
): Promise<BriefingResponse> {
  const res = await fetch(`${GATEWAY_URL}/api/context/briefing`, {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw await toError(res);
  return res.json() as Promise<BriefingResponse>;
}
