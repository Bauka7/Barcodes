import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getBatchDetail, listPrintHistory, previewBatchPdf, printBatchPdf } from '../api/barcodes';
import type { PrintedBatchItem } from '../api/types';
import { useDepartmentName } from '../lib/departmentName';
import { downloadBlob, openBlob } from '../lib/pdf';
import { BarcodeView } from '../components/BarcodeView';
import { DataTable, type Column } from '../components/DataTable';
import { Pagination } from '../components/Pagination';
import { Button, Card, ErrorText, Field, Input, Loading, PageHeader } from '../components/ui';

const LIMIT = 20;

function fmt(dt: string) {
  return new Date(dt).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function PrintPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const deptName = useDepartmentName();
  const [params, setParams] = useSearchParams();
  const batchId = params.get('batch') ? Number(params.get('batch')) : null;

  const [batchInput, setBatchInput] = useState(batchId ? String(batchId) : '');
  const [printer, setPrinter] = useState('');
  const [notes, setNotes] = useState('');
  const [offset, setOffset] = useState(0);

  const batchQuery = useQuery({
    queryKey: ['batch', batchId],
    queryFn: () => getBatchDetail(batchId as number),
    enabled: batchId != null && Number.isFinite(batchId),
  });

  const history = useQuery({
    queryKey: ['print-history', offset],
    queryFn: () => listPrintHistory({ limit: LIMIT, offset }),
  });

  const previewMut = useMutation({
    mutationFn: () => previewBatchPdf(batchId as number),
    onSuccess: (blob) => openBlob(blob),
  });

  const printMut = useMutation({
    mutationFn: () =>
      printBatchPdf(batchId as number, {
        printer_name: printer.trim() || undefined,
        notes: notes.trim() || undefined,
      }),
    onSuccess: (blob) => {
      downloadBlob(blob, `barcodes_batch_${batchId}.pdf`);
      qc.invalidateQueries({ queryKey: ['print-history'] });
      qc.invalidateQueries({ queryKey: ['batch', batchId] });
    },
  });

  const openBatch = () => {
    const v = Number(batchInput);
    if (Number.isFinite(v) && v > 0) setParams({ batch: String(v) });
  };

  const columns: Column<PrintedBatchItem>[] = [
    { key: 'batch', header: t('print.batch'), render: (r) => `#${r.generated_batch_id}` },
    { key: 'printer', header: t('print.printer'), render: (r) => r.printer_name ?? '—' },
    { key: 'by', header: t('print.by'), render: (r) => <span className="font-mono">{r.printed_by ?? '—'}</span> },
    { key: 'count', header: t('print.count'), render: (r) => r.printed_count },
    { key: 'dept', header: t('journal.dept'), render: (r) => deptName(r.department_id) },
    { key: 'date', header: t('journal.date'), render: (r) => <span className="text-t2">{fmt(r.printed_at)}</span> },
  ];

  return (
    <div>
      <PageHeader title={t('print.title')} subtitle={t('print.subtitle')} />

      <Card className="mb-5 max-w-3xl">
        <div className="mb-3 flex items-end gap-2">
          <Field label={t('print.batchId')} className="mb-0 w-40">
            <Input
              type="number"
              value={batchInput}
              onChange={(e) => setBatchInput(e.target.value)}
              placeholder="1042"
            />
          </Field>
          <Button onClick={openBatch}>{t('print.open')}</Button>
        </div>

        {batchId != null && (
          batchQuery.isLoading ? (
            <Loading />
          ) : batchQuery.isError ? (
            <ErrorText error={batchQuery.error} />
          ) : batchQuery.data ? (
            <div className="grid grid-cols-1 sm:grid-cols-[220px_1fr] gap-5 border-t-[0.5px] border-bd3 pt-4">
              <div>
                <div className="mb-1.5 text-[15px] text-t2">{t('print.preview')} · 126×71</div>
                <BarcodeView
                  code={batchQuery.data.first_barcode}
                  caption={deptName(batchQuery.data.department_id)}
                  height={52}
                />
              </div>
              <div>
                <Field label={t('print.printer')}>
                  <Input value={printer} onChange={(e) => setPrinter(e.target.value)} placeholder="Zebra S4M" />
                </Field>
                <Field label={t('gen.notes')}>
                  <Input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={t('print.notesPh')} />
                </Field>
                <div className="flex gap-2">
                  <Button onClick={() => previewMut.mutate()} disabled={previewMut.isPending}>
                    <i className="ti ti-eye" /> {t('gen.previewPdf')}
                  </Button>
                  <Button variant="primary" onClick={() => printMut.mutate()} disabled={printMut.isPending}>
                    <i className="ti ti-printer" /> {t('print.printAndDownload')}
                  </Button>
                </div>
                <div className="mt-2 text-[13px] text-t3">
                  {t('print.willMark', { count: batchQuery.data.quantity })}
                </div>
                {printMut.isError && (
                  <div className="mt-2">
                    <ErrorText error={printMut.error} />
                  </div>
                )}
              </div>
            </div>
          ) : null
        )}
      </Card>

      <div className="mb-2 text-[16px] font-medium">{t('print.history')}</div>
      {history.isError ? (
        <ErrorText error={history.error} />
      ) : (
        <>
          <DataTable
            columns={columns}
            rows={history.data ?? []}
            rowKey={(r) => r.id}
            loading={history.isLoading}
            empty={t('print.historyEmpty')}
          />
          <Pagination
            offset={offset}
            limit={LIMIT}
            shown={history.data?.length ?? 0}
            hasNext={(history.data?.length ?? 0) === LIMIT}
            onChange={setOffset}
          />
        </>
      )}
    </div>
  );
}
