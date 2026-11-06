import { api } from "./client";
import type { AlertView, ItemsResponse } from "./types";
export const adminAlertsApi = { list: () => api<ItemsResponse<AlertView>>("/api/admin/alerts") };
