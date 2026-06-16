// Fetch-обёртка для бэкенда QazPostWeb (раздел 3 брифа).
// - Authorization: Bearer <token> на КАЖДЫЙ /api запрос (если есть токен).
// - 401 -> чистим токен и зовём глобальный обработчик (разлогин + /login).
// - 403 -> зовём обработчик («нет доступа»), бросаем ApiError.
// - PDF и прочее качаем как blob (responseType: 'blob').

const TOKEN_KEY = 'token';
let authToken: string | null = localStorage.getItem(TOKEN_KEY);

export function getToken(): string | null {
  return authToken;
}
export function setToken(token: string): void {
  authToken = token;
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken(): void {
  authToken = null;
  localStorage.removeItem(TOKEN_KEY);
}

// Глобальная реакция на 401/403. Регистрируется в AuthContext.
type AuthErrorHandler = (status: 401 | 403) => void;
let authErrorHandler: AuthErrorHandler | null = null;
export function setAuthErrorHandler(fn: AuthErrorHandler | null): void {
  authErrorHandler = fn;
}

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export interface ApiOptions extends Omit<RequestInit, 'body'> {
  /** JSON по умолчанию; URLSearchParams -> form-urlencoded (login); FormData/Blob — как есть. */
  body?: unknown;
  /** слать ли Bearer (по умолчанию true; для login — false) */
  auth?: boolean;
  /** как читать ответ */
  responseType?: 'json' | 'blob' | 'none';
}

const BASE = '/api';

export async function apiFetch<T = unknown>(path: string, opts: ApiOptions = {}): Promise<T> {
  const { body, auth = true, responseType = 'json', headers, ...rest } = opts;

  const finalHeaders = new Headers(headers);
  let finalBody: BodyInit | undefined;

  if (body instanceof URLSearchParams) {
    finalHeaders.set('Content-Type', 'application/x-www-form-urlencoded');
    finalBody = body;
  } else if (body instanceof FormData || body instanceof Blob) {
    finalBody = body; // Content-Type выставит браузер
  } else if (body !== undefined) {
    finalHeaders.set('Content-Type', 'application/json');
    finalBody = JSON.stringify(body);
  }

  if (auth && authToken) {
    finalHeaders.set('Authorization', `Bearer ${authToken}`);
  }

  const res = await fetch(`${BASE}${path}`, { ...rest, headers: finalHeaders, body: finalBody });

  if (res.status === 401) {
    clearToken();
    authErrorHandler?.(401);
    throw new ApiError(401, 'Не авторизован');
  }
  if (res.status === 403) {
    let detail: unknown;
    let message = 'Нет доступа';
    try {
      const data = await res.json();
      detail = (data as { detail?: unknown })?.detail ?? data;
      if (typeof (data as { detail?: unknown })?.detail === 'string') {
        message = (data as { detail: string }).detail;
      }
    } catch {
      /* тело не JSON — оставляем дефолтное сообщение */
    }
    authErrorHandler?.(403);
    throw new ApiError(403, message, detail);
  }

  if (!res.ok) {
    let detail: unknown;
    let message = `Ошибка ${res.status}`;
    try {
      const data = await res.json();
      detail = (data as { detail?: unknown })?.detail ?? data;
      if (typeof (data as { detail?: unknown })?.detail === 'string') {
        message = (data as { detail: string }).detail;
      }
    } catch {
      /* тело не JSON — оставляем дефолтное сообщение */
    }
    throw new ApiError(res.status, message, detail);
  }

  if (responseType === 'none' || res.status === 204) return undefined as T;
  if (responseType === 'blob') return (await res.blob()) as T;
  return (await res.json()) as T;
}
