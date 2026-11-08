import { api } from "./client";
import type { ItemsResponse, TicketPatch, TicketView } from "./types";
export const adminTicketsApi = { list: () => api<ItemsResponse<TicketView>>("/api/admin/tickets"), update: (id: number, patch: TicketPatch) => api<TicketView>(`/api/admin/tickets/${id}`, { method: "PATCH", body: JSON.stringify(patch) }) };
