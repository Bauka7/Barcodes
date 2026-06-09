import {
  Barcode,
  Building2,
  FileClock,
  FileText,
  History,
  LogOut,
  Moon,
  Search,
  Sparkles,
  Sun,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";
import { useI18n } from "../i18n";

const navItems = [
  { to: "/app/departments", labelKey: "departments", icon: Building2 },
  { to: "/app/generate", labelKey: "generate", icon: Sparkles },
  { to: "/app/history", labelKey: "history", icon: History },
  { to: "/app/search", labelKey: "search", icon: Search },
  { to: "/app/pdf", labelKey: "pdf", icon: FileText },
  { to: "/app/print-history", labelKey: "printHistory", icon: FileClock },
] as const;

type Theme = "light" | "dark";

const THEME_STORAGE_KEY = "qazpost.theme";

function getInitialTheme(): Theme {
  return localStorage.getItem(THEME_STORAGE_KEY) === "dark" ? "dark" : "light";
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const { language, setLanguage, t } = useI18n();
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.body.classList.toggle("dark", theme === "dark");
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  function toggleTheme(): void {
    setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"));
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Barcode size={18} />
        </div>
        <div>
          <div className="brand-name">QazPost</div>
          <div className="brand-subtitle">SHPI</div>
        </div>
      </div>

      <nav className="nav-list" aria-label="Main navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              <Icon size={16} />
              <span>{t(item.labelKey)}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="ghost-button theme-toggle" type="button" onClick={toggleTheme}>
          {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
          <span>{theme === "dark" ? "Light" : "Dark"}</span>
        </button>

        <div className="segmented" aria-label="Language">
          <button
            className={language === "ru" ? "active" : ""}
            type="button"
            onClick={() => setLanguage("ru")}
          >
            RU
          </button>
          <button
            className={language === "kk" ? "active" : ""}
            type="button"
            onClick={() => setLanguage("kk")}
          >
            ҚАЗ
          </button>
        </div>

        <div className="user-panel">
          <div className="role-badge">{user?.role ?? "operator"}</div>
          <div className="user-name">{user?.username ?? "unknown"}</div>
        </div>

        <button className="ghost-button logout-button" type="button" onClick={logout}>
          <LogOut size={15} />
          <span>{t("logout")}</span>
        </button>
      </div>
    </aside>
  );
}
