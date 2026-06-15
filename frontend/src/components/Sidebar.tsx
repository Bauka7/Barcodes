import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { Role } from '../types';
import { navForRole } from './navItems';
import { LangSwitch } from './LangSwitch';
import { ThemeToggle } from './ThemeToggle';
import { RoleBadge } from './RoleBadge';

interface Props {
  role: Role;
  onLogout: () => void;
  /** закрыть мобильный drawer при переходе */
  onNavigate?: () => void;
}

export function Sidebar({ role, onLogout, onNavigate }: Props) {
  const { t } = useTranslation();
  const items = navForRole(role);

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r-[0.5px] border-bd3 bg-bg2 p-4">
      {/* бренд */}
      <div className="flex items-center gap-2.5 px-1.5 pb-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-ctl bg-brand text-white">
          <i className="ti ti-barcode text-[24px]" />
        </div>
        <div className="text-[18px] font-medium">
          Barcodes
        </div>
      </div>

      {/* навигация (фильтр по роли) */}
      <nav className="flex flex-col gap-1 overflow-auto text-[16px]">
        {items.map((item) => (
          <NavLink
            key={item.key}
            to={item.path}
            onClick={() => onNavigate?.()}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-ctl px-3 py-2.5 ${
                isActive ? 'bg-brand-tint font-medium text-brand-dark' : 'text-t2 hover:bg-bg3 hover:text-t1'
              }`
            }
          >
            <i className={`ti ti-${item.icon} text-[22px]`} />
            {t(`nav.${item.key}`)}
          </NavLink>
        ))}
      </nav>

      {/* подвал: язык + тема, бейдж роли, выход */}
      <div className="mt-auto flex flex-col gap-3 pt-5">
        <div className="flex items-center justify-between">
          <LangSwitch />
          <ThemeToggle />
        </div>
        <RoleBadge role={role} />
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-2 text-[16px] text-t2 hover:text-t1"
        >
          <i className="ti ti-logout text-[20px]" />
          {t('shell.logout')}
        </button>
      </div>
    </aside>
  );
}
