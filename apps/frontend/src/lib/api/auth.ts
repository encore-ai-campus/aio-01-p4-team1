import { api } from "./client";
import type { User } from "./types";
export const login = (login_id: string, password: string) => api<{ user: User }>("/api/auth/login", { method: "POST", body: JSON.stringify({ login_id, password }) });
export const logout = () => api<{ ok: true }>("/api/auth/logout", { method: "POST" });
export const me = () => api<User>("/api/auth/me");
