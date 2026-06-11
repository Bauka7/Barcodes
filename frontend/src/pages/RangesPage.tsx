import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  cancelRange,
  generateFromRange,
  getRangeRemaining,
  listRanges,
  renewRange,
} from '../api/ranges';
import type { BarcodeRangeRead } from '../api/types';
import { DataTable, type Column } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { Drawer } from '../components/Drawer';
import { Button, Card, ErrorText, Field, Input, Loading, PageHeader } from '../components/ui';

const fmtDate = (s: string | null | undefined): string =>
  s ? new Date(s).toLocaleDateString() : '—';

// Дата из <input type="date"> → ISO с концом дня (срок действует весь выбранный день).
const dayEndIso = (d: string): string => new Date(`${d}T23:59:59`).toISOString();

export default function RangesPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<BarcodeRangeRead | null>(null);
  const [qty, setQty] = useState('20');
  const [genNotes, setGenNotes] = useState('');

  const [cancelOpen, setCancelOpen] = useState(false);
  const [renewOpen, setRenewOpen] = useState(false);
  const [renewDate, setRenewDate] = useState('');

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
    mutationFn: () =>
      generateFromRange(selected!.id, { quantity: Number(qty), notes: genNotes.trim() || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['range-remaining', selected?.id] });
      qc.invalidateQueries({ queryKey: ['ranges'] });
      setGenNotes('');
    },
  });

  const cancel = useMutation({
    mutationFn: (reason: string) => cancelRange(selected!.id, reason),
    onSuccess: (updated) => {
      setSelected(updated);
      setCancelOpen(false);
      qc.invalidateQueries({ queryKey: ['ranges'] });
    },
  });

  const renew = useMutation({
    mutationFn: () => renewRange(selected!.id, dayEndIso(renewDate)),
    onSuccess: (updated) => {
      setSelected(updated);
      setRenewOpen(false);
      setRenewDate('');
      qc.invalidateQueries({ queryKey: ['ranges'] });
      qc.invalidateQueries({ queryKey: ['range-remaining', selected?.id] });
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
    { key: 'expires', header: t('ranges.expires'), render: (r) => fmtDate(r.expires_at) },
    { key: 'status', header: t('ranges.status'), render: (r) => <StatusBadge status={r.status} domain="range" /> },
  ];

  const total = selected ? selected.end_number - selected.start_number + 1 : 0;
  const rem = remaining.data?.remaining ?? 0;
  const used = total - rem;
  const pct = total > 0 ? Math.round((used / total) * 100) : 0;
  const canManage = selected != null && (selected.status === 'active' || selected.status === 'expired');

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
                      <tr>
                        <td className="py-1 text-t2">{t('ranges.expires')}</td>
                        <td className="py-1 text-right">{fmtDate(selected.expires_at)}</td>
                      </tr>
                    </tbody>
                  </table>

                  {selected.status === 'cancelled' && selected.cancellation_reason && (
                    <div className="mb-3 rounded-ctl bg-bg2 px-3 py-2 text-[15px]">
                      <span className="text-t2">{t('ranges.cancelReason')}: </span>
                      {selected.cancellation_reason}
                    </div>
                  )}

                  {selected.status === 'active' && (
                    <Field label={t('ranges.generateFrom')} className="mb-3">
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
                  )}

                  {canManage && (
                    <div className="flex gap-2 border-t-[0.5px] border-bd3 pt-3">
                      <Button onClick={() => { setRenewDate(''); setRenewOpen(true); }}>
                        <i className="ti ti-calendar-plus" /> {t('ranges.renew')}
                      </Button>
                      <Button variant="danger" onClick={() => setCancelOpen(true)}>
                        <i className="ti ti-ban" /> {t('ranges.cancel')}
                      </Button>
                    </div>
                  )}

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

      <ConfirmDialog
        open={cancelOpen}
        title={t('ranges.cancelTitle')}
        danger
        confirmLabel={t('ranges.cancel')}
        input={{ label: t('actions.reason') }}
        busy={cancel.isPending}
        onConfirm={(reason) => cancel.mutate(reason)}
        onCancel={() => setCancelOpen(false)}
      />

      <Drawer open={renewOpen} onClose={() => setRenewOpen(false)} title={t('ranges.renewTitle')}>
        <Field label={t('ranges.newExpiry')}>
          <Input type="date" value={renewDate} onChange={(e) => setRenewDate(e.target.value)} />
        </Field>
        {renew.isError && <ErrorText error={renew.error} />}
        <div className="mt-3 flex gap-2">
          <Button
            variant="primary"
            className="flex-1"
            disabled={!renewDate || renew.isPending}
            onClick={() => renew.mutate()}
          >
            {t('ranges.renew')}
          </Button>
          <Button onClick={() => setRenewOpen(false)}>{t('actions.cancel')}</Button>
        </div>
      </Drawer>
    </div>
  );
}
