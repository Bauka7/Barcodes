import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { createClient, listClients, updateClient } from '../api/clients';
import type { ClientRead } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { DataTable, type Column } from '../components/DataTable';
import { Chip } from '../components/Chip';
import { Drawer } from '../components/Drawer';
import { Button, ErrorText, Field, Input, PageHeader, Textarea } from '../components/ui';

interface FormState {
  name: string;
  contact_person: string;
  contact_phone: string;
  email: string;
  notes: string;
  is_active: boolean;
}
const empty: FormState = { name: '', contact_person: '', contact_phone: '', email: '', notes: '', is_active: true };

export default function ClientsPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['clients'],
    queryFn: () => listClients({ limit: 100 }),
  });

  const [editing, setEditing] = useState<ClientRead | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<FormState>(empty);

  useEffect(() => {
    if (!open) return;
    setForm(
      editing
        ? {
            name: editing.name,
            contact_person: editing.contact_person ?? '',
            contact_phone: editing.contact_phone ?? '',
            email: editing.email ?? '',
            notes: editing.notes ?? '',
            is_active: editing.is_active,
          }
        : empty,
    );
  }, [open, editing]);

  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: form.name.trim(),
        contact_person: form.contact_person.trim() || undefined,
        contact_phone: form.contact_phone.trim() || undefined,
        email: form.email.trim() || undefined,
        notes: form.notes.trim() || undefined,
        is_active: form.is_active,
      };
      return editing ? updateClient(editing.id, body) : createClient(body);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clients'] });
      setOpen(false);
      setEditing(null);
    },
  });

  const columns: Column<ClientRead>[] = [
    { key: 'name', header: t('clients.name'), render: (r) => r.name },
    { key: 'contact', header: t('clients.contact'), render: (r) => r.contact_person ?? '—' },
    { key: 'phone', header: t('clients.phone'), render: (r) => r.contact_phone ?? '—' },
    { key: 'email', header: 'Email', render: (r) => <span className="text-t2">{r.email ?? '—'}</span> },
    {
      key: 'status',
      header: t('clients.status'),
      render: (r) =>
        r.is_active ? <Chip tone="ok">{t('clients.active')}</Chip> : <Chip tone="muted">{t('clients.inactive')}</Chip>,
    },
    {
      key: 'edit',
      header: '',
      align: 'right',
      render: (r) =>
        isAdmin ? (
          <Button
            size="sm"
            onClick={() => {
              setEditing(r);
              setOpen(true);
            }}
          >
            <i className="ti ti-pencil" />
          </Button>
        ) : null,
    },
  ];

  return (
    <div>
      <PageHeader
        title={t('clients.title')}
        subtitle={t('clients.subtitle')}
        actions={
          isAdmin ? (
            <Button
              variant="primary"
              onClick={() => {
                setEditing(null);
                setOpen(true);
              }}
            >
              <i className="ti ti-plus" /> {t('actions.add')}
            </Button>
          ) : undefined
        }
      />

      {isError ? (
        <ErrorText error={error} />
      ) : (
        <DataTable
          columns={columns}
          rows={data ?? []}
          rowKey={(r) => r.id}
          loading={isLoading}
          empty={t('clients.empty')}
        />
      )}

      <Drawer open={open} onClose={() => setOpen(false)} title={editing ? t('clients.edit') : t('actions.add')}>
        <Field label={t('clients.name')}>
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </Field>
        <Field label={t('clients.contact')}>
          <Input value={form.contact_person} onChange={(e) => setForm({ ...form, contact_person: e.target.value })} />
        </Field>
        <Field label={t('clients.phone')}>
          <Input value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} />
        </Field>
        <Field label="Email">
          <Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <Field label={t('gen.notes')}>
          <Textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </Field>
        <Field>
          <label className="flex items-center justify-between text-[16px]">
            {t('clients.active')}
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            />
          </label>
        </Field>
        {save.isError && <ErrorText error={save.error} />}
        <div className="mt-3 flex gap-2">
          <Button
            variant="primary"
            className="flex-1"
            disabled={!form.name.trim() || save.isPending}
            onClick={() => save.mutate()}
          >
            {t('actions.save')}
          </Button>
          <Button onClick={() => setOpen(false)}>{t('actions.cancel')}</Button>
        </div>
      </Drawer>
    </div>
  );
}
