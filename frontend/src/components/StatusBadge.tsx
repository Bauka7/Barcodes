import { useTranslation } from 'react-i18next';
import { Chip, type ChipTone } from './Chip';

// Домены статусов: ШПИ (раздел 7), диапазоны (Шаг 10), заявки (Шаг 11).
type Domain = 'barcode' | 'range' | 'request';

const TONES: Record<Domain, Record<string, ChipTone>> = {
  barcode: { generated: 'info', printed: 'ok', used: 'muted', cancelled: 'bad' },
  range: { active: 'ok', exhausted: 'muted', closed: 'muted' },
  request: { pending: 'warn', approved: 'ok', rejected: 'bad', cancelled: 'muted' },
};

interface Props {
  status: string;
  domain?: Domain;
}

export function StatusBadge({ status, domain = 'barcode' }: Props) {
  const { t } = useTranslation();
  const tone = TONES[domain][status] ?? 'muted';
  const label = t(`status.${domain}.${status}`, { defaultValue: status });
  return <Chip tone={tone}>{label}</Chip>;
}
