export type UserRole = "admin" | "operator" | "client";

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserRead {
  id: number;
  username: string;
  full_name: string | null;
  role: UserRole;
  department_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DepartmentTreeItem {
  id: number;
  code: string;
  name: string;
  department_type: string | null;
  full_path: string | null;
  children: DepartmentTreeItem[];
}

export interface SelectedDepartment {
  id: number;
  code: string;
  name: string;
  full_path: string | null;
}

export interface BarcodeNumberRequest {
  package_type: string;
  quantity: number;
  department_id: number;
  notes?: string | null;
}

export interface BarcodeNumberResponse {
  batch_id: number;
  items: string[];
  count: number;
  first_barcode: string;
  last_barcode: string;
}

export interface GeneratedBatchItem {
  id: number;
  package_type: string;
  quantity: number;
  first_barcode: string;
  last_barcode: string;
  department_id: number | null;
  generated_by: string | null;
  source: string | null;
  status: string;
  generated_at: string;
  notes: string | null;
}

export interface GeneratedBarcodeItem {
  id: number;
  batch_id: number;
  barcode: string;
  package_type: string;
  department_id: number | null;
  sequence_number: number;
  printed: boolean;
  printed_at: string | null;
  generated_at: string;
}

export interface GeneratedBatchDetail extends GeneratedBatchItem {
  barcodes: GeneratedBarcodeItem[];
}

export interface GeneratedBarcodeSearchResponse extends GeneratedBarcodeItem {
  batch: GeneratedBatchItem;
}

export interface PrintBatchRequest {
  printer_name: string;
  notes?: string | null;
}

export interface PrintedBatchItem {
  id: number;
  generated_batch_id: number;
  department_id: number | null;
  printed_count: number;
  first_barcode: string;
  last_barcode: string;
  printed_by: string | null;
  printer_name: string | null;
  status: string;
  printed_at: string;
  notes: string | null;
}
