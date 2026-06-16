import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { createUser, listUsers, updateUser } from '../api/users';
import type { DepartmentTreeItem, UserRead } from '../api/types';
import type { Role } from '../types';
import { useAuth } from '../auth/AuthContext';
import { useDepartmentTree } from '../lib/departmentName';
import { DataTable, type Column } from '../components/DataTable';
import { Chip, type ChipTone } from '../components/Chip';
import { DepartmentPicker } from '../components/DepartmentPicker';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { Modal } from '../components/Modal';
import { Button, Card, ErrorText, Field, Input, PageHeader, Select } from '../components/ui';

const ROLE_TONE: Record<string, ChipTone> = {
  admin: 'info',
  operator: 'ok',
  client: 'muted',
};

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
  displayName: string;
  shortName: string;
  searchText: string;
};

function flattenDepartmentOptions(nodes: DepartmentTreeItem[]): DepartmentOption[] {
  const out: DepartmentOption[] = [];

  const walk = (items: DepartmentTreeItem[], parents: string[]) => {
    for (const item of items) {
      const code = item.code ? ` (${item.code})` : '';
      const fallbackPath = [...parents, item.name].join(' / ');
      const displayName = item.full_path || fallbackPath || item.name;
      const shortName = `${item.name}${code}`;

      out.push({
        id: item.id,
        displayName: `${displayName}${code}`,
        shortName,
        searchText: `${displayName} ${shortName} ${item.code ?? ''}`.toLowerCase(),
      });

      if (item.children?.length) {
        walk(item.children, [...parents, item.name]);
      }
    }
  };

  walk(nodes, []);
  return out;
}

function normalize(value: string): string {
  return value.trim().toLowerCase();
}

function getInitials(fullName?: string | null, username?: string | null): string {
  const source = (fullName || username || '').trim();
  if (!source) return '??';

  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

  return `${parts[0][0] ?? ''}${parts[1][0] ?? ''}`.toUpperCase();
}

function UserAvatar({ fullName, username }: { fullName?: string | null; username?: string | null }) {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-bd3 bg-brand-tint text-[13px] font-semibold text-brand">
      {getInitials(fullName, username)}
    </div>
  );
}

