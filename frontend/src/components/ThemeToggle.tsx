import { useTranslation } from 'react-i18next';
import { useTheme } from '../theme/ThemeContext';

// Светлая/тёмная тема (раздел 4 брифа). Иконка-кнопка рядом с переключателем языка.
export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const { t } = useTranslation();
  return (
    <button
      type="button"
      onClick={toggle}
      title={t('shell.theme')}
      aria-label={t('shell.theme')}
      className="flex h-7 w-7 items-center justify-center rounded-ctl border-[0.5px] border-bd2 text-t2 hover:text-t1"
    >
      <i className={`ti ti-${theme === 'dark' ? 'sun' : 'moon'} text-[15px]`} />
    </button>
  );
}
