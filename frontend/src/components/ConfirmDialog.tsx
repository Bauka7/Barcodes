import { useEffect, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from './Modal';
import { Button, Textarea } from './ui';

interface Props {
  open: boolean;
  title: ReactNode;
  message?: ReactNode;
  confirmLabel?: string;
  danger?: boolean;
  /** опциональное поле ввода (напр. причина отмены) */
  input?: { label?: string; placeholder?: string; required?: boolean };
  busy?: boolean;
  onConfirm: (value: string) => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  danger,
  input,
  busy,
  onConfirm,
  onCancel,
}: Props) {
  const { t } = useTranslation();
  const [value, setValue] = useState('');

  useEffect(() => {
    if (open) setValue('');
  }, [open]);

  const disabled = busy || (input?.required ? !value.trim() : false);

  return (
    <Modal open={open} onClose={onCancel} title={title}>
      {message && <p className="mb-3 text-[16px] text-t2">{message}</p>}
      {input && (
        <div className="mb-3">
          {input.label && <label className="mb-1 block text-[15px] text-t2">{input.label}</label>}
          <Textarea
            rows={2}
            value={value}
            placeholder={input.placeholder}
            onChange={(e) => setValue(e.target.value)}
          />
        </div>
      )}
      <div className="flex justify-end gap-2">
        <Button onClick={onCancel} disabled={busy}>
          {t('actions.cancel')}
        </Button>
        <Button
          variant={danger ? 'danger' : 'primary'}
          onClick={() => onConfirm(value)}
          disabled={disabled}
        >
          {confirmLabel ?? t('actions.confirm')}
        </Button>
      </div>
    </Modal>
  );
}