export default function UsersPage() {
  const { t } = useTranslation();
  const { user: currentUser } = useAuth();
  const qc = useQueryClient();
  const menuRef = useRef<HTMLDivElement | null>(null);
  const { data: tree, isLoading: departmentsLoading } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartmentOptions(tree ?? []), [tree]);
  const deptById = useMemo(() => new Map(depts.map((dept) => [dept.id, dept])), [depts]);

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
  const [statusTarget, setStatusTarget] = useState<UserRead | null>(null);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<'all' | Role>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [menuOpenId, setMenuOpenId] = useState<number | null>(null);

  useEffect(() => {
    if (!open) return;
    setUsername(editing?.username ?? '');
    setPassword('');
    setFullName(editing?.full_name ?? '');
    setRole((editing?.role as Role) ?? 'operator');
    setDepartmentId(editing?.department_id ? String(editing.department_id) : '');
    setIsActive(editing?.is_active ?? true);
  }, [open, editing]);

  useEffect(() => {
    if (menuOpenId === null) return;

    const handlePointerDown = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpenId(null);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, [menuOpenId]);

  const roleRequiresDepartment = role === 'operator' || role === 'client';
  const missingRequiredDepartment = roleRequiresDepartment && !departmentId;
  const validCreate = editing ? true : username.trim().length > 0 && password.length > 0;
  const validSave = validCreate && !missingRequiredDepartment;

  const filteredUsers = useMemo(() => {
    const users = data ?? [];
    const searchValue = normalize(search);

    return users.filter((user) => {
      const dept = user.department_id == null ? null : deptById.get(user.department_id);
      const matchesSearch =
        searchValue.length === 0 ||
        `${user.full_name ?? ''} ${user.username} ${dept?.searchText ?? ''}`.toLowerCase().includes(searchValue);

      const matchesRole = roleFilter === 'all' || user.role === roleFilter;
      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && user.is_active) ||
        (statusFilter === 'inactive' && !user.is_active);
      const matchesDepartment =
        departmentFilter === 'all' || String(user.department_id ?? '') === departmentFilter;

      return matchesSearch && matchesRole && matchesStatus && matchesDepartment;
    });
  }, [data, deptById, departmentFilter, roleFilter, search, statusFilter]);

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

  const changeStatus = useMutation({
    mutationFn: (target: UserRead) =>
      updateUser(target.id, {
        is_active: !target.is_active,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] });
      setStatusTarget(null);
      setMenuOpenId(null);
    },
  });

  const columns: Column<UserRead>[] = [
    {
      key: 'name',
      header: t('users.fullName'),
      cellClassName: 'w-[36%]',
      render: (user) => (
        <div className="flex min-w-0 items-center gap-3">
          <UserAvatar fullName={user.full_name} username={user.username} />
          <div className="min-w-0">
            <div className="whitespace-normal break-words font-medium text-t1" title={user.full_name ?? user.username}>
              {user.full_name ?? '—'}
            </div>
            <div className="mt-0.5 whitespace-normal break-all font-mono text-[13px] text-t2" title={user.username}>
              {user.username}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: t('users.role'),
      cellClassName: 'w-[18%]',
      render: (user) => {
        const roleValue = user.role as Role;
        return <Chip tone={ROLE_TONE[user.role] ?? 'muted'}>{ROLE_LABELS[roleValue] ?? user.role}</Chip>;
      },
    },
    {
      key: 'dept',
      header: t('lifecycle.dept'),
      cellClassName: 'w-[28%]',
      render: (user) => {
        if (user.department_id == null) return <span className="text-t3">—</span>;
        const dept = deptById.get(user.department_id);
        return (
          <span
            className="block whitespace-normal break-words text-[15px] leading-5"
            title={dept?.displayName ?? `#${user.department_id}`}
          >
            {dept?.shortName ?? `#${user.department_id}`}
          </span>
        );
      },
    },
    {
      key: 'status',
      header: t('users.status'),
      cellClassName: 'w-[14%]',
      render: (user) => (
        <span
          className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[14px] font-medium ${
            user.is_active
              ? 'border border-success/25 bg-success/10 text-st'
              : 'border border-danger/25 bg-dx text-dt'
          }`}
        >
          <span className={`h-2 w-2 rounded-full ${user.is_active ? 'bg-success' : 'bg-danger'}`} />
          {user.is_active ? t('users.activeStatus') : t('users.inactiveStatus')}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      cellClassName: 'w-[4%]',
      render: (user) => {
        const isNearBottom = filteredUsers.findIndex((item) => item.id === user.id) >= filteredUsers.length - 2;

        return (
          <div className="flex justify-end">
            <div className="relative" ref={menuOpenId === user.id ? menuRef : undefined}>
              <Button
                size="sm"
                aria-label="Actions"
                title="Actions"
                onClick={() => setMenuOpenId((prev) => (prev === user.id ? null : user.id))}
              >
                <i className="ti ti-dots-vertical" />
              </Button>
              {menuOpenId === user.id && (
                <div
                  className={`absolute right-0 z-20 min-w-[220px] rounded-ctl border border-bd3 bg-bg1 p-1.5 shadow-xl ${
                    isNearBottom ? 'bottom-[calc(100%+6px)]' : 'top-[calc(100%+6px)]'
                  }`}
                >
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 rounded-ctl px-3 py-2 text-left text-[15px] text-t1 hover:bg-bg2"
                    onClick={() => {
                      setEditing(user);
                      setOpen(true);
                      setMenuOpenId(null);
                    }}
                  >
                    <i className="ti ti-pencil text-[16px]" />
                    {t('users.edit')}
                  </button>
                  <button
                    type="button"
                    disabled={user.id === currentUser?.id}
                    className="flex w-full items-center gap-2 rounded-ctl px-3 py-2 text-left text-[15px] text-t1 hover:bg-bg2 disabled:cursor-not-allowed disabled:opacity-50"
                    onClick={() => setStatusTarget(user)}
                  >
                    <i className={`ti ti-${user.is_active ? 'user-off' : 'user-check'} text-[16px]`} />
                    {user.is_active ? t('users.disable') : t('users.restore')}
                  </button>
                </div>
              )}
            </div>
          </div>
        );
      },
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

      <Card className="mb-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.3fr)_180px_180px_240px]">
          <Field className="mb-0">
            <div className="relative">
              <i className="ti ti-search pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-t3" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Поиск по ФИО, логину, отделу"
                className="pl-9"
              />
            </div>
          </Field>
          <Field className="mb-0">
            <Select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as 'all' | Role)}>
              <option value="all">Все роли</option>
              <option value="admin">{ROLE_LABELS.admin}</option>
              <option value="operator">{ROLE_LABELS.operator}</option>
              <option value="client">{ROLE_LABELS.client}</option>
            </Select>
          </Field>
          <Field className="mb-0">
            <Select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as 'all' | 'active' | 'inactive')}
            >
              <option value="all">Все статусы</option>
              <option value="active">{t('users.activeStatus')}</option>
              <option value="inactive">{t('users.inactiveStatus')}</option>
            </Select>
          </Field>
          <Field className="mb-0">
            <Select value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)}>
              <option value="all">Все отделы</option>
              {depts.map((dept) => (
                <option key={dept.id} value={String(dept.id)}>
                  {dept.shortName}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <div className="mt-3 flex items-center justify-between gap-3 text-[14px] text-t2">
          <span>Найдено: {filteredUsers.length}</span>
          <button
            type="button"
            className="text-brand hover:text-brand-dark"
            onClick={() => {
              setSearch('');
              setRoleFilter('all');
              setStatusFilter('all');
              setDepartmentFilter('all');
            }}
          >
            Сбросить фильтры
          </button>
        </div>
      </Card>

      {isError ? (
        <ErrorText error={error} />
      ) : (
        <DataTable
          columns={columns}
          rows={filteredUsers}
          rowKey={(user) => user.id}
          rowClassName={(user) => (user.is_active ? '' : 'bg-bg2/60')}
          loading={isLoading}
          empty="Пользователи не найдены"
          tableClassName="table-fixed"
        />
      )}

      {changeStatus.isError && (
        <div className="mt-3">
          <ErrorText error={changeStatus.error} />
        </div>
      )}

      <Modal
        open={open}
        onClose={() => {
          setOpen(false);
          setEditing(null);
        }}
        title={<div className="text-[22px] font-semibold leading-7">{editing ? t('users.edit') : t('users.new')}</div>}
        position="right"
        panelClassName="p-0"
      >
        <div className="flex h-full flex-col px-6 pb-6 pt-1">
          <Field label={t('users.login')} className="mb-4">
            <Input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              disabled={!!editing}
              className="font-mono"
              placeholder="op_almaty"
            />
          </Field>

          {!editing && (
            <Field label={t('login.password')} className="mb-4">
              <Input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </Field>
          )}

          <Field label={t('users.fullName')} className="mb-4">
            <Input value={fullName} onChange={(event) => setFullName(event.target.value)} />
          </Field>

          <Field label={t('users.role')} className="mb-2">
            <Select value={role} onChange={(event) => setRole(event.target.value as Role)}>
              <option value="admin">{ROLE_LABELS.admin}</option>
              <option value="operator">{ROLE_LABELS.operator}</option>
              <option value="client">{ROLE_LABELS.client}</option>
            </Select>
          </Field>
          <p className="mb-4 text-[14px] leading-6 text-t2">{ROLE_HELP[role]}</p>

          <Field label={t('users.department')} className="mb-2">
            <DepartmentPicker
              nodes={tree ?? []}
              value={departmentId ? Number(departmentId) : null}
              onChange={(id) => setDepartmentId(id === null ? '' : String(id))}
              allowClear={role === 'admin'}
              loading={departmentsLoading}
            />
          </Field>
          {missingRequiredDepartment && (
            <p className="mb-4 text-[14px] leading-6 text-dt">Для этой роли нужно выбрать подразделение.</p>
          )}

          <Field className="mb-5">
            <label className="flex items-center justify-between text-[16px]">
              <span>{t('users.active')}</span>
              <input type="checkbox" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />
            </label>
          </Field>

          {save.isError && (
            <div className="mb-4">
              <ErrorText error={save.error} />
            </div>
          )}

          <div className="flex items-center gap-3">
            <Button
              variant="primary"
              className="flex-1"
              disabled={!validSave || save.isPending}
              onClick={() => save.mutate()}
            >
              {t('actions.save')}
            </Button>
            <Button
              onClick={() => {
                setOpen(false);
                setEditing(null);
              }}
            >
              {t('actions.cancel')}
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={statusTarget !== null}
        title={statusTarget?.is_active ? t('users.disableTitle') : t('users.restoreTitle')}
        message={
          statusTarget
            ? t(statusTarget.is_active ? 'users.disableMessage' : 'users.restoreMessage', {
                name: statusTarget.full_name || statusTarget.username,
                username: statusTarget.username,
              })
            : undefined
        }
        confirmLabel={statusTarget?.is_active ? t('users.disable') : t('users.restore')}
        danger={statusTarget?.is_active}
        busy={changeStatus.isPending}
        onConfirm={() => statusTarget && changeStatus.mutate(statusTarget)}
        onCancel={() => setStatusTarget(null)}
      />
    </div>
  );
}
