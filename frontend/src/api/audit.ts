import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { AuditLogItem, AuditLogListResponse } from './types';

export interface AuditParams {
  limit?: number;
  offset?: number;
  action?: string;
  username?: string;
  entity_type?: string;
  entity_id?: string;
  department_id?: number;
  date_from?: string;
  date_to?: string;
}

function normalizeAuditResponse(
  data: AuditLogListResponse | AuditLogItem[],
  params: AuditParams,
): AuditLogListResponse {
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
      limit: params.limit ?? data.length,
      offset: params.offset ?? 0,
    };
  }

  return data;
}

export const listAuditLogs = async (p: AuditParams = {}): Promise<AuditLogListResponse> => {
  const data = await apiFetch<AuditLogListResponse | AuditLogItem[]>(`/audit-logs${qs({ ...p })}`);
  return normalizeAuditResponse(data, p);
};
