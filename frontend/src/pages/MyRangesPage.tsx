import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { generateFromRange, listMyRanges } from '../api/ranges';
import { getMyBatchDetail, listMyBatches, printBatchPdf } from '../api/barcodes';
import type { BarcodeNumberResponse, BarcodeRangeRead, GeneratedBatchItem } from '../api/types';
import { openBlob } from '../lib/pdf';
import { DataTable, type Column } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { Drawer } from '../components/Drawer';
import { Button, ErrorText, Field, Input, PageHeader } from '../components/ui';
import { useDepartmentName } from '../lib/departmentName';

const remainingOf = (r: BarcodeRangeRead): number =>
  r.status === 'active' ? Math.max(0, r.end_number - r.current_number + 1) : 0;

const PRINT_LAYOUT_KEY = 'qazpost.printLayoutSettings';
const LEGACY_PRINT_LAYOUT_KEY = 'qazpost.printLayout';
const A4_WIDTH_MM = 210;
const A4_HEIGHT_MM = 297;
const LABEL_WIDTH_MM = 45;
const LABEL_HEIGHT_MM = 25;

interface PrintLayoutSettings {
  offsetLeft: number;
  offsetTop: number;
  gapX: number;
  gapY: number;
  rows: number;
  columns: number;
}

const DEFAULT_LAYOUT: PrintLayoutSettings = {
  offsetLeft: 0,
  offsetTop: 0,
  gapX: 0,
  gapY: 0,
  rows: 1,
  columns: 1,
};

const normalizeLayout = (value: Partial<PrintLayoutSettings>): PrintLayoutSettings => ({
  offsetLeft: clampNumber(Number(value.offsetLeft), 0, 120),
  offsetTop: clampNumber(Number(value.offsetTop), 0, 120),
  gapX: clampNumber(Number(value.gapX), 0, 120),
  gapY: clampNumber(Number(value.gapY), 0, 120),
  rows: clampNumber(Number(value.rows), 1, 5),
  columns: clampNumber(Number(value.columns), 1, 4),
});

const fromLegacyLayout = (value: Record<string, unknown>): PrintLayoutSettings => ({
  offsetLeft: Number(value.marginLeft ?? DEFAULT_LAYOUT.offsetLeft),
  offsetTop: Number(value.marginTop ?? DEFAULT_LAYOUT.offsetTop),
  gapX: Number(value.gapHorizontal ?? DEFAULT_LAYOUT.gapX),
  gapY: Number(value.gapVertical ?? DEFAULT_LAYOUT.gapY),
  rows: Number(value.rowsPerPage ?? DEFAULT_LAYOUT.rows),
  columns: Number(value.labelsPerRow ?? DEFAULT_LAYOUT.columns),
});

const loadLayout = (): PrintLayoutSettings => {
  try {
    const raw = localStorage.getItem(PRINT_LAYOUT_KEY);
    if (raw) return normalizeLayout({ ...DEFAULT_LAYOUT, ...JSON.parse(raw) });

    const legacyRaw = localStorage.getItem(LEGACY_PRINT_LAYOUT_KEY);
    if (legacyRaw) return normalizeLayout(fromLegacyLayout(JSON.parse(legacyRaw)));

    return DEFAULT_LAYOUT;
  } catch {
    return DEFAULT_LAYOUT;
  }
};

const clampNumber = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, Number.isFinite(value) ? value : min));

const toBackendPrintLayout = (layout: PrintLayoutSettings) => ({
  offset_left: layout.offsetLeft,
  offset_top: layout.offsetTop,
  gap_x: layout.gapX,
  gap_y: layout.gapY,
  rows: layout.rows,
  columns: layout.columns,
});

const CODE128_PATTERNS = [
  '212222', '222122', '222221', '121223', '121322', '131222', '122213', '122312', '132212',
  '221213', '221312', '231212', '112232', '122132', '122231', '113222', '123122', '123221',
  '223211', '221132', '221231', '213212', '223112', '312131', '311222', '321122', '321221',
  '312212', '322112', '322211', '212123', '212321', '232121', '111323', '131123', '131321',
  '112313', '132113', '132311', '211313', '231113', '231311', '112133', '112331', '132131',
  '113123', '113321', '133121', '313121', '211331', '231131', '213113', '213311', '213131',
  '311123', '311321', '331121', '312113', '312311', '332111', '314111', '221411', '431111',
  '111224', '111422', '121124', '121421', '141122', '141221', '112214', '112412', '122114',
  '122411', '142112', '142211', '241211', '221114', '413111', '241112', '134111', '111242',
  '121142', '121241', '114212', '124112', '124211', '411212', '421112', '421211', '212141',
  '214121', '412121', '111143', '111341', '131141', '114113', '114311', '411113', '411311',
  '113141', '114131', '311141', '411131', '211412', '211214', '211232', '2331112',
] as const;

