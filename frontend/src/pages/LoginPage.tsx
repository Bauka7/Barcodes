import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../auth/AuthContext';
import { LangSwitch } from '../components/LangSwitch';
import { ApiError } from '../api/client';

export default function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const ssoLoginEnabled = import.meta.env.VITE_SSO_LOGIN_ENABLED === 'true';

  // после входа — на стартовую по роли через HomeRedirect ('/'):
  // staff → Генерация, client → Мои диапазоны. Так никто не упирается в «Нет доступа».
  const dest = '/';

  // уже вошёл — на дашборд
  if (status === 'authenticated') {
    return <Navigate to={dest} replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(username.trim(), password); // POST /auth/login (form-urlencoded) + GET /auth/me
      navigate(dest, { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setError(t('login.invalid'));
      else setError(err instanceof Error ? err.message : t('login.failed'));
    } finally {
      setBusy(false);
    }
  }

  const inputCls =
    'w-full rounded-ctl border-[0.5px] border-bd2 bg-bg1 px-2.5 py-2 text-[16px] text-t1 outline-none focus:border-brand';

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg2 p-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-[360px] rounded-card border-[0.5px] border-bd3 bg-bg1 p-7"
      >
        <div className="mb-5 flex flex-col items-center gap-2.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-ctl bg-brand text-white">
            <i className="ti ti-barcode text-[34px]" />
          </div>
          <div className="text-center">
            <div className="text-xl font-medium">{t('login.title')}</div>
            <div className="text-[13px] text-t2">{t('login.subtitle')}</div>
          </div>
        </div>

        <label className="mb-1 block text-[15px] text-t2">{t('login.username')}</label>
        <input
          className={`${inputCls} mb-3`}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
          autoComplete="username"
        />

        <label className="mb-1 block text-[15px] text-t2">{t('login.password')}</label>
        <input
          type="password"
          className={inputCls}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          placeholder="••••••••"
        />

        {error && (
          <div className="mt-2 rounded-ctl bg-dx px-2.5 py-1.5 text-[13px] text-dt">{error}</div>
        )}

        <button
          type="submit"
          disabled={busy || !username || !password}
          className="mt-4 flex w-full items-center justify-center rounded-ctl bg-brand px-3 py-2 text-[16px] font-medium text-white disabled:opacity-60"
        >
          {busy ? t('login.submitting') : t('login.submit')}
        </button>

        {ssoLoginEnabled && (
          <button
            type="button"
            disabled
            className="mt-2 flex w-full items-center justify-center rounded-ctl border-[0.5px] border-bd2 bg-bg1 px-3 py-2 text-[16px] text-t1 disabled:opacity-60"
          >
            {t('login.sso')}
          </button>
        )}

        <div className="mt-4 flex justify-center">
          <LangSwitch />
        </div>
      </form>
    </div>
  );
}
