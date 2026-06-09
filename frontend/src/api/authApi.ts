import { http } from "./http";
import type { TokenResponse, UserRead } from "./types";

export async function loginRequest(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const response = await http.post<TokenResponse>("/auth/login", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return response.data;
}

export async function getCurrentUser(): Promise<UserRead> {
  const response = await http.get<UserRead>("/auth/me");
  return response.data;
}
