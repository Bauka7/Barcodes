import { apiFetch } from './client';
import { qs } from '../lib/qs';
import type { UserCreate, UserRead, UserUpdate } from './types';

export const listUsers = (p: { limit?: number; offset?: number } = {}): Promise<UserRead[]> =>
  apiFetch<UserRead[]>(`/users${qs({ ...p })}`);

export const getUser = (id: number): Promise<UserRead> => apiFetch<UserRead>(`/users/${id}`);

export const createUser = (body: UserCreate): Promise<UserRead> =>
  apiFetch<UserRead>('/users', { method: 'POST', body });

export const updateUser = (id: number, body: UserUpdate): Promise<UserRead> =>
  apiFetch<UserRead>(`/users/${id}`, { method: 'PATCH', body });
