import type { ReactNode } from 'react';

interface Props {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  panelClassName?: string;
  position?: 'center' | 'right';
}

export function Modal({
  open,
  onClose,
  title,
  children,
  panelClassName = '',
  position = 'center',
}: Props) {
  if (!open) return null;

  const overlayClassName =
    position === 'right'
      ? 'fixed inset-0 z-50 bg-black/30'
      : 'fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4';

  const panelClassNameResolved =
    position === 'right'
      ? `absolute right-0 top-0 flex h-full w-full max-w-[420px] flex-col overflow-y-auto rounded-none border-l-[0.5px] border-bd3 bg-bg1 p-5 shadow-xl ${panelClassName}`
      : `w-full max-w-sm rounded-card border-[0.5px] border-bd3 bg-bg1 p-5 shadow-xl ${panelClassName}`;

  return (
    <div
      className={overlayClassName}
      onClick={onClose}
    >
      <div
        className={panelClassNameResolved}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <div className="mb-3 flex items-start justify-between gap-3">
            <div className="text-[19px] font-medium">{title}</div>
            <button
              type="button"
              aria-label="Close"
              className="text-t2 transition-colors hover:text-t1"
              onClick={onClose}
            >
              <i className="ti ti-x text-xl" />
            </button>
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
