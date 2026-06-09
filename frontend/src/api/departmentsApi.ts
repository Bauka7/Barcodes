import { http } from "./http";
import type { DepartmentTreeItem, SelectedDepartment } from "./types";

export const SELECTED_DEPARTMENT_STORAGE_KEY = "qazpost.selectedDepartment";

export async function getDepartmentsTree(): Promise<DepartmentTreeItem[]> {
  const response = await http.get<DepartmentTreeItem[]>("/departments/tree");
  return response.data;
}

export function saveSelectedDepartment(department: SelectedDepartment): void {
  localStorage.setItem(SELECTED_DEPARTMENT_STORAGE_KEY, JSON.stringify(department));
}

export function getSelectedDepartment(): SelectedDepartment | null {
  const rawValue = localStorage.getItem(SELECTED_DEPARTMENT_STORAGE_KEY);

  if (!rawValue) {
    return null;
  }

  try {
    const parsedValue = JSON.parse(rawValue) as SelectedDepartment;

    if (typeof parsedValue.id === "number" && typeof parsedValue.name === "string") {
      return parsedValue;
    }
  } catch {
    localStorage.removeItem(SELECTED_DEPARTMENT_STORAGE_KEY);
  }

  return null;
}
