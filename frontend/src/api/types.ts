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

export type AuditLogItem = S['AuditLogItem'] & {
  department_id?: number | null;
  department_name?: string | null;
  department_code?: string | null;
  department_full_path?: string | null;
};

export type DepartmentItem = S['DepartmentItem'];
export type DepartmentTreeItem = S['DepartmentTreeItem'];
