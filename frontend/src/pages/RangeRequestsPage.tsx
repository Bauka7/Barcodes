import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  approveRangeRequest,
  cancelRangeRequest,
  createRangeRequest,
  listRangeRequests,
  rejectRangeRequest,
} from '../api/rangeRequests';
import { listClients } from '../api/clients';
import { listBarcodeCodes } from '../api/barcodeCodes';
import type { RangeRequestRead } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { flattenDepartments, useDepartmentName, useDepartmentTree } from '../lib/departmentName';
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
  const deptName = useDepartmentName();

  const { data: tree } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartments(tree ?? []), [tree]);

  const clientsQ = useQuery({
    queryKey: ['clients'],
    queryFn: () => listClients({ limit: 100 }),
    enabled: isStaff,
  });
  const clientName = useMemo(() => {
    const m = new Map<number, string>();
    for (const c of clientsQ.data ?? []) m.set(c.id, c.name);
    return m;
  }, [clientsQ.data]);

  // Справочник кодов для одобрения (только сотрудники).
  const codesQ = useQuery({
    queryKey: ['barcode-codes'],
    queryFn: () => listBarcodeCodes({ limit: 100 }),
    enabled: isStaff,
  });

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['range-requests'],
    queryFn: () => listRangeRequests({ limit: 100 }),
  });

  // ── создание заявки-потребности ───────────────────────────────
  const [open, setOpen] = useState(false);
  const [purpose, setPurpose] = useState('');
  const [quantity, setQuantity] = useState('100');
  const [requestedCode, setRequestedCode] = useState('');
  const [clientId, setClientId] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [notes, setNotes] = useState('');

  const resetCreate = () => {
    setPurpose('');
    setQuantity('100');
    setRequestedCode('');
    setClientId('');
    setDepartmentId('');
    setNotes('');
  };

  const create = useMutation({
    mutationFn: () =>
      createRangeRequest({
        purpose: purpose.trim(),
        requested_quantity: Number(quantity),
        department_id: Number(departmentId),
        requested_code: requestedCode.trim() ? requestedCode.trim().toUpperCase() : undefined,
        request_type: 'issue_range',
        client_id: isStaff && clientId ? Number(clientId) : undefined,
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-requests'] });
      setOpen(false);
      resetCreate();
    },
  });

  // ── решение по заявке ─────────────────────────────────────────
  const [decision, setDecision] = useState<
    { kind: 'reject' | 'cancel'; id: number } | null
  >(null);
  const [approveFor, setApproveFor] = useState<RangeRequestRead | null>(null);
  const [approveCode, setApproveCode] = useState('');
  const [approveNotes, setApproveNotes] = useState('');

  const openApprove = (r: RangeRequestRead) => {
    setApproveFor(r);
    setApproveCode((r.requested_code ?? '').toUpperCase());
    setApproveNotes('');
  };

  const approve = useMutation({
    mutationFn: ({ id, code, notes }: { id: number; code: string; notes: string }) =>
      approveRangeRequest(id, code, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-requests'] });
      setApproveFor(null);
    },
  });
  const reject = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) =>
      rejectRangeRequest(id, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-requests'] });
      setDecision(null);
    },
  });
  const cancel = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes: string }) =>
      cancelRangeRequest(id, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-requests'] });
      setDecision(null);
    },
  });

  const codeCell = (r: RangeRequestRead) => {
    if (r.approved_code) return <span className="font-mono font-medium">{r.approved_code}</span>;
    if (r.requested_code) return <span className="font-mono text-t2">{r.requested_code}?</span>;
    return <span className="text-t3">—</span>;
  };

  const columns: Column<RangeRequestRead>[] = [
    { key: 'id', header: '#', render: (r) => <span className="font-medium">{r.id}</span> },
    {
      key: 'purpose',
      header: t('requests.purpose'),
      render: (r) => <span className="line-clamp-2 max-w-[260px]">{r.purpose ?? '—'}</span>,
    },
    { key: 'qty', header: t('requests.qty'), render: (r) => r.requested_quantity },
    { key: 'code', header: t('requests.code'), render: codeCell },
    {
      key: 'department',
      header: t('requests.department'),
      render: (r) => deptName(r.department_id),
    },
    {
      key: 'client',
      header: t('requests.client'),
      render: (r) => (r.client_id ? (clientName.get(r.client_id) ?? `#${r.client_id}`) : '—'),
    },
    {
      key: 'status',
      header: t('requests.status'),
      render: (r) => <StatusBadge status={r.status} domain="request" />,
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (r) => {
        if (r.status !== 'pending') return <span className="text-t3">—</span>;
        if (isStaff) {
          return (
            <span className="flex justify-end gap-1.5">
              <Button size="sm" variant="primary" onClick={() => openApprove(r)}>
                {t('requests.approve')}
              </Button>
              <Button size="sm" onClick={() => setDecision({ kind: 'reject', id: r.id })}>
                {t('requests.reject')}
              </Button>
            </span>
          );
        }
        // клиент может отменить свою заявку, пока она pending
        return (
          <span className="flex justify-end">
            <Button size="sm" onClick={() => setDecision({ kind: 'cancel', id: r.id })}>
              {t('requests.cancel')}
            </Button>
          </span>
        );
      },
    },
  ];

  const validCreate =
    purpose.trim().length > 0 &&
    Number(quantity) >= 1 &&
    departmentId !== '' &&
    (requestedCode.trim() === '' || /^[A-Za-z]{2}$/.test(requestedCode.trim()));

  const validApprove = /^[A-Za-z]{2}$/.test(approveCode.trim());

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

      {/* Создание заявки-потребности */}
      <Drawer open={open} onClose={() => setOpen(false)} title={t('requests.new')}>
        <Field label={t('requests.purpose')}>
          <Textarea
            rows={2}
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder={t('requests.purposePh')}
          />
        </Field>
        <Field label={t('requests.qty')}>
          <Input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />
        </Field>
        <Field label={t('requests.department')}>
          <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">{t('requests.departmentPh')}</option>
            {depts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_path ?? d.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t('requests.requestedCode')}>
          <Input
            value={requestedCode}
            onChange={(e) => setRequestedCode(e.target.value.toUpperCase().slice(0, 2))}
            className="font-mono uppercase"
            placeholder={t('requests.requestedCodePh')}
          />
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
        <Field label={t('gen.notes')}>
          <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </Field>
        {create.isError && <ErrorText error={create.error} />}
        <div className="mt-3 flex gap-2">
          <Button
            variant="primary"
            className="flex-1"
            disabled={!validCreate || create.isPending}
            onClick={() => create.mutate()}
          >
            {t('actions.save')}
          </Button>
          <Button onClick={() => setOpen(false)}>{t('actions.cancel')}</Button>
        </div>
      </Drawer>

      {/* Одобрение: модератор назначает код из справочника */}
      <Drawer open={!!approveFor} onClose={() => setApproveFor(null)} title={t('requests.approveTitle')}>
        {approveFor && (
          <>
            <div className="mb-3 rounded-ctl bg-bg2 px-3 py-2 text-[15px]">
              <div className="text-t2">{t('requests.purpose')}</div>
              <div className="mb-1">{approveFor.purpose ?? '—'}</div>
              <div className="text-t2">
                {t('requests.qty')}: <span className="text-t1">{approveFor.requested_quantity}</span>
              </div>
            </div>
            <Field label={t('requests.code')}>
              <Select value={approveCode} onChange={(e) => setApproveCode(e.target.value)}>
                <option value="">{t('requests.codePh')}</option>
                {(codesQ.data ?? []).map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.code}
                    {c.name ? ` — ${c.name}` : ''} ({c.status})
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t('actions.notesOptional')}>
              <Textarea
                rows={2}
                value={approveNotes}
                onChange={(e) => setApproveNotes(e.target.value)}
              />
            </Field>
            {approve.isError && <ErrorText error={approve.error} />}
            <div className="mt-3 flex gap-2">
              <Button
                variant="primary"
                className="flex-1"
                disabled={!validApprove || approve.isPending}
                onClick={() =>
                  approve.mutate({
                    id: approveFor.id,
                    code: approveCode.trim().toUpperCase(),
                    notes: approveNotes,
                  })
                }
              >
                {t('requests.approve')}
              </Button>
              <Button onClick={() => setApproveFor(null)}>{t('actions.cancel')}</Button>
            </div>
          </>
        )}
      </Drawer>

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
      <ConfirmDialog
        open={decision?.kind === 'cancel'}
        title={t('requests.cancelTitle')}
        confirmLabel={t('requests.cancel')}
        input={{ label: t('actions.notesOptional') }}
        busy={cancel.isPending}
        onConfirm={(notes) => decision && cancel.mutate({ id: decision.id, notes })}
        onCancel={() => setDecision(null)}
      />
    </div>
  );
}
