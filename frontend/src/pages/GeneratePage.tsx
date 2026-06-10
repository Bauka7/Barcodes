import { useMemo, useState, type FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { generateNumbers, previewBatchPdf } from '../api/barcodes';
import { useAuth } from '../auth/AuthContext';
import { flattenDepartments, useDepartmentTree } from '../lib/departmentName';
import { openBlob } from '../lib/pdf';
import { Button, ErrorText, Field, Input, PageHeader, Select, Textarea } from '../components/ui';
import { BarcodeView } from '../components/BarcodeView';
import { Chip } from '../components/Chip';

export default function GeneratePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isStaff = user?.role === 'admin' || user?.role === 'operator';
  const navigate = useNavigate();

  const { data: tree } = useDepartmentTree();
  const depts = useMemo(() => flattenDepartments(tree ?? []), [tree]);

  const [packageType, setPackageType] = useState('');
  const [quantity, setQuantity] = useState('50');
  const [departmentId, setDepartmentId] = useState('');
  const [notes, setNotes] = useState('');

  const gen = useMutation({
    mutationFn: () =>
      generateNumbers({
        package_type: packageType.trim().toUpperCase(),
        quantity: Number(quantity),
        department_id: departmentId ? Number(departmentId) : undefined,
        notes: notes.trim() || undefined,
      }),
  });

  const preview = useMutation({
    mutationFn: (batchId: number) => previewBatchPdf(batchId),
    onSuccess: (blob) => openBlob(blob),
  });

  const qNum = Number(quantity);
  const valid = /^[A-Za-z]{2}$/.test(packageType.trim()) && qNum >= 1 && qNum <= 1000;
  const result = gen.data;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (valid) gen.mutate();
  };

  return (
    <div>
      <PageHeader title={t('gen.title')} subtitle={t('gen.subtitle')} />

      <form onSubmit={onSubmit} className="grid max-w-md grid-cols-1 sm:grid-cols-2 gap-x-4">
        <Field label={t('gen.packageType')}>
          <Input
            value={packageType}
            onChange={(e) => setPackageType(e.target.value.toUpperCase().slice(0, 2))}
            placeholder={t('gen.packageTypePh')}
            className="font-mono uppercase"
          />
        </Field>
        <Field label={t('gen.quantity')}>
          <Input
            type="number"
            min={1}
            max={1000}
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />
        </Field>
        <Field label={t('gen.department')} className="col-span-2">
          <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">{t('gen.departmentNone')}</option>
            {depts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_path ?? d.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t('gen.notes')} className="col-span-2">
          <Textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={t('gen.notesPh')}
          />
        </Field>
        <div className="col-span-2">
          <Button type="submit" variant="primary" disabled={!valid || gen.isPending}>
            <i className="ti ti-bolt" /> {gen.isPending ? t('gen.generating') : t('gen.generate')}
          </Button>
        </div>
      </form>

      {gen.isError && (
        <div className="mt-3 max-w-md">
          <ErrorText error={gen.error} />
        </div>
      )}

      {result && (
        <div className="mt-6 max-w-2xl border-t-[0.5px] border-bd3 pt-4">
          <div className="mb-3 flex items-center justify-between">
            <Chip tone="ok">
              <i className="ti ti-circle-check" />
              {t('gen.created', { id: result.batch_id, count: result.count })}
            </Chip>
            {isStaff && (
              <Button size="sm" onClick={() => navigate(`/print?batch=${result.batch_id}`)}>
                <i className="ti ti-printer" /> {t('gen.toPrint')}
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] gap-3">
            <BarcodeView code={result.first_barcode} />
            <div className="flex flex-col gap-2">
              <div className="rounded-ctl bg-bg2 px-3 py-2">
                <div className="text-[15px] text-t2">{t('gen.range')}</div>
                <div className="font-mono text-[16px] font-medium">
                  {result.first_barcode} → {result.last_barcode}
                </div>
              </div>
              <div className="rounded-ctl bg-bg2 px-3 py-2">
                <div className="text-[15px] text-t2">{t('gen.printed')}</div>
                <div className="text-[16px] font-medium">0 / {result.count}</div>
              </div>
              <Button size="sm" onClick={() => preview.mutate(result.batch_id)} disabled={preview.isPending}>
                <i className="ti ti-eye" /> {t('gen.previewPdf')}
              </Button>
              <Link
                to={`/barcodes/${result.first_barcode}`}
                className="inline-flex items-center gap-1.5 text-[15px] text-brand hover:text-brand-dark"
              >
                <i className="ti ti-arrow-right" /> {t('gen.openDetail')}
              </Link>
            </div>
          </div>

          {preview.isError && (
            <div className="mt-2">
              <ErrorText error={preview.error} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
