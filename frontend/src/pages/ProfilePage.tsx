import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { updateMyProfile } from '../api/auth';
import { useAuth } from '../auth/AuthContext';
import { Button, Card, ErrorText, Field, Input, Loading, PageHeader } from '../components/ui';

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
    <div className="grid gap-1 border-b-[0.5px] border-bd3 py-2 last:border-b-0 sm:grid-cols-[170px_1fr] sm:gap-3">
      <div className="text-[15px] text-t2">{label}</div>
      <div className={`min-w-0 text-[15px] text-t1 ${mono ? 'font-mono' : ''}`}>
        {isEmpty ? <span className="text-t3">-</span> : String(value)}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<unknown>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!user || editing) return;
    setFullName(user.full_name ?? '');
    setEmail(user.email ?? '');
    setPhone(user.phone ?? '');
  }, [editing, user]);

  if (!user) {
    return <Loading label={t('common.loading')} />;
  }

  const department = user.department;
  const shpiRegion =
    department?.shpi_region_code
      ? `${department.shpi_region_code}${department.shpi_region_name ? ` — ${department.shpi_region_name}` : ''}`
      : null;
  const moderator = user.moderator;
  const isAdmin = user.role === 'admin';
  const isOperator = user.role === 'operator';
  const scopeType = user.scope?.type;
  const scopeLabel =
    scopeType === 'all'
      ? t('profile.scopeAll')
      : scopeType === 'subtree'
        ? t('profile.scopeSubtree')
        : t('profile.scopeOwn');

  const startEdit = () => {
    setFullName(user.full_name ?? '');
    setEmail(user.email ?? '');
    setPhone(user.phone ?? '');
    setSaveError(null);
    setSaved(false);
    setEditing(true);
  };

  const cancelEdit = () => {
    setEditing(false);
    setSaveError(null);
  };

  const saveProfile = async () => {
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      await updateMyProfile({
        full_name: fullName.trim() || null,
        email: email.trim() || null,
        phone: phone.trim() || null,
      });
      await refreshUser();
      setEditing(false);
      setSaved(true);
    } catch (error) {
      setSaveError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex max-w-5xl flex-col gap-4">
      <PageHeader title={t('profile.title')} subtitle={t('profile.subtitle')} />

      {saved ? (
        <div className="rounded-ctl border-[0.5px] border-green-200 bg-green-50 px-3 py-2 text-[15px] text-green-900">
          {t('profile.saved')}
        </div>
      ) : null}
      {saveError ? <ErrorText error={saveError} /> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center gap-2">
            <i className="ti ti-id text-[22px] text-brand" />
            <h3 className="text-lg font-medium">{t('profile.account')}</h3>
          </div>
          <ValueRow label={t('profile.username')} value={user.username} mono />
          <ValueRow label={t('profile.fullName')} value={user.full_name} />
          <ValueRow label={t('profile.role')} value={user.role_label || user.role} />
          <ValueRow label={t('profile.status')} value={user.is_active ? t('profile.active') : t('profile.inactive')} />
          <ValueRow label={t('profile.userId')} value={user.id} mono />
        </Card>

        {isAdmin ? (
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <i className="ti ti-shield-check text-[22px] text-brand" />
              <h3 className="text-lg font-medium">{t('profile.access')}</h3>
            </div>
            <ValueRow label={t('profile.accessType')} value={scopeLabel} />
            <ValueRow label={t('profile.description')} value={t('profile.adminScopeDescription')} />
          </Card>
        ) : null}

        {!isAdmin ? (
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <i className="ti ti-building-community text-[22px] text-brand" />
              <h3 className="text-lg font-medium">{t('profile.department')}</h3>
            </div>
            <ValueRow label={t('profile.departmentName')} value={department?.name ?? null} />
            <ValueRow label={t('profile.departmentCode')} value={department?.code ?? null} mono />
            <ValueRow label={t('profile.departmentRegion')} value={department?.region ?? null} />
            <ValueRow label={t('profile.shpiRegion')} value={shpiRegion} />
            <ValueRow label={t('profile.departmentType')} value={department?.department_type ?? null} />
            <ValueRow label={t('profile.departmentPath')} value={department?.full_path ?? null} />
            <ValueRow label={t('profile.departmentId')} value={user.department_id} mono />
          </Card>
        ) : null}

        {isOperator ? (
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <i className="ti ti-sitemap text-[22px] text-brand" />
              <h3 className="text-lg font-medium">{t('profile.responsibility')}</h3>
            </div>
            <ValueRow label={t('profile.accessType')} value={scopeLabel} />
            <ValueRow label={t('profile.description')} value={t('profile.operatorScopeDescription')} />
          </Card>
        ) : null}

        <Card>
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <i className="ti ti-address-book text-[22px] text-brand" />
              <h3 className="text-lg font-medium">{t('profile.contacts')}</h3>
            </div>
            {!editing ? (
              <Button size="sm" onClick={startEdit}>
                <i className="ti ti-edit" />
                {t('profile.edit')}
              </Button>
            ) : null}
          </div>

          {editing ? (
            <div>
              <Field label={t('profile.fullName')}>
                <Input value={fullName} onChange={(event) => setFullName(event.target.value)} />
              </Field>
              <Field label={t('profile.email')}>
                <Input value={email} onChange={(event) => setEmail(event.target.value)} />
              </Field>
              <Field label={t('profile.phone')}>
                <Input value={phone} onChange={(event) => setPhone(event.target.value)} />
              </Field>
              <div className="flex gap-2">
                <Button variant="primary" onClick={saveProfile} disabled={saving}>
                  {saving ? t('common.loading') : t('profile.save')}
                </Button>
                <Button onClick={cancelEdit} disabled={saving}>
                  {t('profile.cancel')}
                </Button>
              </div>
            </div>
          ) : (
            <>
              <ValueRow label={t('profile.email')} value={user.email} />
              <ValueRow label={t('profile.phone')} value={user.phone} />
            </>
          )}
        </Card>

        {!isAdmin && moderator ? (
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <i className="ti ti-user-shield text-[22px] text-brand" />
              <h3 className="text-lg font-medium">{t('profile.moderator')}</h3>
            </div>
            <ValueRow label={t('profile.moderatorName')} value={moderator.full_name ?? moderator.username} />
            <ValueRow label={t('profile.moderatorRole')} value={moderator.role} />
            <ValueRow label={t('profile.moderatorContact')} value={moderator.email ?? moderator.phone} />
          </Card>
        ) : null}
      </div>
    </div>
  );
}
