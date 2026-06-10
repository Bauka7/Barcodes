import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { ClientCreate, ClientRead, ClientUpdate } from './types';

export interface ClientsParams {
  search?: string;
  limit?: number;
  offset?: number;
  is_active?: boolean;
}
export const listClients = (p: ClientsParams = {}): Promise<ClientRead[]> =>
  apiFetch<ClientRead[]>(`/clients${qs({ ...p })}`);

export const getClient = (id: number): Promise<ClientRead> =>
  apiFetch<ClientRead>(`/clients/${id}`);

export const createClient = (body: ClientCreate): Promise<ClientRead> =>
  apiFetch<ClientRead>('/clients', { method: 'POST', body });

export const updateClient = (id: number, body: ClientUpdate): Promise<ClientRead> =>
  apiFetch<ClientRead>(`/clients/${id}`, { method: 'PATCH', body });
