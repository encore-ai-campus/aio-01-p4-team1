import { api } from "./client";
import type { AccountView, CreateAccountRequest, CreateEmployeeRequest, EmployeeAdminView, ItemsResponse } from "./types";
export const adminUsersApi = {
  listEmployees: () => api<ItemsResponse<EmployeeAdminView>>("/api/admin/employees"),
  listAccounts: () => api<ItemsResponse<AccountView>>("/api/admin/users"),
  createEmployee: (request: CreateEmployeeRequest) => api<EmployeeAdminView>("/api/admin/employees", { method: "POST", body: JSON.stringify(request) }),
  create: (request: CreateAccountRequest) => api<AccountView>("/api/admin/users", { method: "POST", body: JSON.stringify(request) }),
  setActive: (id: number, is_active: boolean) => api<AccountView>(`/api/admin/users/${id}`, { method: "PATCH", body: JSON.stringify({ is_active }) }),
  resetPassword: (id: number, temporary_password: string) => api<{ ok: true }>(`/api/admin/users/${id}/reset-password`, { method: "POST", body: JSON.stringify({ temporary_password }) }),
  deleteAccount: (id: number) => api<{ ok: true }>(`/api/admin/users/${id}`, { method: "DELETE" }),
};
