import { useTranslation } from 'react-i18next';
import { Card, PageHeader } from '../components/ui';

// Заглушка (раздел 6, п.14): эндпоинтов настроек нет — никаких вызовов API.
export default function SettingsPage() {
  const { t } = useTranslation();
  return (
    <div>
      <PageHeader title={t('settings.title')} subtitle={t('settings.subtitle')} />
      <Card className="max-w-xl">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-ctl bg-brand-tint text-brand-dark">
            <i className="ti ti-settings text-2xl" />
          </div>
          <div>
            <div className="text-[18px] font-medium">{t('settings.stubTitle')}</div>
            <p className="mt-1 text-[16px] text-t2">{t('settings.stubBody')}</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
