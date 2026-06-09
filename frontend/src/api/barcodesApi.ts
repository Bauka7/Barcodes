import { http } from "./http";
import type {
  BarcodeNumberRequest,
  BarcodeNumberResponse,
  GeneratedBarcodeSearchResponse,
  GeneratedBatchDetail,
  GeneratedBatchItem,
  PrintBatchRequest,
  PrintedBatchItem,
} from "./types";

export const PACKAGE_TYPES = [
  "VC",
  "KG",
  "ON",
  "AD",
  "BP",
  "CE",
  "GF",
  "RZ",
  "AV",
  "UP",
  "CP",
  "CZ",
  "RC",
  "CC",
  "VR",
  "CV",
  "MM",
  "UB",
  "PP",
  "DQ",
  "UE",
  "UO",
  "CF",
  "RW",
  "RG",
  "LR",
  "GP",
  "CO",
  "GB",
  "RR",
] as const;

export interface ListBatchesParams {
  limit: number;
  offset: number;
  package_type?: string;
  department_id?: number;
}

export interface PrintHistoryParams {
  limit: number;
  offset: number;
  department_id?: number;
  generated_batch_id?: number;
}

export async function generateBarcodeNumbers(
  payload: BarcodeNumberRequest,
): Promise<BarcodeNumberResponse> {
  const response = await http.post<BarcodeNumberResponse>("/barcodes/numbers", payload);
  return response.data;
}

export async function listBatches(params: ListBatchesParams): Promise<GeneratedBatchItem[]> {
  const response = await http.get<GeneratedBatchItem[]>("/barcodes/history/batches", { params });
  return response.data;
}

export async function getBatchDetail(batchId: number): Promise<GeneratedBatchDetail> {
  const response = await http.get<GeneratedBatchDetail>(`/barcodes/history/batches/${batchId}`);
  return response.data;
}

export async function searchBarcode(barcode: string): Promise<GeneratedBarcodeSearchResponse> {
  const response = await http.get<GeneratedBarcodeSearchResponse>("/barcodes/history/search", {
    params: { barcode },
  });
  return response.data;
}

export async function previewBatchPdf(batchId: number): Promise<Blob> {
  const response = await http.get<Blob>(`/barcodes/batches/${batchId}/pdf-preview`, {
    responseType: "blob",
  });
  return response.data;
}

export async function printBatchPdf(batchId: number, payload: PrintBatchRequest): Promise<Blob> {
  const response = await http.post<Blob>(`/barcodes/batches/${batchId}/pdf`, payload, {
    responseType: "blob",
  });
  return response.data;
}

export async function listPrintHistory(params: PrintHistoryParams): Promise<PrintedBatchItem[]> {
  const response = await http.get<PrintedBatchItem[]>("/barcodes/print-history", { params });
  return response.data;
}
