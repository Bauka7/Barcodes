import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { listAuditLogs } from '../api/audit';
import type { AuditLogItem } from '../api/types';
import { DataTable, type Column } from '../components/DataTable';
import { Chip } from '../components/Chip';
import { Pagination } from '../components/Pagination';
import { ErrorText, Field, Input, PageHeader } from '../components/ui';

const LIMIT = 20;

function fmt(dt: string) {
  return new Date(dt).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AuditPage() {
  const { t } = useTranslation();
  const [action, setAction] = useState('');
  const [username, setUsername] = useState('');
  const [offset, setOffset] = useState(0);

  const params = {
    action: action || undefined,
    username: username || undefined,
    limit: LIMIT,
    offset,
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['audit', params],
    queryFn: () => listAuditLogs(params),
  });

  const columns: Column<AuditLogItem>[] = [
    { key: 'time', header: t('audit.time'), render: (r) => <span className="text-t2">{fmt(r.created_at)}</span> },
    { key: 'user', header: t('audit.user'), render: (r) => <span className="font-mono">{r.username ?? '—'}</span> },
    { key: 'action', header: t('audit.action'), render: (r) => <Chip tone="info">{r.action}</Chip> },
    {
      key: 'entity',
      header: t('audit.entity'),
      render: (r) => (r.entity_type ? `${r.entity_type} #${r.entity_id ?? ''}` : '—'),
    },
    { key: 'ip', header: 'IP', render: (r) => <span className="font-mono text-t2">{r.ip_address ?? '—'}</span> },
  ];

  return (
    <div>
      <PageHeader title={t('audit.title')} subtitle={t('audit.subtitle')} />

      <div className="mb-3 flex flex-wrap items-end gap-2">
        <Field label={t('audit.user')} className="mb-0 w-48">
          <Input
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
              setOffset(0);
            }}
            placeholder="admin"
          />
        </Field>
        <Field label={t('audit.action')} className="mb-0 w-56">
          <Input
            value={action}
            onChange={(e) => {
              setAction(e.target.value);
              setOffset(0);
            }}
            placeholder="barcode_generated"
          />
        </Field>
      </div>

      {isError ? (
        <ErrorText error={error} />
      ) : (
        <>
          <DataTable
            columns={columns}
            rows={data ?? []}
            rowKey={(r) => r.id}
            loading={isLoading}
            empty={t('audit.empty')}
          />
          <Pagination
            offset={offset}
            limit={LIMIT}
            shown={data?.length ?? 0}
            hasNext={(data?.length ?? 0) === LIMIT}
            onChange={setOffset}
          />
        </>
      )}
    </div>
  );
}
