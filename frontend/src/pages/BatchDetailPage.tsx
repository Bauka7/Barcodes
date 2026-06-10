import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getBatchDetail } from '../api/barcodes';
import type { GeneratedBarcodeItem } from '../api/types';
import { useAuth } from '../auth/AuthContext';
import { useDepartmentName } from '../lib/departmentName';
import { DataTable, type Column } from '../components/DataTable';
import { StatusBadge } from '../components/StatusBadge';
import { Chip } from '../components/Chip';
import { Button, Card, ErrorText, Loading, PageHeader } from '../components/ui';

export default function BatchDetailPage() {
  const { t } = useTranslation();
  const { batchId } = useParams();
  const id = Number(batchId);
  const navigate = useNavigate();
  const { user } = useAuth();
  const isStaff = user?.role === 'admin' || user?.role === 'operator';
  const deptName = useDepartmentName();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['batch', id],
    queryFn: () => getBatchDetail(id),
    enabled: Number.isFinite(id),
  });

  const columns: Column<GeneratedBarcodeItem>[] = [
    { key: 'barcode', header: t('lifecycle.barcode'), render: (r) => <span className="font-mono">{r.barcode}</span> },
    { key: 'seq', header: '№', render: (r) => r.sequence_number },
    { key: 'status', header: t('lifecycle.status'), render: (r) => <StatusBadge status={r.status} /> },
    {
      key: 'printed',
      header: t('lifecycle.printed'),
      render: (r) => (r.printed ? <StatusBadge status="printed" /> : <Chip tone="muted">{t('common.no')}</Chip>),
    },
  ];

  return (
    <div>
      <Link to="/journal" className="mb-2 inline-flex items-center gap-1 text-[16px] text-t2 hover:text-t1">
        <i className="ti ti-chevron-left" /> {t('journal.title')}
      </Link>

      {isLoading ? (
        <Loading />
      ) : isError ? (
        <ErrorText error={error} />
      ) : data ? (
        <>
          <PageHeader
            title={t('batch.title', { id: data.id })}
            subtitle={`${data.package_type} · ${data.quantity} ${t('batch.pcs')}`}
            actions={
              isStaff ? (
                <Button size="sm" onClick={() => navigate(`/print?batch=${data.id}`)}>
                  <i className="ti ti-printer" /> {t('gen.toPrint')}
                </Button>
              ) : undefined
            }
          />

          <Card className="mb-4 max-w-xl">
            <table className="w-full text-[16px]">
              <tbody>
                <tr>
                  <td className="py-1 text-t2">{t('detail.department')}</td>
                  <td className="py-1 text-right">{deptName(data.department_id)}</td>
                </tr>
                <tr>
                  <td className="py-1 text-t2">{t('gen.range')}</td>
                  <td className="py-1 text-right font-mono">
                    {data.first_barcode} → {data.last_barcode}
                  </td>
                </tr>
                <tr>
                  <td className="py-1 text-t2">{t('journal.source')}</td>
                  <td className="py-1 text-right">{data.source ?? '—'}</td>
                </tr>
                {data.notes && (
                  <tr>
                    <td className="py-1 text-t2">{t('gen.notes')}</td>
                    <td className="py-1 text-right">{data.notes}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </Card>

          <DataTable columns={columns} rows={data.barcodes} rowKey={(r) => r.id} empty="—" />
        </>
      ) : null}
    </div>
  );
}
