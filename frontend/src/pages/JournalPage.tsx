import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listBatches } from '../api/barcodes';
import type { GeneratedBatchItem } from '../api/types';
import { flattenDepartments, useDepartmentName, useDepartmentTree } from '../lib/departmentName';
import { DataTable, type Column } from '../components/DataTable';
import { Chip } from '../components/Chip';
import { Pagination } from '../components/Pagination';
import { ErrorText, Field, PageHeader, Select } from '../components/ui';

const LIMIT = 20;

function fmt(dt: string) {
  const d = new Date(dt);
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export default function JournalPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const deptName = useDepartmentName();
  const { data: tree } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartments(tree ?? []), [tree]);

  const [packageType, setPackageType] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [offset, setOffset] = useState(0);

  const params = {
    package_type: packageType || undefined,
    department_id: departmentId ? Number(departmentId) : undefined,
    limit: LIMIT,
    offset,
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['batches', params],
    queryFn: () => listBatches(params),
  });

  const columns: Column<GeneratedBatchItem>[] = [
    { key: 'id', header: '#', render: (r) => <span className="font-medium">{r.id}</span> },
    { key: 'type', header: t('journal.type'), render: (r) => <Chip tone="info">{r.package_type}</Chip> },
    { key: 'dept', header: t('journal.dept'), render: (r) => deptName(r.department_id) },
    { key: 'qty', header: t('journal.qty'), render: (r) => r.quantity },
    { key: 'src', header: t('journal.source'), render: (r) => <span className="text-t2">{r.source ?? '—'}</span> },
    { key: 'date', header: t('journal.date'), render: (r) => <span className="text-t2">{fmt(r.generated_at)}</span> },
  ];

  return (
    <div>
      <PageHeader title={t('journal.title')} subtitle={t('journal.subtitle')} />

      <div className="mb-3 flex flex-wrap items-end gap-2">
        <Field label={t('journal.type')} className="mb-0 w-28">
          <input
            className="w-full rounded-ctl border-[0.5px] border-bd2 bg-bg1 px-2.5 py-2 font-mono text-[16px] uppercase outline-none focus:border-brand"
            value={packageType}
            onChange={(e) => {
              setPackageType(e.target.value.toUpperCase().slice(0, 2));
              setOffset(0);
            }}
          />
        </Field>
        <Field label={t('journal.dept')} className="mb-0 w-56">
          <Select
            value={departmentId}
            onChange={(e) => {
              setDepartmentId(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">{t('lifecycle.allDepts')}</option>
            {depts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
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
            empty={t('journal.empty')}
            onRowClick={(r) => navigate(`/journal/${r.id}`)}
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
