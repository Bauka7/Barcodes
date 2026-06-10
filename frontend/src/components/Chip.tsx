import type { ReactNode } from 'react';

// Чип статуса/метки. Тона — из палитры design-reference.html.
export type ChipTone = 'ok' | 'bad' | 'info' | 'muted' | 'warn';

const TONE: Record<ChipTone, string> = {
  ok: 'bg-sx text-st',
  bad: 'bg-dx text-dt',
  info: 'bg-brand-tint text-brand-dark',
  muted: 'bg-bg3 text-t2',
  warn: 'bg-wx text-wt',
};

interface Props {
  tone?: ChipTone;
  children: ReactNode;
  className?: string;
}

export function Chip({ tone = 'muted', children, className = '' }: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-ctl px-2 py-0.5 text-[13px] ${TONE[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
