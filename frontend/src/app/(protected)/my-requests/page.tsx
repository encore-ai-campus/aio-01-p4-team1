"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { requestsApi } from "../../../lib/api/requests";
import type { InquiryView } from "../../../lib/api/types";

function ticketStatus(ticket: InquiryView["ticket"]) { if (!ticket) return "티켓 없음"; const status = ticket.status; return status === "resolved" ? "완료" : status === "in_progress" ? "처리 중" : status === "open" ? "접수" : status ?? "현재 상태 정보 미제공"; }
function ticketReply(ticket: InquiryView["ticket"]) { return typeof ticket?.reply === "string" ? ticket.reply : ""; }
function answerOf(item: InquiryView) { const result = item.result; if (!result || typeof result !== "object") return ""; const answer = (result as Record<string, unknown>).answer; return typeof answer === "string" ? answer : ""; }
export default function MyRequestsPage() {
  const [items, setItems] = useState<InquiryView[]>([]);
  const [openId, setOpenId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await requestsApi.listMine();
      setItems(response.items);
      setOpenId((current) => response.items.some((item) => item.request_id === current)
        ? current
        : response.items[0]?.request_id ?? "");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "문의 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return <main className="requests-content">
    <div className="requests-title-row">
      <div className="requests-title"><span className="title-bubble" aria-hidden="true">•••</span><div><h1>내 문의</h1><p>오케퐁에 문의한 내용과 처리 현황을 확인할 수 있어요.</p></div></div>
      <div className="requests-actions"><button className="refresh-button" type="button" disabled={loading} onClick={() => void load()}>⟳　새로고침</button><Link className="ask-button" href="/ask">✎　질문하기</Link></div>
    </div>
    {error && <p className="error" role="alert">{error}</p>}
    {loading ? <section className="request-empty" role="status">문의 목록을 불러오는 중입니다…</section>
      : items.length === 0 ? <section className="request-empty"><strong>아직 문의가 없습니다.</strong><Link href="/ask">첫 질문 남기기</Link></section>
        : <div className="request-list">{items.map((item) => {
          const status = ticketStatus(item.ticket);
          const reply = ticketReply(item.ticket);
          const answer = answerOf(item);
          const expanded = openId === item.request_id;
          const detailId = `request-detail-${item.request_id}`;
          return <article className={`request-card ${expanded ? "expanded" : ""}`} key={item.request_id}>
            <button className="request-summary" type="button" aria-expanded={expanded} aria-controls={detailId} onClick={() => setOpenId(expanded ? "" : item.request_id)}>
              <span className="request-icon" aria-hidden="true">◌</span>
              <span className="request-copy"><strong>{item.question}</strong><small>문의 번호 {item.request_id} · {new Date(item.created_at).toLocaleString("ko-KR")}</small></span>
              <span className="request-status">{status}</span><span className="chevron" aria-hidden="true">{expanded ? "⌃" : "⌄"}</span>
            </button>
            {expanded && <div className="request-detail" id={detailId} role="region" aria-label={`${item.request_id} 문의 상세`}>
              <div><b>문의 내용</b><p>{item.question}</p></div>
              {answer && <div><b>자동 안내</b><p>{answer}</p></div>}
              {reply && <div><b>담당자 답변</b><p>{reply}</p></div>}
              <div className="request-meta"><span><b>현재 티켓 상태</b>　{status}</span>{item.ticket?.ticket_id && <span><b>티켓 번호</b>　{item.ticket.ticket_id}</span>}</div>
            </div>}
          </article>;
        })}</div>}
  </main>;
}
