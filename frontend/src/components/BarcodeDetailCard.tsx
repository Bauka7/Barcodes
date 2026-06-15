import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getBarcodeDetail } from '../api/barcodes';
import { Card, ErrorText, Loading } from './ui';
import { StatusBadge } from './StatusBadge';
import { Chip } from './Chip';

interface Props {
  barcode: string;
  canAct: boolean;
}

export function BarcodeDetailCard({ barcode }: Props) {
  const { t } = useTranslation();
  const key = ['barcode', 'detail', barcode];

  const { data, isLoading, isError, error } = useQuery({
    queryKey: key,
    queryFn: () => getBarcodeDetail(barcode),
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorText error={error} />;
  if (!data) return null;

  const rows: Array<[string, React.ReactNode]> = [
    [t('detail.batch'), `#${data.batch.id}`],
    [t('detail.packageType'), data.package_type],
    [t('detail.department'), data.department ? `${data.department.name} (${data.department.code})` : '—'],
    [
      t('detail.range'),
      data.range ? `#${data.range.id} · ${data.range.start_number}–${data.range.end_number}` : '—',
    ],
    [t('detail.sequence'), data.sequence_number],
    [t('lifecycle.generatedBy'), <span className="font-mono">{data.generated_by ?? data.batch.generated_by ?? '—'}</span>],
    [t('lifecycle.printedBy'), <span className="font-mono">{data.printed_by ?? '—'}</span>],
  ];

  return (
    <Card className="max-w-xl">
      <div className="mb-3 flex items-center justify-between gap-2">
        <span className="font-mono text-[20px] font-medium">{data.barcode}</span>
        <span className="flex gap-1.5">
          <StatusBadge status={data.status} />
          {data.printed ? (
            <StatusBadge status="printed" />
          ) : (
            <Chip tone="muted">{t('common.no')}</Chip>
          )}
        </span>
      </div>

      <table className="w-full text-[16px]">
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <td className="py-1 text-t2">{label}</td>
              <td className="py-1 text-right">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
