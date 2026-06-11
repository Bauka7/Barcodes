import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type {
  BarcodeNumberResponse,
  BarcodeRangeRead,
  GeneratedBatchItem,
  RangeRemainingResponse,
} from './types';

export interface RangesParams {
  limit?: number;
  offset?: number;
  package_type?: string;
  status?: string;
  client_id?: number;
  department_id?: number;
}
export const listRanges = (p: RangesParams = {}): Promise<BarcodeRangeRead[]> =>
  apiFetch<BarcodeRangeRead[]>(`/ranges${qs({ ...p })}`);

// GET /ranges/my — диапазоны, выданные организации текущего клиента.
export const listMyRanges = (
  p: { limit?: number; offset?: number; status?: string } = {},
): Promise<BarcodeRangeRead[]> =>
  apiFetch<BarcodeRangeRead[]>(`/ranges/my${qs({ ...p })}`);

export const getRange = (id: number): Promise<BarcodeRangeRead> =>
  apiFetch<BarcodeRangeRead>(`/ranges/${id}`);

export const getRangeRemaining = (id: number): Promise<RangeRemainingResponse> =>
  apiFetch<RangeRemainingResponse>(`/ranges/${id}/remaining`);

export const listRangeBatches = (
  id: number,
  p: { limit?: number; offset?: number } = {},
): Promise<GeneratedBatchItem[]> =>
  apiFetch<GeneratedBatchItem[]>(`/ranges/${id}/batches${qs({ ...p })}`);

export const generateFromRange = (
  id: number,
  body: { quantity: number; notes?: string },
): Promise<BarcodeNumberResponse> =>
  apiFetch<BarcodeNumberResponse>(`/ranges/${id}/generate`, { method: 'POST', body });

// Отмена диапазона модератором (с причиной).
export const cancelRange = (id: number, reason: string): Promise<BarcodeRangeRead> =>
  apiFetch<BarcodeRangeRead>(`/ranges/${id}/cancel`, { method: 'POST', body: { reason } });

// Продление диапазона: новый срок (ISO-строка).
export const renewRange = (id: number, expires_at: string): Promise<BarcodeRangeRead> =>
  apiFetch<BarcodeRangeRead>(`/ranges/${id}/renew`, { method: 'POST', body: { expires_at } });
