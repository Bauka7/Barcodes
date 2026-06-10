import { useTranslation } from 'react-i18next';

const SEG = 'px-2.5 py-1';

// Переключатель РУ / ҚАЗ. Язык сохраняется в localStorage (см. i18n/index.ts).
export function LangSwitch() {
  const { i18n } = useTranslation();
  const cur = i18n.resolvedLanguage;

  const set = (lng: 'ru' | 'kz') => {
    i18n.changeLanguage(lng);
    localStorage.setItem('lang', lng);
  };

  return (
    <div className="inline-flex w-fit overflow-hidden rounded-ctl border-[0.5px] border-bd2 text-[13px]">
      <button
        type="button"
        onClick={() => set('ru')}
        className={cur === 'ru' ? `${SEG} bg-brand font-medium text-white` : `${SEG} text-t2`}
      >
        РУ
      </button>
      <button
        type="button"
        onClick={() => set('kz')}
        className={cur === 'kz' ? `${SEG} bg-brand font-medium text-white` : `${SEG} text-t2`}
      >
        ҚАЗ
      </button>
    </div>
  );
}
