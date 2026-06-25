import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { DepartmentItem, DepartmentTreeItem } from './types';

// Типы — из сгенерированного openapi (src/api/generated.ts), не пишем руками.
export type { DepartmentItem, DepartmentTreeItem };

export interface FilPassportDepartmentImportResponse {
  created: number;
  updated: number;
  skipped: number;
  missing: number;
  errors: string[];
  source_url: string;
  imported_at: string;
  dry_run: boolean;
}

// GET /api/departments/tree — иерархия (массив корней). Грузим один раз,
// строим map id->имя в lib/departmentName.ts (раздел 7 брифа).
export function getDepartmentTree(): Promise<DepartmentTreeItem[]> {
  return apiFetch<DepartmentTreeItem[]>('/departments/tree');
}

export function listDepartments(p: { search?: string; limit?: number; offset?: number } = {}): Promise<DepartmentItem[]> {
  return apiFetch<DepartmentItem[]>(`/departments${qs({ ...p })}`);
}

export function importFilPassportDepartments(
  dryRun = false,
): Promise<FilPassportDepartmentImportResponse> {
  return apiFetch<FilPassportDepartmentImportResponse>(
    `/admin/departments/import-filpassport${qs({ dry_run: dryRun })}`,
    { method: 'POST' },
  );
}
