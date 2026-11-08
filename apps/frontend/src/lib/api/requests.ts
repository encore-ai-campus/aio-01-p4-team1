import { api } from "./client";
import type { InquiryView, ItemsResponse } from "./types";
export const requestsApi = { listMine: () => api<ItemsResponse<InquiryView>>("/api/my-requests") };
