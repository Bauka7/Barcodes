import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type {
  BarcodeDetailResponse,
  BarcodeLifecycleListResponse,
  BarcodeNumberResponse,
  GeneratedBatchDetail,
  GeneratedBatchItem,
  PrintedBatchItem,
} from './types';

export interface GenerateNumbersInput {
  package_type: string;
  quantity: number;
  department_id?: number | null;
  notes?: string;
}

// POST /barcodes/numbers — generated_by НЕ слать (раздел 3 брифа).
export function generateNumbers(input: GenerateNumbersInput): Promise<BarcodeNumberResponse> {
  return apiFetch<BarcodeNumberResponse>('/barcodes/numbers', { method: 'POST', body: input });
}

export interface LifecycleParams {
  status?: string;
  package_type?: string;
  department_id?: number;
  printed?: boolean;
  limit?: number;
  offset?: number;
}
export function listLifecycle(p: LifecycleParams): Promise<BarcodeLifecycleListResponse> {
  return apiFetch<BarcodeLifecycleListResponse>(`/barcodes/lifecycle${qs({ ...p })}`);
}

export function getBarcodeDetail(barcode: string): Promise<BarcodeDetailResponse> {
  return apiFetch<BarcodeDetailResponse>(`/barcodes/${encodeURIComponent(barcode)}/detail`);
}

export interface BatchesParams {
  limit?: number;
  offset?: number;
  package_type?: string;
  department_id?: number;
}
export function listBatches(p: BatchesParams): Promise<GeneratedBatchItem[]> {
  return apiFetch<GeneratedBatchItem[]>(`/barcodes/history/batches${qs({ ...p })}`);
}

export function getBatchDetail(batchId: number): Promise<GeneratedBatchDetail> {
  return apiFetch<GeneratedBatchDetail>(`/barcodes/history/batches/${batchId}`);
}

// PDF как blob (раздел 7 брифа).
export function previewBatchPdf(batchId: number): Promise<Blob> {
  return apiFetch<Blob>(`/barcodes/batches/${batchId}/pdf-preview`, { responseType: 'blob' });
}

export interface PrintBatchInput {
  printer_name?: string;
  notes?: string;
}
// POST .../pdf — printed_by НЕ слать; помечает партию напечатанной.
export function printBatchPdf(batchId: number, input: PrintBatchInput): Promise<Blob> {
  return apiFetch<Blob>(`/barcodes/batches/${batchId}/pdf`, {
    method: 'POST',
    body: input,
    responseType: 'blob',
  });
}

export interface PrintHistoryParams {
  limit?: number;
  offset?: number;
  department_id?: number;
  generated_batch_id?: number;
}
export function listPrintHistory(p: PrintHistoryParams): Promise<PrintedBatchItem[]> {
  return apiFetch<PrintedBatchItem[]>(`/barcodes/print-history${qs({ ...p })}`);
}

// Клиентские «мои» эндпоинты (по организации текущего пользователя).
export function listMyBatches(p: { limit?: number; offset?: number } = {}): Promise<GeneratedBatchItem[]> {
  return apiFetch<GeneratedBatchItem[]>(`/barcodes/my-batches${qs({ ...p })}`);
}

export function getMyBatchDetail(batchId: number): Promise<GeneratedBatchDetail> {
  return apiFetch<GeneratedBatchDetail>(`/barcodes/my-batches/${batchId}`);
}

export function listMyPrintHistory(p: { limit?: number; offset?: number } = {}): Promise<PrintedBatchItem[]> {
  return apiFetch<PrintedBatchItem[]>(`/barcodes/my-print-history${qs({ ...p })}`);
}
