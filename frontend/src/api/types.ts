// Централизованные алиасы типов из сгенерированного openapi (не пишем руками).
import type { components } from './generated';

type S = components['schemas'];

export type GeneratedBatchItem = S['GeneratedBatchItem'];
export type GeneratedBarcodeItem = S['GeneratedBarcodeItem'];
export type GeneratedBatchDetail = S['GeneratedBatchDetail'];
export type GeneratedBarcodeSearchResponse = S['GeneratedBarcodeSearchResponse'];
export type BarcodeDetailResponse = S['BarcodeDetailResponse'];
export type BarcodeNumberRequest = S['BarcodeNumberRequest'];
export type BarcodeNumberResponse = S['BarcodeNumberResponse'];
export type BarcodeLifecycleListResponse = S['BarcodeLifecycleListResponse'];
export type PrintedBatchItem = S['PrintedBatchItem'];
export type PrintBatchRequest = S['PrintBatchRequest'];

export type BarcodeRangeRead = S['BarcodeRangeRead'];
export type RangeRemainingResponse = S['RangeRemainingResponse'];
export type RangeGenerateRequest = S['RangeGenerateRequest'];

export type RangeRequestRead = S['RangeRequestRead'];
export type RangeRequestCreate = S['RangeRequestCreate'];
export type RangeRequestDecision = S['RangeRequestDecision'];

export type ClientRead = S['ClientRead'];
export type ClientCreate = S['ClientCreate'];
export type ClientUpdate = S['ClientUpdate'];

export type UserRead = S['UserRead'];
export type UserCreate = S['UserCreate'];
export type UserUpdate = S['UserUpdate'];

export type AuditLogItem = S['AuditLogItem'];

export type DepartmentItem = S['DepartmentItem'];
export type DepartmentTreeItem = S['DepartmentTreeItem'];
