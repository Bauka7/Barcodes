import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { RangeRequestCreate, RangeRequestRead } from './types';

export interface RangeRequestsParams {
  limit?: number;
  offset?: number;
  status?: string;
  package_type?: string;
  client_id?: number;
  department_id?: number;
}
// client получает только свои заявки (фильтрует бэк).
export const listRangeRequests = (p: RangeRequestsParams = {}): Promise<RangeRequestRead[]> =>
  apiFetch<RangeRequestRead[]>(`/range-requests${qs({ ...p })}`);

export const getRangeRequest = (id: number): Promise<RangeRequestRead> =>
  apiFetch<RangeRequestRead>(`/range-requests/${id}`);

export const createRangeRequest = (body: RangeRequestCreate): Promise<RangeRequestRead> =>
  apiFetch<RangeRequestRead>('/range-requests', { method: 'POST', body });

export const approveRangeRequest = (id: number, notes?: string): Promise<RangeRequestRead> =>
  apiFetch<RangeRequestRead>(`/range-requests/${id}/approve`, { method: 'POST', body: { notes } });

export const rejectRangeRequest = (id: number, notes?: string): Promise<RangeRequestRead> =>
  apiFetch<RangeRequestRead>(`/range-requests/${id}/reject`, { method: 'POST', body: { notes } });

export const cancelRangeRequest = (id: number, notes?: string): Promise<RangeRequestRead> =>
  apiFetch<RangeRequestRead>(`/range-requests/${id}/cancel`, { method: 'POST', body: { notes } });
