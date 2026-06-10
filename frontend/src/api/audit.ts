import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { AuditLogItem } from './types';

export interface AuditParams {
  limit?: number;
  offset?: number;
  action?: string;
  username?: string;
}
export const listAuditLogs = (p: AuditParams = {}): Promise<AuditLogItem[]> =>
  apiFetch<AuditLogItem[]>(`/audit-logs${qs({ ...p })}`);
