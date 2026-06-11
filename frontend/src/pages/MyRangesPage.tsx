import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { generateFromRange, listMyRanges } from '../api/ranges';
import { listMyBatches, previewBatchPdf, printBatchPdf } from '../api/barcodes';
import type { BarcodeNumberResponse, BarcodeRangeRead, GeneratedBatchItem } from '../api/types';
import { openBlob } from '../lib/pdf';
import { DataTable, type Column } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { Drawer } from '../components/Drawer';
import { Button, ErrorText, Field, Input, PageHeader } from '../components/ui';

const remainingOf = (r: BarcodeRangeRead): number =>
  r.status === 'active' ? Math.max(0, r.end_number - r.current_number + 1) : 0;

export default function MyRangesPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();

  const rangesQ = useQuery({ queryKey: ['my-ranges'], queryFn: () => listMyRanges({ limit: 100 }) });
  const batchesQ = useQuery({ queryKey: ['my-batches'], queryFn: () => listMyBatches({ limit: 50 }) });

  // ── генерация из диапазона ────────────────────────────────────
  const [genFor, setGenFor] = useState<BarcodeRangeRead | null>(null);
  const [genQty, setGenQty] = useState('50');
  const [genResult, setGenResult] = useState<BarcodeNumberResponse | null>(null);

  const openGen = (r: BarcodeRangeRead) => {
    setGenFor(r);
    setGenQty(String(Math.min(50, remainingOf(r)) || 1));
    setGenResult(null);
  };

  const generate = useMutation({
    mutationFn: ({ id, quantity }: { id: number; quantity: number }) =>
      generateFromRange(id, { quantity }),
    onSuccess: (res) => {
      setGenResult(res);
      qc.invalidateQueries({ queryKey: ['my-ranges'] });
      qc.invalidateQueries({ queryKey: ['my-batches'] });
    },
  });

  const preview = useMutation({
    mutationFn: (batchId: number) => previewBatchPdf(batchId),
    onSuccess: (blob) => openBlob(blob),
  });
  const print = useMutation({
    mutationFn: (batchId: number) => printBatchPdf(batchId, {}),
    onSuccess: (blob) => {
      openBlob(blob);
      qc.invalidateQueries({ queryKey: ['my-batches'] });
    },
  });

  const rangeColumns: Column<BarcodeRangeRead>[] = [
    { key: 'code', header: t('myranges.code'), render: (r) => <span className="font-mono font-medium">{r.package_type}</span> },
    {
      key: 'range',
      header: t('myranges.range'),
      render: (r) => (
        <span className="font-mono text-[15px]">
          {r.start_number}–{r.end_number}
        </span>
      ),
    },
    { key: 'remaining', header: t('myranges.remaining'), render: (r) => remainingOf(r) },
    { key: 'status', header: t('requests.status'), render: (r) => <StatusBadge status={r.status} domain="range" /> },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (r) =>
        r.status === 'active' && remainingOf(r) > 0 ? (
          <Button size="sm" variant="primary" onClick={() => openGen(r)}>
            <i className="ti ti-bolt" /> {t('myranges.generate')}
          </Button>
        ) : (
          <span className="text-t3">—</span>
        ),
    },
  ];

  const batchColumns: Column<GeneratedBatchItem>[] = [
    { key: 'id', header: '#', render: (b) => <span className="font-medium">{b.id}</span> },
    { key: 'code', header: t('myranges.code'), render: (b) => <span className="font-mono">{b.package_type}</span> },
    { key: 'qty', header: t('requests.qty'), render: (b) => b.quantity },
    {
      key: 'range',
      header: t('myranges.range'),
      render: (b) => (
        <span className="font-mono text-[15px]">
          {b.first_barcode} → {b.last_barcode}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (b) => (
        <span className="flex justify-end gap-1.5">
          <Button size="sm" onClick={() => preview.mutate(b.id)} disabled={preview.isPending}>
            <i className="ti ti-eye" /> {t('myranges.preview')}
          </Button>
          <Button size="sm" variant="primary" onClick={() => print.mutate(b.id)} disabled={print.isPending}>
            <i className="ti ti-printer" /> {t('myranges.print')}
          </Button>
        </span>
      ),
    },
  ];

  const genMax = genFor ? remainingOf(genFor) : 0;
  const genValid = Number(genQty) >= 1 && Number(genQty) <= Math.min(genMax, 1000);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <PageHeader title={t('myranges.title')} subtitle={t('myranges.subtitle')} />
        {rangesQ.isError ? (
          <ErrorText error={rangesQ.error} />
        ) : (
          <DataTable
            columns={rangeColumns}
            rows={rangesQ.data ?? []}
            rowKey={(r) => r.id}
            loading={rangesQ.isLoading}
            empty={t('myranges.emptyRanges')}
          />
        )}
      </div>

      <div>
        <h3 className="mb-3 text-lg font-medium">{t('myranges.batchesTitle')}</h3>
        {batchesQ.isError ? (
          <ErrorText error={batchesQ.error} />
        ) : (
          <DataTable
            columns={batchColumns}
            rows={batchesQ.data ?? []}
            rowKey={(b) => b.id}
            loading={batchesQ.isLoading}
            empty={t('myranges.emptyBatches')}
          />
        )}
        {(preview.isError || print.isError) && (
          <div className="mt-2">
            <ErrorText error={preview.error ?? print.error} />
          </div>
        )}
      </div>

      {/* Генерация ШПИ из выбранного диапазона */}
      <Drawer open={!!genFor} onClose={() => setGenFor(null)} title={t('myranges.generate')}>
        {genFor && (
          <>
            <div className="mb-3 rounded-ctl bg-bg2 px-3 py-2 text-[15px]">
              <div className="font-mono font-medium">{genFor.package_type}</div>
              <div className="text-t2">
                {t('myranges.remaining')}: <span className="text-t1">{genMax}</span>
              </div>
            </div>

            {!genResult ? (
              <>
                <Field label={t('myranges.quantity')}>
                  <Input
                    type="number"
                    min={1}
                    max={Math.min(genMax, 1000)}
                    value={genQty}
                    onChange={(e) => setGenQty(e.target.value)}
                  />
                </Field>
                {generate.isError && <ErrorText error={generate.error} />}
                <div className="mt-3 flex gap-2">
                  <Button
                    variant="primary"
                    className="flex-1"
                    disabled={!genValid || generate.isPending}
                    onClick={() => generate.mutate({ id: genFor.id, quantity: Number(genQty) })}
                  >
                    <i className="ti ti-bolt" /> {t('myranges.generate')}
                  </Button>
                  <Button onClick={() => setGenFor(null)}>{t('actions.cancel')}</Button>
                </div>
              </>
            ) : (
              <>
                <div className="mb-3 rounded-ctl bg-bg2 px-3 py-2 text-[15px]">
                  <div className="text-t2">{t('gen.created', { id: genResult.batch_id, count: genResult.count })}</div>
                  <div className="mt-1 font-mono">
                    {genResult.first_barcode} → {genResult.last_barcode}
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <Button onClick={() => preview.mutate(genResult.batch_id)} disabled={preview.isPending}>
                    <i className="ti ti-eye" /> {t('myranges.preview')}
                  </Button>
                  <Button variant="primary" onClick={() => print.mutate(genResult.batch_id)} disabled={print.isPending}>
                    <i className="ti ti-printer" /> {t('myranges.print')}
                  </Button>
                  <Button onClick={() => setGenFor(null)}>{t('actions.done')}</Button>
                </div>
              </>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
}
