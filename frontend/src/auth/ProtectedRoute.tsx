import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from './AuthContext';
import type { Role } from '../types';

interface Props {
  /** если задано — пускаем только эти роли, иначе «нет доступа» */
  roles?: Role[];
  children: ReactNode;
}

// Гард маршрута (раздел 3/6 брифа): нет токена -> /login; не та роль -> «нет доступа».
export function ProtectedRoute({ roles, children }: Props) {
  const { status, user } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();

  if (status === 'loading') {
    return <div className="p-6 text-t2">{t('common.loading')}</div>;
  }

  if (status === 'unauthenticated' || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Forbidden />;
  }

  return <>{children}</>;
}

function Forbidden() {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-md pt-16 text-center">
      <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-card bg-dx text-dt">
        <i className="ti ti-lock text-3xl" />
      </div>
      <h2 className="text-2xl font-medium">{t('error.forbiddenTitle')}</h2>
      <p className="mt-1 text-[16px] text-t2">{t('error.forbiddenBody')}</p>
    </div>
  );
}
