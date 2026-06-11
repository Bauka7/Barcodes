import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { listBarcodeCodes } from '../api/barcodeCodes';
import type { BarcodeCodeRead } from '../api/types';
import { DataTable, type Column } from '../components/DataTable';
import { Chip, type ChipTone } from '../components/Chip';
import { ErrorText, PageHeader } from '../components/ui';

const STATUS_TONE: Record<string, ChipTone> = {
  available: 'info',
  active: 'ok',
  reserved: 'warn',
  blocked: 'bad',
  deprecated: 'muted',
};

export default function CodesPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['barcode-codes'],
    queryFn: () => listBarcodeCodes({ limit: 100 }),
  });

  const columns: Column<BarcodeCodeRead>[] = [
    { key: 'code', header: t('codes.code'), render: (c) => <span className="font-mono font-medium">{c.code}</span> },
    { key: 'name', header: t('codes.name'), render: (c) => c.name ?? '—' },
    { key: 'category', header: t('codes.category'), render: (c) => c.category ?? '—' },
    {
      key: 'status',
      header: t('codes.status'),
      render: (c) => <Chip tone={STATUS_TONE[c.status] ?? 'muted'}>{c.status}</Chip>,
    },
    { key: 'owner', header: t('codes.owner'), render: (c) => c.owner ?? '—' },
  ];

  return (
    <div>
      <PageHeader title={t('codes.title')} subtitle={t('codes.subtitle')} />
      {isError ? (
        <ErrorText error={error} />
      ) : (
        <DataTable
          columns={columns}
          rows={data ?? []}
          rowKey={(c) => c.code}
          loading={isLoading}
          empty={t('codes.empty')}
        />
      )}
    </div>
  );
}
