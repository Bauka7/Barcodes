import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../auth/AuthContext';
import { BarcodeDetailCard } from '../components/BarcodeDetailCard';
import { Button, Input, PageHeader } from '../components/ui';

export default function SearchPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isStaff = user?.role === 'admin' || user?.role === 'operator';

  const [value, setValue] = useState('');
  const [submitted, setSubmitted] = useState('');

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const v = value.trim().toUpperCase();
    if (v) setSubmitted(v);
  };

  return (
    <div>
      <PageHeader title={t('search.title')} subtitle={t('search.subtitle')} />

      <form onSubmit={onSubmit} className="mb-4 flex max-w-md gap-2">
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value.toUpperCase())}
          placeholder={t('search.placeholder')}
          className="font-mono"
        />
        <Button type="submit" variant="primary" className="shrink-0">
          <i className="ti ti-search" /> {t('search.find')}
        </Button>
      </form>

      {submitted && <BarcodeDetailCard barcode={submitted} canAct={isStaff} />}
    </div>
  );
}
