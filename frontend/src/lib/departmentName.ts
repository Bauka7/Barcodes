import { useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getDepartmentTree, type DepartmentTreeItem } from '../api/departments';

// Плоский список всех узлов дерева (для поиска/маппинга).
export function flattenDepartments(nodes: DepartmentTreeItem[]): DepartmentTreeItem[] {
  const out: DepartmentTreeItem[] = [];
  const walk = (ns: DepartmentTreeItem[]) => {
    for (const n of ns) {
      out.push(n);
      if (n.children?.length) walk(n.children);
    }
  };
  walk(nodes);
  return out;
}

// map id -> name по дереву (раздел 7 брифа).
export function buildDepartmentNameMap(nodes: DepartmentTreeItem[]): Map<number, string> {
  const map = new Map<number, string>();
  for (const n of flattenDepartments(nodes)) map.set(n.id, n.name);
  return map;
}

const TREE_KEY = ['departments', 'tree'] as const;

// Дерево грузим один раз и держим в кэше (id->имя нужен многим таблицам).
export function useDepartmentTree() {
  return useQuery({
    queryKey: TREE_KEY,
    queryFn: getDepartmentTree,
    staleTime: 5 * 60_000,
  });
}

export function useDepartmentNameMap() {
  const { data, isLoading, isError } = useDepartmentTree();
  const map = useMemo(() => buildDepartmentNameMap(data ?? []), [data]);
  return { map, isLoading, isError };
}

// Резолвер id -> имя для таблиц: '—' для null/пусто, '#id' если не найдено в дереве.
export function useDepartmentName(): (id?: number | null) => string {
  const { map } = useDepartmentNameMap();
  return useCallback((id?: number | null) => (id == null ? '—' : (map.get(id) ?? `#${id}`)), [map]);
}
