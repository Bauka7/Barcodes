import type { Role } from '../types';

// Цвет бейджа по роли (как в карточках ролей design-reference.html).
const ROLE_CHIP: Record<Role, string> = {
  admin: 'bg-brand-tint text-brand-dark',
  operator: 'bg-sx text-st',
  client: 'bg-bg3 text-t2',
};

export function RoleBadge({ role }: { role: Role }) {
  return (
    <span
      className={`inline-flex w-fit items-center gap-1.5 rounded-ctl px-2.5 py-0.5 text-[13px] ${ROLE_CHIP[role]}`}
    >
      <i className="ti ti-user-circle text-[13px]" />
      {role}
    </span>
  );
}
