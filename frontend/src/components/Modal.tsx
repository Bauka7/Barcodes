import type { ReactNode } from 'react';

interface Props {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
}

export function Modal({ open, onClose, title, children }: Props) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-card border-[0.5px] border-bd3 bg-bg1 p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {title && <div className="mb-3 text-[19px] font-medium">{title}</div>}
        {children}
      </div>
    </div>
  );
}
