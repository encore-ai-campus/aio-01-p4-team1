import type { AskResponse } from "../lib/api/types";
export const mockAsk: AskResponse = { request_id: "ui-auto-001", route: "자동 답변", answer: "VPN 접속 오류 항목의 점검 순서를 확인해 주세요.", sources: [{ doc: "remote-work-vpn", section: "접속 오류", score: 0.82 }], ticket: null, agents: ["triage", "retriever", "writer", "verifier"], security: {} };