const encodeCode128B = (value: string): string[] => {
  const values = [104];
  for (const char of value) {
    const code = char.charCodeAt(0);
    values.push(code >= 32 && code <= 126 ? code - 32 : 0);
  }

  const checksum = values.reduce((sum, code, index) => sum + (index === 0 ? code : code * index), 0) % 103;
  return [...values, checksum, 106].map((code) => CODE128_PATTERNS[code]);
};

function Code128Preview({ value }: { value: string }) {
  const patterns = encodeCode128B(value);
  const modules = patterns.flatMap((pattern) =>
    pattern.split('').map((width, index) => ({ width: Number(width), black: index % 2 === 0 })),
  );
  let x = 0;
  const totalWidth = modules.reduce((sum, module) => sum + module.width, 0);

  return (
    <svg viewBox={`0 0 ${totalWidth} 38`} style={{ width: '38mm', height: '8mm' }} preserveAspectRatio="none">
      {modules.map((module, index) => {
        const currentX = x;
        x += module.width;
        return module.black ? (
          <rect key={index} x={currentX} y={0} width={module.width} height={38} fill="black" />
        ) : null;
      })}
    </svg>
  );
}

export default function MyRangesPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const deptName = useDepartmentName();

  const rangesQ = useQuery({ queryKey: ['my-ranges'], queryFn: () => listMyRanges({ limit: 100 }) });
  const batchesQ = useQuery({ queryKey: ['my-batches'], queryFn: () => listMyBatches({ limit: 50 }) });
  const [previewBatchId, setPreviewBatchId] = useState<number | null>(null);
  const [layout, setLayout] = useState<PrintLayoutSettings>(loadLayout);
  const previewQ = useQuery({
    queryKey: ['my-batch-detail', previewBatchId],
    queryFn: () => getMyBatchDetail(previewBatchId ?? 0),
    enabled: previewBatchId != null,
  });

  useEffect(() => {
    localStorage.setItem(PRINT_LAYOUT_KEY, JSON.stringify(layout));
  }, [layout]);

  const updateLayout = (key: keyof PrintLayoutSettings, value: string, min: number, max: number) => {
    setLayout((current) => ({
      ...current,
      [key]: clampNumber(Number(value), min, max),
    }));
  };

  const previewPages = useMemo(() => {
    const barcodes = previewQ.data?.barcodes ?? [];
    const labelsPerPage = layout.columns * layout.rows;
    const pages = [];
    for (let i = 0; i < barcodes.length; i += labelsPerPage) {
      pages.push(barcodes.slice(i, i + labelsPerPage));
    }
    return pages;
  }, [layout.columns, layout.rows, previewQ.data?.barcodes]);

  const pageWidth = A4_WIDTH_MM;
  const pageHeight = A4_HEIGHT_MM;
  const previewDepartmentName =
    previewQ.data?.department_id != null ? deptName(previewQ.data.department_id) : 'KazPost';

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

  const print = useMutation({
    mutationFn: (batchId: number) =>
      printBatchPdf(batchId, { print_layout: toBackendPrintLayout(layout) }),
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
          {r.start_number}-{r.end_number}
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
          <span className="text-t3">-</span>
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
          {b.first_barcode} {'->'} {b.last_barcode}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (b) => (
        <span className="flex justify-end gap-1.5">
          <Button size="sm" onClick={() => setPreviewBatchId(b.id)}>
            <i className="ti ti-eye" /> {t('myranges.preview')}
          </Button>
          <Button size="sm" variant="primary" onClick={() => print.mutate(b.id)} disabled={print.isPending}>
            <i className="ti ti-download" /> Скачать PDF
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
        {print.isError && (
          <div className="mt-2">
            <ErrorText error={print.error} />
          </div>
        )}
      </div>

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
                    {genResult.first_barcode} {'->'} {genResult.last_barcode}
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <Button onClick={() => setPreviewBatchId(genResult.batch_id)}>
                    <i className="ti ti-eye" /> {t('myranges.preview')}
                  </Button>
                  <Button variant="primary" onClick={() => print.mutate(genResult.batch_id)} disabled={print.isPending}>
                    <i className="ti ti-download" /> Скачать PDF
                  </Button>
                  <Button onClick={() => setGenFor(null)}>{t('actions.done')}</Button>
                </div>
              </>
            )}
          </>
        )}
      </Drawer>

      {previewBatchId != null && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={() => setPreviewBatchId(null)}
        >
          <div
            className="flex h-[92vh] w-[min(1280px,96vw)] flex-col overflow-hidden rounded-card border-[0.5px] border-bd2 bg-bg1"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b-[0.5px] border-bd2 px-5 py-3">
              <div>
                <div className="text-[20px] font-medium">Предпросмотр печати</div>
              </div>
              <button
                type="button"
                onClick={() => setPreviewBatchId(null)}
                className="text-t2 hover:text-t1"
                aria-label="close"
              >
                <i className="ti ti-x text-[22px]" />
              </button>
            </div>

            <div className="grid min-h-0 flex-1 grid-cols-[300px_1fr]">
              <aside className="overflow-auto border-r-[0.5px] border-bd2 p-4">
                <p className="mb-3 text-[14px] text-t2">
                  Настройки сохраняются автоматически и применяются к PDF.
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Слева, мм">
                    <Input
                      type="number"
                      min={0}
                      max={120}
                      value={layout.offsetLeft}
                      onChange={(e) => updateLayout('offsetLeft', e.target.value, 0, 120)}
                    />
                  </Field>
                  <Field label="Сверху, мм">
                    <Input
                      type="number"
                      min={0}
                      max={120}
                      value={layout.offsetTop}
                      onChange={(e) => updateLayout('offsetTop', e.target.value, 0, 120)}
                    />
                  </Field>
                  <Field label="Горизонт., мм">
                    <Input
                      type="number"
                      min={0}
                      max={120}
                      value={layout.gapX}
                      onChange={(e) => updateLayout('gapX', e.target.value, 0, 120)}
                    />
                  </Field>
                  <Field label="Вертик., мм">
                    <Input
                      type="number"
                      min={0}
                      max={120}
                      value={layout.gapY}
                      onChange={(e) => updateLayout('gapY', e.target.value, 0, 120)}
                    />
                  </Field>
                  <Field label="Рядов">
                    <Input
                      type="number"
                      min={1}
                      max={5}
                      value={layout.rows}
                      onChange={(e) => updateLayout('rows', e.target.value, 1, 5)}
                    />
                  </Field>
                  <Field label="В ряд">
                    <Input
                      type="number"
                      min={1}
                      max={4}
                      value={layout.columns}
                      onChange={(e) => updateLayout('columns', e.target.value, 1, 4)}
                    />
                  </Field>
                </div>

                <div className="mt-2 flex flex-col gap-2">
                  <Button onClick={() => setLayout(DEFAULT_LAYOUT)}>Сбросить</Button>
                  <Button
                    variant="primary"
                    onClick={() => print.mutate(previewBatchId)}
                    disabled={print.isPending}
                  >
                    <i className="ti ti-download" /> Скачать PDF
                  </Button>
                </div>

              </aside>

              <main className="min-w-0 overflow-auto bg-bg2 p-5">
                {previewQ.isError ? (
                  <ErrorText error={previewQ.error} />
                ) : previewQ.isLoading ? (
                  <div className="py-8 text-center text-t2">...</div>
                ) : (
                  <div className="flex min-w-max flex-col items-center gap-6">
                    {previewPages.map((page, pageIndex) => (
                      <div key={pageIndex}>
                        <div className="mb-1 text-[13px] text-t3">Страница {pageIndex + 1}</div>
                        <div
                          className="relative border-[0.5px] border-bd3 bg-white text-black"
                          style={{ width: `${pageWidth}mm`, height: `${pageHeight}mm` }}
                        >
                          {page.map((item, index) => {
                            const row = Math.floor(index / layout.columns);
                            const col = index % layout.columns;
                            const left = layout.offsetLeft + col * (LABEL_WIDTH_MM + layout.gapX);
                            const top = layout.offsetTop + row * (LABEL_HEIGHT_MM + layout.gapY);
                            return (
                              <div
                                key={item.id}
                                className="absolute flex flex-col items-center justify-between overflow-hidden border-[0.5px] border-dashed border-zinc-300 bg-white px-[1mm] py-[1mm]"
                                style={{
                                  left: `${left}mm`,
                                  top: `${top}mm`,
                                  width: `${LABEL_WIDTH_MM}mm`,
                                  height: `${LABEL_HEIGHT_MM}mm`,
                                }}
                              >
                                <div className="max-w-full truncate text-[5.5pt] leading-none">
                                  {previewDepartmentName}
                                </div>
                                <Code128Preview value={item.barcode} />
                                <div className="max-w-full truncate font-mono text-[6.2pt] leading-none">
                                  {item.barcode}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </main>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
