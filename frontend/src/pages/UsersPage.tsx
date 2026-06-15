import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { createUser, listUsers, updateUser } from '../api/users';
import type { DepartmentTreeItem, UserRead } from '../api/types';
import type { Role } from '../types';
import { useDepartmentTree } from '../lib/departmentName';
import { DataTable, type Column } from '../components/DataTable';
import { Chip, type ChipTone } from '../components/Chip';
import { Drawer } from '../components/Drawer';
import { Button, ErrorText, Field, Input, PageHeader, Select } from '../components/ui';

const ROLE_TONE: Record<string, ChipTone> = { admin: 'info', operator: 'ok', client: 'muted' };

const ROLE_LABELS: Record<Role, string> = {
  admin: 'Администратор',
  operator: 'Модератор',
  client: 'Пользователь отделения',
};

const ROLE_HELP: Record<Role, string> = {
  admin: 'Администратор видит всю систему. Подразделение необязательно.',
  operator: 'Модератор видит своё подразделение и все дочерние подразделения.',
  client: 'Пользователь видит только своё подразделение.',
};

type DepartmentOption = {
  id: number;
  label: string;
  displayName: string;
};

function flattenDepartmentOptions(nodes: DepartmentTreeItem[]): DepartmentOption[] {
  const out: DepartmentOption[] = [];

  const walk = (items: DepartmentTreeItem[], depth: number, parents: string[]) => {
    for (const item of items) {
      const code = item.code ? ` (${item.code})` : '';
      const prefix = depth === 0 ? '' : `${'—'.repeat(depth)} `;
      const fallbackPath = [...parents, item.name].join(' / ');
      const displayName = item.full_path || fallbackPath || item.name;

      out.push({
        id: item.id,
        label: `${prefix}${item.name}${code}`,
        displayName: `${displayName}${code}`,
      });

      if (item.children?.length) {
        walk(item.children, depth + 1, [...parents, item.name]);
      }
    }
  };

  walk(nodes, 0, []);
  return out;
}

export default function UsersPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: tree } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartmentOptions(tree ?? []), [tree]);
  const deptLabelById = useMemo(() => new Map(depts.map((d) => [d.id, d.displayName])), [depts]);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => listUsers({ limit: 100 }),
  });

  const [editing, setEditing] = useState<UserRead | null>(null);
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<Role>('operator');
  const [departmentId, setDepartmentId] = useState('');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (!open) return;
    setUsername(editing?.username ?? '');
    setPassword('');
    setFullName(editing?.full_name ?? '');
    setRole((editing?.role as Role) ?? 'operator');
    setDepartmentId(editing?.department_id ? String(editing.department_id) : '');
    setIsActive(editing?.is_active ?? true);
  }, [open, editing]);

  const roleRequiresDepartment = role === 'operator' || role === 'client';
  const missingRequiredDepartment = roleRequiresDepartment && !departmentId;
  const validCreate = editing ? true : username.trim().length > 0 && password.length > 0;
  const validSave = validCreate && !missingRequiredDepartment;

  const save = useMutation({
    mutationFn: () => {
      const dep = departmentId ? Number(departmentId) : null;
      if (editing) {
        return updateUser(editing.id, {
          full_name: fullName.trim() || undefined,
          role,
          department_id: dep,
          is_active: isActive,
        });
      }
      return createUser({
        username: username.trim(),
        password,
        full_name: fullName.trim() || undefined,
        role,
        department_id: dep,
        is_active: isActive,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] });
      setOpen(false);
      setEditing(null);
    },
  });

  const columns: Column<UserRead>[] = [
    { key: 'name', header: t('users.fullName'), render: (r) => r.full_name ?? '—' },
    { key: 'login', header: t('users.login'), render: (r) => <span className="font-mono">{r.username}</span> },
    {
      key: 'role',
      header: t('users.role'),
      render: (r) => {
        const roleValue = r.role as Role;
        return <Chip tone={ROLE_TONE[r.role] ?? 'muted'}>{ROLE_LABELS[roleValue] ?? r.role}</Chip>;
      },
    },
    {
      key: 'dept',
      header: t('lifecycle.dept'),
      render: (r) => (r.department_id == null ? '—' : (deptLabelById.get(r.department_id) ?? `#${r.department_id}`)),
    },
    {
      key: 'status',
      header: t('users.status'),
      render: (r) =>
        r.is_active ? (
          <span className="text-st">{t('users.activeStatus')}</span>
        ) : (
          <span className="text-t3">{t('users.inactiveStatus')}</span>
        ),
    },
    {
      key: 'edit',
      header: '',
      align: 'right',
      render: (r) => (
        <Button
          size="sm"
          onClick={() => {
            setEditing(r);
            setOpen(true);
          }}
        >
          <i className="ti ti-pencil" />
        </Button>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('users.title')}
        subtitle={t('users.subtitle')}
        actions={
          <Button
            variant="primary"
            onClick={() => {
              setEditing(null);
              setOpen(true);
            }}
          >
            <i className="ti ti-plus" /> {t('actions.add')}
          </Button>
        }
      />

      {isError ? (
        <ErrorText error={error} />
      ) : (
        <DataTable columns={columns} rows={data ?? []} rowKey={(r) => r.id} loading={isLoading} empty="—" />
      )}

      <Drawer open={open} onClose={() => setOpen(false)} title={editing ? t('users.edit') : t('users.new')}>
        <Field label={t('users.login')}>
          <Input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={!!editing}
            className="font-mono"
            placeholder="op_almaty"
          />
        </Field>
        {!editing && (
          <Field label={t('login.password')}>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
        )}
        <Field label={t('users.fullName')}>
          <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </Field>
        <Field label={t('users.role')}>
          <Select value={role} onChange={(e) => setRole(e.target.value as Role)}>
            <option value="admin">{ROLE_LABELS.admin}</option>
            <option value="operator">{ROLE_LABELS.operator}</option>
            <option value="client">{ROLE_LABELS.client}</option>
          </Select>
          <p className="mt-1 text-[14px] text-t2">{ROLE_HELP[role]}</p>
        </Field>
        <Field label={t('users.department')}>
          <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">{role === 'admin' ? 'Без подразделения' : 'Выберите подразделение'}</option>
            {depts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </Select>
          {missingRequiredDepartment && (
            <p className="mt-1 text-[14px] text-dt">Для этой роли нужно выбрать подразделение.</p>
          )}
        </Field>
        <Field>
          <label className="flex items-center justify-between text-[16px]">
            {t('users.active')}
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          </label>
        </Field>
        {save.isError && <ErrorText error={save.error} />}
        <div className="mt-3 flex gap-2">
          <Button variant="primary" className="flex-1" disabled={!validSave || save.isPending} onClick={() => save.mutate()}>
            {t('actions.save')}
          </Button>
          <Button onClick={() => setOpen(false)}>{t('actions.cancel')}</Button>
        </div>
      </Drawer>
    </div>
  );
}
