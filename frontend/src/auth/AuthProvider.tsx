import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { getCurrentUser, loginRequest } from "../api/authApi";
import { clearStoredToken, getStoredToken, setStoredToken } from "../api/http";
import type { UserRead } from "../api/types";

interface AuthContextValue {
  token: string | null;
  user: UserRead | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const storedToken = getStoredToken();

    if (!storedToken) {
      setLoading(false);
      setUser(null);
      setToken(null);
      return;
    }

    try {
      setLoading(true);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setToken(storedToken);
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  }, [logout]);

  async function login(username: string, password: string): Promise<void> {
    const tokenResponse = await loginRequest(username, password);
    setStoredToken(tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    const currentUser = await getCurrentUser();
    setUser(currentUser);
  }

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  useEffect(() => {
    window.addEventListener("qazpost:unauthorized", logout);
    return () => window.removeEventListener("qazpost:unauthorized", logout);
  }, [logout]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      loading,
      login,
      logout,
      refreshUser,
    }),
    [loading, refreshUser, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
