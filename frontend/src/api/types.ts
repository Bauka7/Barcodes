// Централизованные алиасы типов из сгенерированного openapi (не пишем руками).
import type { components } from './generated';

type S = components['schemas'];

export type GeneratedBatchItem = S['GeneratedBatchItem'];
export type GeneratedBarcodeItem = S['GeneratedBarcodeItem'] & {
  generated_by?: string | null;
  printed_by?: string | null;
};
export type GeneratedBatchDetail = S['GeneratedBatchDetail'];
export type GeneratedBarcodeSearchResponse = S['GeneratedBarcodeSearchResponse'];
export type BarcodeDetailResponse = S['BarcodeDetailResponse'] & {
  generated_by?: string | null;
  printed_by?: string | null;
  range_created_by?: string | null;
};
export type BarcodeNumberRequest = S['BarcodeNumberRequest'];
export type BarcodeNumberResponse = S['BarcodeNumberResponse'];
export type BarcodeLifecycleListResponse = S['BarcodeLifecycleListResponse'];
export type PrintedBatchItem = S['PrintedBatchItem'];
export type PrintBatchRequest = S['PrintBatchRequest'];

export type BarcodeRangeRead = S['BarcodeRangeRead'];
export type RangeRemainingResponse = S['RangeRemainingResponse'];
export type RangeGenerateRequest = S['RangeGenerateRequest'];

export type BarcodeCodeRead = S['BarcodeCodeRead'];

export type RangeRequestRead = S['RangeRequestRead'];
export type RangeRequestCreate = S['RangeRequestCreate'];
export type RangeRequestDecision = S['RangeRequestDecision'];

export type ClientRead = S['ClientRead'];
export type ClientCreate = S['ClientCreate'];
export type ClientUpdate = S['ClientUpdate'];

export type UserRead = S['UserRead'];
export type UserCreate = S['UserCreate'];
export type UserUpdate = S['UserUpdate'];

// Kept explicit until the checked-in OpenAPI client is regenerated.
export interface AuditLogItem {
  id: number;
  user_id: number | null;
  department_id: number | null;
  department_name: string | null;
  department_code: string | null;
  department_full_path: string | null;
  username: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  details: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  limit: number;
  offset: number;
}

// Kept explicit until the checked-in OpenAPI client is regenerated.
export interface DepartmentItem {
  id: number;
  external_id: string | null;
  code: string;
  name: string;
  region: string;
  shpi_region_code: string | null;
  shpi_region_name: string | null;
  parent_id: number | null;
  department_type: string | null;
  full_path: string | null;
  is_active: boolean;
}

export interface DepartmentTreeItem {
  id: number;
  external_id: string | null;
  code: string;
  name: string;
  shpi_region_code: string | null;
  shpi_region_name: string | null;
  department_type: string | null;
  full_path: string | null;
  is_active: boolean;
  children: DepartmentTreeItem[];
}
