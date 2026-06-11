import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { BarcodeCodeRead } from './types';

export interface BarcodeCodesParams {
  limit?: number;
  offset?: number;
  status?: string;
}

// GET /api/barcode-codes — справочник 2-буквенных кодов (staff).
// Модератор выбирает код отсюда при одобрении заявки.
export const listBarcodeCodes = (p: BarcodeCodesParams = {}): Promise<BarcodeCodeRead[]> =>
  apiFetch<BarcodeCodeRead[]>(`/barcode-codes${qs({ ...p })}`);
