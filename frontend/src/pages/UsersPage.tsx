import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { createUser, listUsers, updateUser } from '../api/users';
import { listClients } from '../api/clients';
import type { UserRead } from '../api/types';
import type { Role } from '../types';
import { flattenDepartments, useDepartmentName, useDepartmentTree } from '../lib/departmentName';
import { DataTable, type Column } from '../components/DataTable';
import { Chip, type ChipTone } from '../components/Chip';
import { Drawer } from '../components/Drawer';
import { Button, ErrorText, Field, Input, PageHeader, Select } from '../components/ui';

const ROLE_TONE: Record<string, ChipTone> = { admin: 'info', operator: 'ok', client: 'muted' };

export default function UsersPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const deptName = useDepartmentName();
  const { data: tree } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartments(tree ?? []), [tree]);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => listUsers({ limit: 100 }),
  });

  // Организации нужны, чтобы привязать пользователя с ролью client.
  const clientsQ = useQuery({ queryKey: ['clients'], queryFn: () => listClients({ limit: 100 }) });

  const [editing, setEditing] = useState<UserRead | null>(null);
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<Role>('operator');
  const [departmentId, setDepartmentId] = useState('');
  const [clientId, setClientId] = useState('');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (!open) return;
    setUsername(editing?.username ?? '');
    setPassword('');
    setFullName(editing?.full_name ?? '');
    setRole((editing?.role as Role) ?? 'operator');
    setDepartmentId(editing?.department_id ? String(editing.department_id) : '');
    setClientId(editing?.client_id ? String(editing.client_id) : '');
    setIsActive(editing?.is_active ?? true);
  }, [open, editing]);

  const save = useMutation({
    mutationFn: () => {
      const dep = departmentId ? Number(departmentId) : undefined;
      // client_id обязателен для роли client (правило бэка); иначе не отправляем.
      const cli = role === 'client' && clientId ? Number(clientId) : undefined;
      if (editing) {
        return updateUser(editing.id, {
          full_name: fullName.trim() || undefined,
          role,
          department_id: dep,
          client_id: cli,
          is_active: isActive,
        });
      }
      return createUser({
        username: username.trim(),
        password,
        full_name: fullName.trim() || undefined,
        role,
        department_id: dep,
        client_id: cli,
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
    { key: 'role', header: t('users.role'), render: (r) => <Chip tone={ROLE_TONE[r.role] ?? 'muted'}>{r.role}</Chip> },
    { key: 'dept', header: t('lifecycle.dept'), render: (r) => deptName(r.department_id) },
    {
      key: 'status',
      header: t('clients.status'),
      render: (r) =>
        r.is_active ? (
          <span className="text-st">{t('clients.active')}</span>
        ) : (
          <span className="text-t3">{t('clients.inactive')}</span>
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

  // Роль client обязана иметь организацию (правило бэка).
  const clientOk = role !== 'client' || clientId !== '';
  const validCreate =
    (editing ? true : username.trim().length > 0 && password.length > 0) && clientOk;

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
            <option value="admin">admin</option>
            <option value="operator">operator</option>
            <option value="client">client</option>
          </Select>
        </Field>
        <Field label={t('users.department')}>
          <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">—</option>
            {depts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </Field>
        {role === 'client' && (
          <Field label={t('users.client')}>
            <Select value={clientId} onChange={(e) => setClientId(e.target.value)}>
              <option value="">{t('users.clientPh')}</option>
              {(clientsQ.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
        )}
        <Field>
          <label className="flex items-center justify-between text-[16px]">
            {t('users.active')}
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          </label>
        </Field>
        {save.isError && <ErrorText error={save.error} />}
        <div className="mt-3 flex gap-2">
          <Button variant="primary" className="flex-1" disabled={!validCreate || save.isPending} onClick={() => save.mutate()}>
            {t('actions.save')}
          </Button>
          <Button onClick={() => setOpen(false)}>{t('actions.cancel')}</Button>
        </div>
      </Drawer>
    </div>
  );
}
