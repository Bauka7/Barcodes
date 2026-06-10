import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  approveRangeRequest,
  createRangeRequest,
  listRangeRequests,
  rejectRangeRequest,
} from '../api/rangeRequests';
import { listClients } from '../api/clients';
import type { RangeRequestRead } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { flattenDepartments, useDepartmentTree } from '../lib/departmentName';
import { DataTable, type Column } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { Drawer } from '../components/Drawer';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { Button, ErrorText, Field, Input, PageHeader, Select, Textarea } from '../components/ui';

export default function RangeRequestsPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { user } = useAuth();
  const isStaff = user?.role === 'admin' || user?.role === 'operator';

  const { data: tree } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartments(tree ?? []), [tree]);

  const clientsQ = useQuery({ queryKey: ['clients'], queryFn: () => listClients({ limit: 100 }), enabled: isStaff });
  const clientName = useMemo(() => {
    const m = new Map<number, string>();
    for (const c of clientsQ.data ?? []) m.set(c.id, c.name);
    return m;
  }, [clientsQ.data]);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['range-requests'],
    queryFn: () => listRangeRequests({ limit: 100 }),
  });

  // создание
  const [open, setOpen] = useState(false);
  const [packageType, setPackageType] = useState('');
  const [quantity, setQuantity] = useState('100');
  const [clientId, setClientId] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [notes, setNotes] = useState('');

  const create = useMutation({
    mutationFn: () =>
      createRangeRequest({
        package_type: packageType.trim().toUpperCase(),
        requested_quantity: Number(quantity),
        request_type: 'issue_range',
        client_id: clientId ? Number(clientId) : undefined,
        department_id: departmentId ? Number(departmentId) : undefined,
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-requests'] });
      setOpen(false);
      setPackageType('');
      setQuantity('100');
      setClientId('');
      setDepartmentId('');
      setNotes('');
    },
  });

  // решение
  const [decision, setDecision] = useState<{ kind: 'approve' | 'reject'; id: number } | null>(null);
  const approve = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) => approveRangeRequest(id, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-requests'] });
      setDecision(null);
    },
  });
  const reject = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) => rejectRangeRequest(id, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-requests'] });
      setDecision(null);
    },
  });

  const columns: Column<RangeRequestRead>[] = [
    { key: 'id', header: '#', render: (r) => <span className="font-medium">{r.id}</span> },
    { key: 'type', header: t('requests.type'), render: (r) => r.package_type },
    { key: 'qty', header: t('requests.qty'), render: (r) => r.requested_quantity },
    {
      key: 'client',
      header: t('requests.client'),
      render: (r) => (r.client_id ? clientName.get(r.client_id) ?? `#${r.client_id}` : '—'),
    },
    { key: 'status', header: t('requests.status'), render: (r) => <StatusBadge status={r.status} domain="request" /> },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (r) =>
        isStaff && r.status === 'pending' ? (
          <span className="flex justify-end gap-1.5">
            <Button size="sm" variant="primary" onClick={() => setDecision({ kind: 'approve', id: r.id })}>
              {t('requests.approve')}
            </Button>
            <Button size="sm" onClick={() => setDecision({ kind: 'reject', id: r.id })}>
              {t('requests.reject')}
            </Button>
          </span>
        ) : (
          <span className="text-t3">—</span>
        ),
    },
  ];

  const validCreate = /^[A-Za-z]{2}$/.test(packageType.trim()) && Number(quantity) >= 1;

  return (
    <div>
      <PageHeader
        title={t('requests.title')}
        subtitle={t('requests.subtitle')}
        actions={
          <Button variant="primary" onClick={() => setOpen(true)}>
            <i className="ti ti-plus" /> {t('requests.new')}
          </Button>
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
          empty={t('requests.empty')}
        />
      )}

      <Drawer open={open} onClose={() => setOpen(false)} title={t('requests.new')}>
        <Field label={t('requests.type')}>
          <Input
            value={packageType}
            onChange={(e) => setPackageType(e.target.value.toUpperCase().slice(0, 2))}
            className="font-mono uppercase"
            placeholder="CV"
          />
        </Field>
        <Field label={t('requests.qty')}>
          <Input type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} />
        </Field>
        {isStaff && (
          <Field label={t('requests.client')}>
            <Select value={clientId} onChange={(e) => setClientId(e.target.value)}>
              <option value="">—</option>
              {(clientsQ.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
        )}
        <Field label={t('requests.department')}>
          <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">—</option>
            {depts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t('gen.notes')}>
          <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </Field>
        {create.isError && <ErrorText error={create.error} />}
        <div className="mt-3 flex gap-2">
          <Button variant="primary" className="flex-1" disabled={!validCreate || create.isPending} onClick={() => create.mutate()}>
            {t('actions.save')}
          </Button>
          <Button onClick={() => setOpen(false)}>{t('actions.cancel')}</Button>
        </div>
      </Drawer>

      <ConfirmDialog
        open={decision?.kind === 'approve'}
        title={t('requests.approveTitle')}
        confirmLabel={t('requests.approve')}
        input={{ label: t('actions.notesOptional') }}
        busy={approve.isPending}
        onConfirm={(notes) => decision && approve.mutate({ id: decision.id, notes })}
        onCancel={() => setDecision(null)}
      />
      <ConfirmDialog
        open={decision?.kind === 'reject'}
        title={t('requests.rejectTitle')}
        danger
        confirmLabel={t('requests.reject')}
        input={{ label: t('actions.notesOptional') }}
        busy={reject.isPending}
        onConfirm={(notes) => decision && reject.mutate({ id: decision.id, notes })}
        onCancel={() => setDecision(null)}
      />
    </div>
  );
}
