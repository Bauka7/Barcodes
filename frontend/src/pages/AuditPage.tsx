import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { listAuditLogs } from '../api/audit';
import type { AuditLogItem } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { Chip, type ChipTone } from '../components/Chip';
import { DataTable, type Column } from '../components/DataTable';
import { Pagination } from '../components/Pagination';
import { Button, ErrorText, Field, Input, PageHeader } from '../components/ui';

const LIMIT = 20;

function fmt(dt: string) {
  return new Date(dt).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function compactEntity(row: AuditLogItem) {
  if (!row.entity_type) return '-';
  return row.entity_id ? `${row.entity_type} #${row.entity_id}` : row.entity_type;
}

function prettyDetails(details: string | null) {
  if (!details) return '-';
  try {
    return JSON.stringify(JSON.parse(details), null, 2);
  } catch {
    return details;
  }
}

function actionGroup(action: string): { label: string; tone: ChipTone } {
  if (action.includes('login')) return { label: 'auth', tone: 'info' };
  if (action.includes('range')) return { label: 'range', tone: 'warn' };
  if (action.includes('barcode') || action.includes('shpi')) return { label: 'barcode', tone: 'ok' };
  if (action.includes('pdf') || action.includes('print')) return { label: 'print', tone: 'info' };
  if (action.includes('user')) return { label: 'user', tone: 'muted' };
  if (action.includes('department') || action.includes('filpassport')) return { label: 'department', tone: 'info' };
  return { label: 'system', tone: 'muted' };
}

export default function AuditPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [action, setAction] = useState('');
  const [username, setUsername] = useState('');
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [offset, setOffset] = useState(0);
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  const isAdmin = user?.role === 'admin';
  const params = {
    action: action || undefined,
    username: username || undefined,
    entity_type: entityType || undefined,
    entity_id: entityId || undefined,
    department_id: isAdmin && departmentId ? Number(departmentId) : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    limit: LIMIT,
    offset,
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['audit', params],
    queryFn: () => listAuditLogs(params),
  });

  const resetOffset = () => setOffset(0);
  const actionLabel = (value: string) => t(`audit.actions.${value}`, { defaultValue: value });

  const columns: Column<AuditLogItem>[] = [
    { key: 'time', header: t('audit.time'), render: (r) => <span className="text-t2">{fmt(r.created_at)}</span> },
    { key: 'user', header: t('audit.user'), render: (r) => <span className="font-mono">{r.username ?? '-'}</span> },
    {
      key: 'action',
      header: t('audit.action'),
      render: (r) => {
        const group = actionGroup(r.action);
        return (
          <div className="flex max-w-72 flex-wrap gap-1">
            <Chip tone={group.tone}>{group.label}</Chip>
            <Chip tone="muted">{actionLabel(r.action)}</Chip>
          </div>
        );
      },
    },
    { key: 'entity', header: t('audit.entity'), render: compactEntity },
    {
      key: 'department',
      header: t('audit.department'),
      render: (r) =>
        r.department_name ? (
          <div>
            <div>{r.department_name}</div>
            <div className="text-[13px] text-t3">{r.department_code ?? `ID ${r.department_id}`}</div>
          </div>
        ) : (
          <span className="text-t3">-</span>
        ),
    },
    { key: 'ip', header: t('audit.ip'), render: (r) => <span className="font-mono text-t2">{r.ip_address ?? '-'}</span> },
    {
      key: 'details',
      header: t('audit.details'),
      cellClassName: 'min-w-72',
      render: (r) => {
        if (!r.details) return <span className="text-t3">-</span>;
        const isExpanded = Boolean(expanded[r.id]);
        const details = prettyDetails(r.details);
        return (
          <div className="max-w-[520px]">
            <Button
              size="sm"
              onClick={() => setExpanded((prev) => ({ ...prev, [r.id]: !prev[r.id] }))}
            >
              {isExpanded ? t('audit.hideDetails') : t('audit.showDetails')}
            </Button>
            {isExpanded ? (
              <pre className="mt-2 max-h-56 overflow-auto rounded-ctl bg-bg2 p-2 text-[13px] text-t1">
                {details}
              </pre>
            ) : null}
          </div>
        );
      },
    },
  ];

  return (
    <div>
      <PageHeader
        title={isAdmin ? t('audit.adminTitle') : t('audit.operatorTitle')}
        subtitle={isAdmin ? t('audit.adminSubtitle') : t('audit.operatorSubtitle')}
      />

      <div className="mb-3 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
        <Field label={t('audit.user')} className="mb-0">
          <Input value={username} onChange={(e) => { setUsername(e.target.value); resetOffset(); }} placeholder="admin" />
        </Field>
        <Field label={t('audit.action')} className="mb-0">
          <Input value={action} onChange={(e) => { setAction(e.target.value); resetOffset(); }} placeholder="login_success" />
        </Field>
        <Field label={t('audit.entityType')} className="mb-0">
          <Input value={entityType} onChange={(e) => { setEntityType(e.target.value); resetOffset(); }} placeholder="barcode_range" />
        </Field>
        <Field label={t('audit.entityId')} className="mb-0">
          <Input value={entityId} onChange={(e) => { setEntityId(e.target.value); resetOffset(); }} placeholder="123" />
        </Field>
        {isAdmin ? (
          <Field label={t('audit.departmentId')} className="mb-0">
            <Input
              type="number"
              value={departmentId}
              onChange={(e) => { setDepartmentId(e.target.value); resetOffset(); }}
              placeholder="857"
            />
          </Field>
        ) : null}
        <Field label={t('audit.dateFrom')} className="mb-0">
          <Input type="datetime-local" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); resetOffset(); }} />
        </Field>
        <Field label={t('audit.dateTo')} className="mb-0">
          <Input type="datetime-local" value={dateTo} onChange={(e) => { setDateTo(e.target.value); resetOffset(); }} />
        </Field>
      </div>

      {isError ? (
        <ErrorText error={error} />
      ) : (
        <>
          <DataTable
            columns={columns}
            rows={data?.items ?? []}
            rowKey={(r) => r.id}
            loading={isLoading}
            empty={t('audit.empty')}
          />
          <Pagination
            offset={offset}
            limit={LIMIT}
            shown={data?.items.length ?? 0}
            total={data?.total}
            onChange={setOffset}
          />
        </>
      )}
    </div>
  );
}
