import { apiFetch } from './client';
import type { Role } from '../types';

// Шейпы из контракта (раздел 3 брифа). Когда появится src/api/generated.ts
// (openapi-typescript), эти типы заменим на сгенерированные.
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface Me {
  id: number;
  username: string;
  email: string | null;
  phone: string | null;
  full_name: string | null;
  role: Role;
  role_label: string;
  department_id: number | null;
  client_id: number | null;
  is_active: boolean;
  department: {
    id: number;
    code: string;
    name: string;
    region: string | null;
    department_type: string | null;
    full_path: string | null;
  } | null;
  moderator: {
    id: number;
    username: string;
    full_name: string | null;
    email: string | null;
    phone: string | null;
    role: Role;
  } | null;
}

// POST /api/auth/login — тело form-urlencoded (НЕ JSON), без Bearer.
export function login(username: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams({ username, password });
  return apiFetch<LoginResponse>('/auth/login', { method: 'POST', body, auth: false });
}

// GET /api/auth/me — текущий профиль (роль определяет навигацию и гарды).
export function getMe(): Promise<Me> {
  return apiFetch<Me>('/auth/me');
}
