import { apiFetch } from './client';
import type { components } from './generated';

// Типы — из сгенерированного openapi (src/api/generated.ts), не пишем руками.
export type DepartmentTreeItem = components['schemas']['DepartmentTreeItem'];
export type DepartmentItem = components['schemas']['DepartmentItem'];

// GET /api/departments/tree — иерархия (массив корней). Грузим один раз,
// строим map id->имя в lib/departmentName.ts (раздел 7 брифа).
export function getDepartmentTree(): Promise<DepartmentTreeItem[]> {
  return apiFetch<DepartmentTreeItem[]>('/departments/tree');
}
