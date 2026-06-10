import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react';

const control =
  'w-full rounded-ctl border-[0.5px] border-bd2 bg-bg1 px-2.5 py-2 text-[16px] text-t1 outline-none focus:border-brand disabled:opacity-60';

interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'default' | 'danger';
  size?: 'sm' | 'md';
}

export function Button({ variant = 'default', size = 'md', className = '', ...rest }: BtnProps) {
  const base =
    'inline-flex items-center justify-center gap-1.5 rounded-ctl border-[0.5px] disabled:opacity-50 disabled:cursor-not-allowed';
  const sizes = size === 'sm' ? 'px-2.5 py-1 text-[15px]' : 'px-3 py-1.5 text-[16px]';
  const variants =
    variant === 'primary'
      ? 'border-brand bg-brand text-white hover:bg-brand-dark font-medium'
      : variant === 'danger'
        ? 'border-danger bg-danger text-white hover:opacity-90 font-medium'
        : 'border-bd2 bg-bg1 text-t1 hover:bg-bg2';
  return <button className={`${base} ${sizes} ${variants} ${className}`} {...rest} />;
}

export function Input({ className = '', ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`${control} ${className}`} {...rest} />;
}

export function Select({
  className = '',
  children,
  ...rest
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={`${control} ${className}`} {...rest}>
      {children}
    </select>
  );
}

export function Textarea({ className = '', ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`${control} ${className}`} {...rest} />;
}

export function Field({
  label,
  children,
  className = '',
}: {
  label?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mb-3 ${className}`}>
      {label && <label className="mb-1 block text-[15px] text-t2">{label}</label>}
      {children}
    </div>
  );
}

export function Card({ className = '', children }: { className?: string; children: ReactNode }) {
  return (
    <div className={`rounded-card border-[0.5px] border-bd3 bg-bg1 p-4 ${className}`}>{children}</div>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div>
        <h2 className="text-2xl font-medium">{title}</h2>
        {subtitle && <p className="mt-0.5 text-[16px] text-t2">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Loading({ label = '…' }: { label?: string }) {
  return <div className="py-8 text-center text-[16px] text-t2">{label}</div>;
}

export function ErrorText({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return <div className="rounded-ctl bg-dx px-2.5 py-1.5 text-[15px] text-dt">{msg}</div>;
}
