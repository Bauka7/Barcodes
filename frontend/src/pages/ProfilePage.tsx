import { useMemo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { listDepartments } from '../api/departments';
import { Card, ErrorText, Loading, PageHeader } from '../components/ui';

function ValueRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string | number | null | undefined;
  mono?: boolean;
}) {
  const isEmpty = value === null || value === undefined || value === '';
  return (
    <div className="grid gap-1 border-b-[0.5px] border-bd3 py-2 last:border-b-0 sm:grid-cols-[160px_1fr] sm:gap-3">
      <div className="text-[15px] text-t2">{label}</div>
      <div className={`min-w-0 text-[15px] text-t1 ${mono ? 'font-mono' : ''}`}>
        {isEmpty ? <span className="text-t3">—</span> : String(value)}
      </div>
    </div>
  );
}

function Notice({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-ctl border-[0.5px] border-bd3 bg-bg2 px-3 py-2 text-[15px] text-t2">
      {children}
    </div>
  );
}

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const departmentsQ = useQuery({
    queryKey: ['departments', 'profile'],
    queryFn: () => listDepartments({ limit: 100 }),
  });

  const department = useMemo(() => {
    return departmentsQ.data?.find((item) => item.id === user?.department_id) ?? null;
  }, [departmentsQ.data, user?.department_id]);

  if (!user) {
    return <Loading label={t('common.loading')} />;
  }

  return (
    <div className="flex max-w-5xl flex-col gap-4">
      <PageHeader title={t('profile.title')} subtitle={t('profile.subtitle')} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center gap-2">
            <i className="ti ti-id text-[22px] text-brand" />
            <h3 className="text-lg font-medium">{t('profile.account')}</h3>
          </div>
          <ValueRow label={t('profile.username')} value={user.username} mono />
          <ValueRow label={t('profile.fullName')} value={user.full_name} />
          <ValueRow label={t('profile.role')} value={user.role} mono />
          <ValueRow label={t('profile.status')} value={user.is_active ? t('profile.active') : t('profile.inactive')} />
          <ValueRow label={t('profile.userId')} value={user.id} mono />
        </Card>

        <Card>
          <div className="mb-3 flex items-center gap-2">
            <i className="ti ti-building-community text-[22px] text-brand" />
            <h3 className="text-lg font-medium">{t('profile.department')}</h3>
          </div>
          {departmentsQ.isError ? (
            <ErrorText error={departmentsQ.error} />
          ) : departmentsQ.isLoading ? (
            <Loading label={t('common.loading')} />
          ) : (
            <>
              <ValueRow label={t('profile.departmentName')} value={department?.name ?? null} />
              <ValueRow label={t('profile.departmentCode')} value={department?.code ?? null} mono />
              <ValueRow label={t('profile.departmentRegion')} value={department?.region ?? null} />
              <ValueRow label={t('profile.departmentType')} value={department?.department_type ?? null} />
              <ValueRow label={t('profile.departmentPath')} value={department?.full_path ?? null} />
              <ValueRow label={t('profile.departmentId')} value={user.department_id} mono />
            </>
          )}
        </Card>

        <Card>
          <div className="mb-3 flex items-center gap-2">
            <i className="ti ti-address-book text-[22px] text-brand" />
            <h3 className="text-lg font-medium">{t('profile.contacts')}</h3>
          </div>
          <ValueRow label={t('profile.clientId')} value={user.client_id} mono />
          <ValueRow label={t('profile.email')} value={null} />
          <ValueRow label={t('profile.phone')} value={null} />
          <Notice>{t('profile.contactsBackendNote')}</Notice>
        </Card>

        <Card>
          <div className="mb-3 flex items-center gap-2">
            <i className="ti ti-user-shield text-[22px] text-brand" />
            <h3 className="text-lg font-medium">{t('profile.moderator')}</h3>
          </div>
          <ValueRow label={t('profile.moderatorName')} value={null} />
          <ValueRow label={t('profile.moderatorRole')} value={null} />
          <ValueRow label={t('profile.moderatorContact')} value={null} />
          <Notice>{t('profile.moderatorBackendNote')}</Notice>
        </Card>
      </div>
    </div>
  );
}
