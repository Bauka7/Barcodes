import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { clearToken, getToken, setAuthErrorHandler, setToken } from '../api/client';
import { getMe, login as apiLogin, type Me } from '../api/auth';

type Status = 'loading' | 'authenticated' | 'unauthenticated';

interface AuthValue {
  status: Status;
  user: Me | null;
  login: (username: string, password: string) => Promise<Me>;
  refreshUser: () => Promise<Me>;
  logout: () => void;
}

const AuthCtx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [user, setUser] = useState<Me | null>(null);
  // если токен уже сохранён — проверяем его через /me ('loading')
  const [status, setStatus] = useState<Status>(() =>
    getToken() ? 'loading' : 'unauthenticated',
  );

  const clearSessionCache = useCallback(() => {
    void queryClient.cancelQueries();
    queryClient.clear();
  }, [queryClient]);

  const logout = useCallback(() => {
    clearToken();
    clearSessionCache();
    setUser(null);
    setStatus('unauthenticated');
    navigate('/login', { replace: true });
  }, [clearSessionCache, navigate]);

  // Глобальная обработка 401/403 из client.ts (раздел 3 брифа).
  useEffect(() => {
    setAuthErrorHandler((s) => {
      if (s === 401) {
        clearToken();
        clearSessionCache();
        setUser(null);
        setStatus('unauthenticated');
        navigate('/login', { replace: true });
      }
      // 403: пользователь валиден, но прав нет — «нет доступа» показывают
      // ProtectedRoute (по роли) или сама страница; глобально не разлогиниваем.
    });
    return () => setAuthErrorHandler(null);
  }, [clearSessionCache, navigate]);

  // Восстановление сессии по сохранённому токену при загрузке.
  useEffect(() => {
    if (!getToken()) return;
    let alive = true;
    getMe()
      .then((me) => {
        if (alive) {
          setUser(me);
          setStatus('authenticated');
        }
      })
      .catch(() => {
        if (alive) {
          clearToken();
          clearSessionCache();
          setUser(null);
          setStatus('unauthenticated');
        }
      });
    return () => {
      alive = false;
    };
  }, [clearSessionCache]);

  const login = useCallback(async (username: string, password: string) => {
    await queryClient.cancelQueries();
    queryClient.clear();
    try {
      const { access_token } = await apiLogin(username, password);
      setToken(access_token);
      const me = await getMe();
      setUser(me);
      setStatus('authenticated');
      return me;
    } catch (error) {
      clearToken();
      queryClient.clear();
      setUser(null);
      setStatus('unauthenticated');
      throw error;
    }
  }, [queryClient]);

  const refreshUser = useCallback(async () => {
    const me = await getMe();
    setUser(me);
    setStatus('authenticated');
    return me;
  }, []);

  return <AuthCtx.Provider value={{ status, user, login, refreshUser, logout }}>{children}</AuthCtx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthValue {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
