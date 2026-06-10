import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { cancelBarcode, getBarcodeDetail, markBarcodeUsed } from '../api/barcodes';
import { Button, Card, ErrorText, Loading } from './ui';
import { StatusBadge } from './StatusBadge';
import { Chip } from './Chip';
import { ConfirmDialog } from './ConfirmDialog';

interface Props {
  barcode: string;
  /** admin/operator — показывать действия отмены/использования */
  canAct: boolean;
}

const actionable = (status: string) => status !== 'used' && status !== 'cancelled';

export function BarcodeDetailCard({ barcode, canAct }: Props) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const key = ['barcode', 'detail', barcode];

  const { data, isLoading, isError, error } = useQuery({
    queryKey: key,
    queryFn: () => getBarcodeDetail(barcode),
  });

  const [dialog, setDialog] = useState<'cancel' | 'use' | null>(null);

  const cancelMut = useMutation({
    mutationFn: (reason: string) => cancelBarcode(barcode, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key });
      setDialog(null);
    },
  });
  const useMut = useMutation({
    mutationFn: (notes: string) => markBarcodeUsed(barcode, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key });
      setDialog(null);
    },
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorText error={error} />;
  if (!data) return null;

  const showActions = canAct && actionable(data.status);

  const rows: Array<[string, React.ReactNode]> = [
    [t('detail.batch'), `#${data.batch.id}`],
    [t('detail.packageType'), data.package_type],
    [t('detail.department'), data.department?.name ?? '—'],
    [
      t('detail.range'),
      data.range ? `#${data.range.id} · ${data.range.start_number}–${data.range.end_number}` : '—',
    ],
    [t('detail.sequence'), data.sequence_number],
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

      {data.status === 'cancelled' && data.cancellation_reason && (
        <p className="mt-2 text-[15px] text-t3">
          {t('detail.cancelReason')}: {data.cancellation_reason}
        </p>
      )}

      {showActions && (
        <div className="mt-3 flex gap-2">
          <Button size="sm" onClick={() => setDialog('use')}>
            {t('actions.markUsed')}
          </Button>
          <Button size="sm" variant="danger" onClick={() => setDialog('cancel')}>
            <i className="ti ti-x" /> {t('actions.cancel2')}
          </Button>
        </div>
      )}

      <ConfirmDialog
        open={dialog === 'cancel'}
        title={t('actions.cancelTitle')}
        danger
        confirmLabel={t('actions.cancel2')}
        input={{ label: t('actions.reason'), required: true }}
        busy={cancelMut.isPending}
        onConfirm={(v) => cancelMut.mutate(v)}
        onCancel={() => setDialog(null)}
      />
      <ConfirmDialog
        open={dialog === 'use'}
        title={t('actions.markUsedTitle')}
        confirmLabel={t('actions.markUsed')}
        input={{ label: t('actions.notesOptional') }}
        busy={useMut.isPending}
        onConfirm={(v) => useMut.mutate(v)}
        onCancel={() => setDialog(null)}
      />
    </Card>
  );
}
