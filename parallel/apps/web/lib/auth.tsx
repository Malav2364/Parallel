"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  ApiError,
  login as apiLogin,
  logout as apiLogout,
  processMessage,
  refresh as apiRefresh,
  register as apiRegister,
  type PendingAction,
  type ProcessResponse,
  type RegisterInput,
  type UserResponse,
} from "@/lib/api";

const ACCESS_KEY = "parallel.access";
const REFRESH_KEY = "parallel.refresh";
const EMAIL_KEY = "parallel.email";

interface AuthUser {
  email: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<UserResponse>;
  logout: () => Promise<void>;
  sendMessage: (
    message: string,
    pendingAction: PendingAction | null,
  ) => Promise<ProcessResponse>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// The access token's `sub` claim is the user's email (identity uses email as
// the subject). Used only as a fallback when the stored email is absent.
function decodeEmailFromToken(accessToken: string): string | null {
  try {
    const payload = accessToken.split(".")[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(normalized)) as { sub?: string };
    return decoded.sub ?? null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  // Tokens live in a ref so sendMessage always reads the latest value after a
  // mid-flight refresh (no stale closure); mirrored to localStorage for persistence.
  const tokensRef = useRef<{ access: string | null; refresh: string | null }>({
    access: null,
    refresh: null,
  });
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const persist = useCallback(
    (access: string, refreshToken: string, email: string) => {
      tokensRef.current = { access, refresh: refreshToken };
      if (typeof window !== "undefined") {
        localStorage.setItem(ACCESS_KEY, access);
        localStorage.setItem(REFRESH_KEY, refreshToken);
        localStorage.setItem(EMAIL_KEY, email);
      }
      setUser({ email });
    },
    [],
  );

  const clear = useCallback(() => {
    tokensRef.current = { access: null, refresh: null };
    if (typeof window !== "undefined") {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
      localStorage.removeItem(EMAIL_KEY);
    }
    setUser(null);
  }, []);

  // Rehydrate session from localStorage on first mount.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const access = localStorage.getItem(ACCESS_KEY);
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (access && refreshToken) {
      tokensRef.current = { access, refresh: refreshToken };
      const email =
        localStorage.getItem(EMAIL_KEY) ?? decodeEmailFromToken(access) ?? "";
      setUser({ email });
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await apiLogin(email, password);
      persist(tokens.access_token, tokens.refresh_token, email);
    },
    [persist],
  );

  const register = useCallback(
    (input: RegisterInput) => apiRegister(input),
    [],
  );

  const logout = useCallback(async () => {
    const refreshToken = tokensRef.current.refresh;
    try {
      if (refreshToken) await apiLogout(refreshToken);
    } catch {
      // Best-effort revoke; discard client tokens regardless.
    }
    clear();
    router.push("/login");
  }, [clear, router]);

  const sendMessage = useCallback(
    async (
      message: string,
      pendingAction: PendingAction | null,
    ): Promise<ProcessResponse> => {
      const access = tokensRef.current.access;
      if (!access) {
        clear();
        router.push("/login");
        throw new ApiError("Not authenticated", 401);
      }
      try {
        return await processMessage(access, message, pendingAction);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          const refreshToken = tokensRef.current.refresh;
          if (refreshToken) {
            try {
              const tokens = await apiRefresh(refreshToken);
              const email =
                user?.email ??
                decodeEmailFromToken(tokens.access_token) ??
                "";
              persist(tokens.access_token, tokens.refresh_token, email);
              return await processMessage(
                tokens.access_token,
                message,
                pendingAction,
              );
            } catch {
              // Refresh failed — fall through to logout.
            }
          }
          clear();
          router.push("/login");
        }
        throw err;
      }
    },
    [clear, persist, router, user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
      sendMessage,
    }),
    [user, isLoading, login, register, logout, sendMessage],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within <AuthProvider>");
  }
  return ctx;
}

// Route guard. Because the login endpoint rejects unverified users (403), the
// mere presence of tokens implies a verified account — so gating on
// authentication also enforces the email-verification requirement.
export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <div className="size-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );
  }

  return <>{children}</>;
}
