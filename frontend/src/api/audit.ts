import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { AuditLogItem } from './types';

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
export const listAuditLogs = (p: AuditParams = {}): Promise<AuditLogItem[]> =>
  apiFetch<AuditLogItem[]>(`/audit-logs${qs({ ...p })}`);
