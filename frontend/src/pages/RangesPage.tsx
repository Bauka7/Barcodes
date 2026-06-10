import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { generateFromRange, getRangeRemaining, listRanges } from '../api/ranges';
import type { BarcodeRangeRead } from '../api/types';
import { DataTable, type Column } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { Button, Card, ErrorText, Field, Input, Loading, PageHeader } from '../components/ui';

export default function RangesPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<BarcodeRangeRead | null>(null);
  const [qty, setQty] = useState('20');
  const [genNotes, setGenNotes] = useState('');

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['ranges'],
    queryFn: () => listRanges({ limit: 100 }),
  });

  const remaining = useQuery({
    queryKey: ['range-remaining', selected?.id],
    queryFn: () => getRangeRemaining(selected!.id),
    enabled: selected != null,
  });

  const gen = useMutation({
    mutationFn: () => generateFromRange(selected!.id, { quantity: Number(qty), notes: genNotes.trim() || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-remaining', selected?.id] });
      qc.invalidateQueries({ queryKey: ['ranges'] });
      setGenNotes('');
    },
  });

  const columns: Column<BarcodeRangeRead>[] = [
    { key: 'id', header: '#', render: (r) => <span className="font-medium">{r.id}</span> },
    { key: 'type', header: t('ranges.type'), render: (r) => r.package_type },
    {
      key: 'range',
      header: t('ranges.range'),
      render: (r) => (
        <span className="font-mono">
          {r.start_number}–{r.end_number}
        </span>
      ),
    },
    { key: 'status', header: t('ranges.status'), render: (r) => <StatusBadge status={r.status} domain="range" /> },
  ];

  const total = selected ? selected.end_number - selected.start_number + 1 : 0;
  const rem = remaining.data?.remaining ?? 0;
  const used = total - rem;
  const pct = total > 0 ? Math.round((used / total) * 100) : 0;

  return (
    <div>
      <PageHeader title={t('ranges.title')} subtitle={t('ranges.subtitle')} />

      {isError ? (
        <ErrorText error={error} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-4">
          <DataTable
            columns={columns}
            rows={data ?? []}
            rowKey={(r) => r.id}
            loading={isLoading}
            empty={t('ranges.empty')}
            onRowClick={(r) => setSelected(r)}
          />

          {selected ? (
            <Card>
              <div className="mb-2 flex items-center justify-between">
                <span className="font-medium">
                  {t('ranges.range')} #{selected.id} · {selected.package_type}
                </span>
                <StatusBadge status={selected.status} domain="range" />
              </div>

              {remaining.isLoading ? (
                <Loading />
              ) : (
                <>
                  <div className="mb-1 text-[15px] text-t2">{t('ranges.used', { used, total })}</div>
                  <div className="mb-3 h-2 overflow-hidden rounded bg-bg3">
                    <div className="h-full bg-brand" style={{ width: `${pct}%` }} />
                  </div>
                  <table className="mb-3 w-full text-[16px]">
                    <tbody>
                      <tr>
                        <td className="py-1 text-t2">{t('ranges.current')}</td>
                        <td className="py-1 text-right font-mono">{remaining.data?.current_number}</td>
                      </tr>
                      <tr>
                        <td className="py-1 text-t2">{t('ranges.remaining')}</td>
                        <td className="py-1 text-right">{rem}</td>
                      </tr>
                    </tbody>
                  </table>

                  <Field label={t('ranges.generateFrom')} className="mb-0">
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        min={1}
                        value={qty}
                        onChange={(e) => setQty(e.target.value)}
                        className="w-28"
                      />
                      <Button
                        variant="primary"
                        onClick={() => gen.mutate()}
                        disabled={gen.isPending || rem <= 0}
                      >
                        <i className="ti ti-bolt" /> {t('ranges.create')}
                      </Button>
                    </div>
                  </Field>
                  {gen.isError && (
                    <div className="mt-2">
                      <ErrorText error={gen.error} />
                    </div>
                  )}
                  {gen.data && (
                    <div className="mt-2 text-[15px] text-st">
                      {t('gen.created', { id: gen.data.batch_id, count: gen.data.count })}
                    </div>
                  )}
                </>
              )}
            </Card>
          ) : (
            <Card>
              <div className="py-8 text-center text-[16px] text-t3">{t('ranges.selectHint')}</div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
