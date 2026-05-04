import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getAuthToken, login as apiLogin, setAuthToken } from "@/api/client";

interface AuthState {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

function decodeJwtSub(token: string): string | null {
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    const parsed = JSON.parse(json) as { sub?: string };
    return parsed.sub || null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [loading, setLoading] = useState(false);

  const username = useMemo(() => (token ? decodeJwtSub(token) : null), [token]);

  const signIn = useCallback(async (u: string, p: string) => {
    setLoading(true);
    try {
      const res = await apiLogin(u, p);
      setToken(res.access_token);
    } finally {
      setLoading(false);
    }
  }, []);

  const signOut = useCallback(() => {
    setAuthToken(null);
    setToken(null);
  }, []);

  // Listen to storage changes from other tabs.
  useEffect(() => {
    const onStorage = () => setToken(getAuthToken());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const value: AuthState = {
    token,
    username,
    isAuthenticated: Boolean(token),
    loading,
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
