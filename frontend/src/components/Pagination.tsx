import { useTranslation } from 'react-i18next';

interface Props {
  offset: number;
  limit: number;
  /** сколько строк показано сейчас */
  shown: number;
  /** общий счётчик, если бэк его отдаёт */
  total?: number;
  /** если total нет — признак наличия следующей страницы */
  hasNext?: boolean;
  onChange: (offset: number) => void;
}

// Пагинация по limit/offset. Бэк QazPost тотал не отдаёт — используем hasNext.
export function Pagination({ offset, limit, shown, total, hasNext, onChange }: Props) {
  const { t } = useTranslation();
  const canPrev = offset > 0;
  const canNext = total != null ? offset + limit < total : !!hasNext;
  const label =
    total != null ? t('pagination.shown', { shown, total }) : t('pagination.shownNoTotal', { shown });

  const btn =
    'flex items-center rounded-ctl border-[0.5px] border-bd2 px-2 py-1 text-t2 disabled:opacity-40';

  return (
    <div className="mt-3 flex items-center justify-between text-[16px] text-t2">
      <span>{label}</span>
      <div className="flex gap-1.5">
        <button
          type="button"
          disabled={!canPrev}
          onClick={() => onChange(Math.max(0, offset - limit))}
          className={btn}
          aria-label="prev"
        >
          <i className="ti ti-chevron-left" />
        </button>
        <button
          type="button"
          disabled={!canNext}
          onClick={() => onChange(offset + limit)}
          className={btn}
          aria-label="next"
        >
          <i className="ti ti-chevron-right" />
        </button>
      </div>
    </div>
  );
}
