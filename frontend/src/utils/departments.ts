import type { DepartmentTreeItem, SelectedDepartment } from "../api/types";

export function toSelectedDepartment(node: DepartmentTreeItem): SelectedDepartment {
  return {
    id: node.id,
    code: node.code,
    name: node.name,
    full_path: node.full_path,
  };
}

export function filterDepartmentTree(
  nodes: DepartmentTreeItem[],
  searchValue: string,
): DepartmentTreeItem[] {
  const query = searchValue.trim().toLowerCase();

  if (!query) {
    return nodes;
  }

  return nodes
    .map((node) => {
      const filteredChildren = filterDepartmentTree(node.children, query);
      const searchableText = [
        node.name,
        node.code,
        node.department_type ?? "",
        node.full_path ?? "",
      ]
        .join(" ")
        .toLowerCase();

      if (searchableText.includes(query) || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren,
        };
      }

      return null;
    })
    .filter((node): node is DepartmentTreeItem => node !== null);
}
