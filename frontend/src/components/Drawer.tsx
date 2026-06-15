import type { ReactNode } from 'react';

interface Props {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  width?: 'default' | 'wide';
}

// Боковая панель для форм (создание/редактирование).
export function Drawer({ open, onClose, title, children, width = 'default' }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30" onClick={onClose}>
      <div
        className={`h-full w-full overflow-auto border-l-[0.5px] border-bd2 bg-bg1 p-5 shadow-xl ${
          width === 'wide' ? 'max-w-[520px]' : 'max-w-[340px]'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <span className="text-[19px] font-medium">{title}</span>
          <button type="button" onClick={onClose} className="text-t2 hover:text-t1" aria-label="close">
            <i className="ti ti-x" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
