import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { listLifecycle } from '../api/barcodes';
import type { GeneratedBarcodeItem } from '../api/types';
import { flattenDepartments, useDepartmentName, useDepartmentTree } from '../lib/departmentName';
import { DataTable, type Column } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { Chip } from '../components/Chip';
import { Pagination } from '../components/Pagination';
import { ErrorText, Field, PageHeader, Select } from '../components/ui';

const LIMIT = 20;

export default function LifecyclePage() {
  const { t } = useTranslation();
  const deptName = useDepartmentName();
  const { data: tree } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartments(tree ?? []), [tree]);

  const [status, setStatus] = useState('');
  const [printed, setPrinted] = useState('');
  const [packageType, setPackageType] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [offset, setOffset] = useState(0);

  const params = {
    status: status || undefined,
    printed: printed === '' ? undefined : printed === 'yes',
    package_type: packageType || undefined,
    department_id: departmentId ? Number(departmentId) : undefined,
    limit: LIMIT,
    offset,
  };

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['lifecycle', params],
    queryFn: () => listLifecycle(params),
  });

  const resetOffset = () => setOffset(0);

  const columns: Column<GeneratedBarcodeItem>[] = [
    { key: 'barcode', header: t('lifecycle.barcode'), render: (r) => <span className="font-mono">{r.barcode}</span> },
    { key: 'type', header: t('lifecycle.type'), render: (r) => r.package_type },
    { key: 'dept', header: t('lifecycle.dept'), render: (r) => deptName(r.department_id) },
    { key: 'generatedBy', header: t('lifecycle.generatedBy'), render: (r) => <span className="font-mono">{r.generated_by ?? '—'}</span> },
    { key: 'printedBy', header: t('lifecycle.printedBy'), render: (r) => <span className="font-mono">{r.printed_by ?? '—'}</span> },
    { key: 'status', header: t('lifecycle.status'), render: (r) => <StatusBadge status={r.status} /> },
    {
      key: 'printed',
      header: t('lifecycle.printed'),
      render: (r) =>
        r.printed ? <StatusBadge status="printed" /> : <Chip tone="muted">{t('common.no')}</Chip>,
    },
  ];

  return (
    <div>
      <PageHeader title={t('lifecycle.title')} subtitle={t('lifecycle.subtitle')} />

      <div className="mb-3 flex flex-wrap items-end gap-2">
        <Field label={t('lifecycle.status')} className="mb-0 w-40">
          <Select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              resetOffset();
            }}
          >
            <option value="">{t('lifecycle.allStatuses')}</option>
            <option value="generated">{t('status.barcode.generated')}</option>
            <option value="printed">{t('status.barcode.printed')}</option>
          </Select>
        </Field>
        <Field label={t('lifecycle.printed')} className="mb-0 w-36">
          <Select
            value={printed}
            onChange={(e) => {
              setPrinted(e.target.value);
              resetOffset();
            }}
          >
            <option value="">{t('lifecycle.printedAll')}</option>
            <option value="yes">{t('status.barcode.printed')}</option>
            <option value="no">{t('common.no')}</option>
          </Select>
        </Field>
        <Field label={t('lifecycle.type')} className="mb-0 w-28">
          <input
            className="w-full rounded-ctl border-[0.5px] border-bd2 bg-bg1 px-2.5 py-2 font-mono text-[16px] uppercase outline-none focus:border-brand"
            value={packageType}
            onChange={(e) => {
              setPackageType(e.target.value.toUpperCase().slice(0, 2));
              resetOffset();
            }}
          />
        </Field>
        <Field label={t('lifecycle.dept')} className="mb-0 w-56">
          <Select
            value={departmentId}
            onChange={(e) => {
              setDepartmentId(e.target.value);
              resetOffset();
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
            rows={data?.items ?? []}
            rowKey={(r) => r.id}
            loading={isLoading}
            empty={t('lifecycle.empty')}
          />
          <Pagination
            offset={offset}
            limit={LIMIT}
            shown={data?.items.length ?? 0}
            hasNext={(data?.items.length ?? 0) === LIMIT}
            onChange={setOffset}
          />
        </>
      )}
    </div>
  );
}
