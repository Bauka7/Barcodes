import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../auth/AuthContext';
import { BarcodeDetailCard } from '../components/BarcodeDetailCard';
import { PageHeader } from '../components/ui';

export default function BarcodeDetailPage() {
  const { t } = useTranslation();
  const { barcode } = useParams();
  const { user } = useAuth();
  const isStaff = user?.role === 'admin' || user?.role === 'operator';

  return (
    <div>
      <Link to="/search" className="mb-2 inline-flex items-center gap-1 text-[16px] text-t2 hover:text-t1">
        <i className="ti ti-chevron-left" /> {t('search.title')}
      </Link>
      <PageHeader title={t('detail.title')} />
      {barcode && <BarcodeDetailCard barcode={barcode} canAct={isStaff} />}
    </div>
  );
}
