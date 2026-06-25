import { apiFetch } from './client';

export type ShpiMapStatus = 'green' | 'gray' | 'red';

export interface ShpiMapCodeItem {
  code: string;
  region_code: string;
  current_value: number;
  status: ShpiMapStatus;
}

export interface ShpiMapRegionItem {
  code: string;
  name: string;
}

export interface ShpiMapResponse {
  regions: ShpiMapRegionItem[];
  region_codes: string[];
  codes: string[];
  cells: ShpiMapCodeItem[];
}

export const getShpiMap = (): Promise<ShpiMapResponse> =>
  apiFetch<ShpiMapResponse>('/admin/shpi-map');
