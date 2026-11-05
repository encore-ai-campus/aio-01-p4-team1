import type { ApiError } from "./types";
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, credentials: "include", headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
  const body = await response.json().catch(() => null) as T | ApiError | null;
  if (!response.ok) throw new Error((body as ApiError | null)?.error?.message ?? "요청을 처리하지 못했습니다.");
  if (body === null) throw new Error("응답을 확인할 수 없습니다.");
  return body as T;
}
