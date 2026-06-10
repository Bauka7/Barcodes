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
