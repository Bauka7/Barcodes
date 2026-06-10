import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { clearToken, getToken, setAuthErrorHandler, setToken } from '../api/client';
import { getMe, login as apiLogin, type Me } from '../api/auth';

type Status = 'loading' | 'authenticated' | 'unauthenticated';

interface AuthValue {
  status: Status;
  user: Me | null;
  login: (username: string, password: string) => Promise<Me>;
  logout: () => void;
}

const AuthCtx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<Me | null>(null);
  // если токен уже сохранён — проверяем его через /me ('loading')
  const [status, setStatus] = useState<Status>(() =>
    getToken() ? 'loading' : 'unauthenticated',
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setStatus('unauthenticated');
    navigate('/login', { replace: true });
  }, [navigate]);

  // Глобальная обработка 401/403 из client.ts (раздел 3 брифа).
  useEffect(() => {
    setAuthErrorHandler((s) => {
      if (s === 401) {
        clearToken();
        setUser(null);
        setStatus('unauthenticated');
        navigate('/login', { replace: true });
      }
      // 403: пользователь валиден, но прав нет — «нет доступа» показывают
      // ProtectedRoute (по роли) или сама страница; глобально не разлогиниваем.
    });
    return () => setAuthErrorHandler(null);
  }, [navigate]);

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
          setUser(null);
          setStatus('unauthenticated');
        }
      });
    return () => {
      alive = false;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await apiLogin(username, password);
    setToken(access_token);
    const me = await getMe();
    setUser(me);
    setStatus('authenticated');
    return me;
  }, []);

  return <AuthCtx.Provider value={{ status, user, login, logout }}>{children}</AuthCtx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthValue {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
