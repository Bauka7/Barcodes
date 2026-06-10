import type { Role } from '../types';

// Модель пункта сайдбара. label берётся из i18n по ключу `nav.<key>`,
// icon — имя Tabler-иконки (без префикса `ti ti-`).
export interface NavItem {
  key: string;
  path: string;
  icon: string;
  roles: Role[];
}

// Навигация по ролям — раздел 6 брифа («выверено по бэку»).
// admin: всё. operator: всё кроме Пользователи/Аудит/Настройки (Клиенты — просмотр).
// client: только Генерация и свои Заявки (остальное скрыто, на бэке 403).
export const NAV_ITEMS: NavItem[] = [
  { key: 'generate', path: '/generate', icon: 'plus', roles: ['admin', 'operator', 'client'] },
  { key: 'journal', path: '/journal', icon: 'history', roles: ['admin', 'operator'] },
  { key: 'search', path: '/search', icon: 'search', roles: ['admin', 'operator'] },
  { key: 'lifecycle', path: '/lifecycle', icon: 'refresh', roles: ['admin', 'operator'] },
  { key: 'print', path: '/print', icon: 'printer', roles: ['admin', 'operator'] },
  { key: 'departments', path: '/departments', icon: 'sitemap', roles: ['admin', 'operator'] },
  { key: 'ranges', path: '/ranges', icon: 'ruler-2', roles: ['admin', 'operator'] },
  { key: 'requests', path: '/range-requests', icon: 'inbox', roles: ['admin', 'operator', 'client'] },
  { key: 'clients', path: '/clients', icon: 'building-store', roles: ['admin', 'operator'] },
  { key: 'users', path: '/users', icon: 'users', roles: ['admin'] },
  { key: 'audit', path: '/audit', icon: 'clipboard-list', roles: ['admin'] },
  { key: 'settings', path: '/settings', icon: 'settings', roles: ['admin'] },
];

export function navForRole(role: Role): NavItem[] {
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}
