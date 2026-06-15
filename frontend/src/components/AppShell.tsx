import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../auth/AuthContext';
import { Sidebar } from './Sidebar';

// Каркас: сайдбар (десктоп — статичный, мобильный — выезжающий бургер) + контент
// в центрированном контейнере с адаптивными отступами.
export function AppShell() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const role = user?.role ?? 'client';
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="flex h-screen bg-bg3 text-t1">
      {/* десктоп */}
      <div className="hidden lg:block">
        <Sidebar role={role} onLogout={logout} />
      </div>

      {/* мобильный drawer */}
      {navOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/30" onClick={() => setNavOpen(false)} />
          <div className="relative h-full w-64">
            <Sidebar role={role} onLogout={logout} onNavigate={() => setNavOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        {/* мобильная шапка */}
        <header className="flex items-center gap-3 border-b-[0.5px] border-bd3 bg-bg2 px-4 py-3 lg:hidden">
          <button type="button" onClick={() => setNavOpen(true)} aria-label={t('shell.menu')} className="text-t1">
            <i className="ti ti-menu-2 text-2xl" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-ctl bg-brand text-white">
              <i className="ti ti-barcode" />
            </div>
            <span className="font-medium">
              Barcodes
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-bg1">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-10 lg:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
