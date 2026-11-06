"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiRequestError } from "../../../lib/api/client";
import { me } from "../../../lib/api/auth";
import { logout } from "../../../lib/api/auth";
import type { AskResponse, User } from "../../../lib/api/types";

const prompts = [["◒", "VPN 연결 오류", "재택근무·네트워크"], ["◎", "계정 잠김", "로그인·접근 권한"], ["▣", "장비 고장", "노트북·주변기기"]];
export default function AskPage() {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [originalQuestion, setOriginalQuestion] = useState("");
  const [requestId, setRequestId] = useState("");
  const [attempt, setAttempt] = useState(1);
  const [context, setContext] = useState("");
  const [clarificationAnswer, setClarificationAnswer] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingUser, setLoadingUser] = useState(true);
  const [pendingFollowup, setPendingFollowup] = useState<{ id: string; text: string } | null>(null);
  const [logoutError, setLogoutError] = useState("");

  async function signOut() { setLogoutError(""); try { await logout(); router.replace("/login"); } catch (cause) { setLogoutError(cause instanceof Error ? cause.message : "로그아웃에 실패했습니다."); } }

  useEffect(() => {
    me().then(setUser).catch((err: unknown) => {
      if (err instanceof ApiRequestError && err.status === 401) {
        router.replace("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "로그인 상태를 확인하지 못했습니다.");
    }).finally(() => setLoadingUser(false));
  }, [router]);

  async function sendAsk(payload: { question: string; request_id: string; attempt: number; context?: string }) {
    setBusy(true);
    setError("");
    try {
      const data = await api<AskResponse>("/api/ask", { method: "POST", body: JSON.stringify(payload) });
      setResult(data);
      setClarificationAnswer("");
      setPendingFollowup(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "질문을 처리하지 못했습니다.");
    } finally {
      setBusy(false);
    }
  }

  async function submitQuestion(event: FormEvent) {
    event.preventDefault();
    const value = question.trim();
    if (value.length < 1 || value.length > 500) {
      setError("질문은 1~500자로 입력해 주세요.");
      return;
    }
    if (!user) {
      router.replace("/login");
      return;
    }

    const retrySameRequest = !result && requestId && originalQuestion === value && attempt === 1;
    const id = retrySameRequest ? requestId : crypto.randomUUID();
    setOriginalQuestion(value);
    setRequestId(id);
    setAttempt(1);
    setContext("");
    setResult(null);
    setPendingFollowup(null);
    await sendAsk({ question: value, request_id: id, attempt: 1 });
  }

  async function submitClarification(event: FormEvent) {
    event.preventDefault();
    const value = clarificationAnswer.trim();
    if (!value) {
      setError("보완 내용을 입력해 주세요.");
      return;
    }
    if (!originalQuestion || !result || result.route !== "보완 질문" || attempt >= 3) return;

    const previousRequest = pendingFollowup?.text === value ? pendingFollowup.id : crypto.randomUUID();
    const nextAttempt = pendingFollowup?.text === value ? attempt : attempt + 1;
    const nextContext = [
      context,
      `이전 문의: ${originalQuestion}`,
      `보완 질문: ${result.answer}`,
      `보완 답변: ${value}`,
    ].filter(Boolean).join("\n");
    if (nextContext.length > 2000) {
      setError("보완 내용이 너무 깁니다. 간단히 줄여 주세요.");
      return;
    }

    setRequestId(previousRequest);
    setAttempt(nextAttempt);
    setContext(nextContext);
    setPendingFollowup({ id: previousRequest, text: value });
    await sendAsk({ question: originalQuestion, request_id: previousRequest, attempt: nextAttempt, context: nextContext });
  }

  const displayName = user?.name ?? "사용자";
  const displayDept = user ? `${user.dept} · ${user.role === "admin" ? "관리자" : "직원"}` : "";

  if (loadingUser) return <main className="center"><p>로그인 상태를 확인하고 있습니다…</p></main>;

  return <main className="ask-shell">
    <aside className="ask-sidebar">
      <div className="brand"><span className="brand-mark">●</span><div><strong>오케퐁</strong><small>IT HELPDESK</small></div></div>
      <div className="side-section"><span className="side-label">WORKSPACE</span><a className="side-link active" href="/ask">▤ <span>질문하기</span></a><a className="side-link" href="/my-requests">▤ <span>내 문의</span></a></div>
      <button className="profile" type="button" onClick={() => void signOut()}><span>{displayName.slice(0, 1)}</span><div><b>{displayName}</b><small>{displayDept}</small></div><i>로그아웃</i></button>
    </aside>
    <section className="ask-main">
      <header className="ask-header"><div>IT 헬프데스크 <b>/ 질문하기</b></div></header>
      <div className="ask-content">
        <div className="ask-heading"><div><p className="eyebrow">SMART IT SUPPORT</p><h1>무엇을 도와드릴까요?</h1><p>업무 중 마주친 IT 문제를 알려주시면 가장 빠른 해결 방법을 찾아드려요.</p></div><span className="secure">♢ 로그인된 사내 계정으로 이용 중</span></div>
        <div className="quick-prompts">{prompts.map(([icon, title, desc]) => <button key={title} type="button" onClick={() => setQuestion(title)}><span>{icon}</span><b>{title}<small>{desc}</small></b></button>)}</div>
        <div className="ask-grid">
          <div className="ask-left">
            <form className="ask-card" onSubmit={submitQuestion}>
              <div className="ask-card-head"><div><p className="eyebrow">ASK OKEPONG</p><h2>문제 상황을 알려주세요</h2><p>오류 메시지와 발생 시점을 함께 적으면 더 정확하게 안내할 수 있어요.</p></div><span>1차 문의</span></div>
              <div className="textarea-wrap"><textarea value={question} onChange={event => setQuestion(event.target.value)} maxLength={500} placeholder="예) 재택근무 중 VPN에 연결하면 인증 오류가 반복됩니다."/><small>{question.length} / 500</small></div>
              <div className="ask-actions"><span>♢ 제출한 문의는 저장한 뒤 처리하며, 결과는 내 문의에서 확인할 수 있습니다.</span><button className="send" disabled={busy || !user}>{busy ? "확인 중…" : "질문 보내기　➤"}</button></div>
              {(error || logoutError) && <p className="error" role="alert">{error || logoutError}</p>}
            </form>
            {result?.route === "보완 질문" && attempt < 3 && <form className="ask-card" onSubmit={submitClarification}>
              <div className="ask-card-head"><div><p className="eyebrow">추가 정보</p><h2>확인 질문에 답해 주세요</h2><p>{result.answer}</p></div><span>{attempt + 1}차 문의</span></div>
              <div className="textarea-wrap"><textarea value={clarificationAnswer} onChange={event => setClarificationAnswer(event.target.value)} maxLength={500} placeholder="확인한 내용이나 오류 메시지를 적어 주세요."/><small>{clarificationAnswer.length} / 500</small></div>
              <div className="ask-actions"><span>추가 답변은 이전 질문 맥락과 함께 저장됩니다.</span><button className="send" disabled={busy}>{busy ? "확인 중…" : "보완 내용 보내기　➤"}</button></div>
              {error && <p className="error" role="alert">{error}</p>}
            </form>}
            <div className="steps"><div><b>01</b><strong>빠른 안내</strong><small>규정과 가이드를 먼저 찾아요</small></div><div><b>02</b><strong>안전한 이관</strong><small>필요하면 IT팀에 연결해요</small></div><div><b>03</b><strong>진행 확인</strong><small>내 문의에서 상태를 확인해요</small></div></div>
          </div>
          <section className={`answer-card ${result ? "has-result" : ""}`}>
            {result ? <><p className="eyebrow">{result.route}</p><h2>답변</h2><p>{result.answer}</p>{result.sources.length > 0 && <div className="sources"><b>근거 문서</b>{result.sources.map(source => <span key={`${source.doc}-${source.section}`}>{source.doc} · {source.section}</span>)}</div>}{result.ticket && <div className="ticket">티켓 {result.ticket.ticket_id} · {result.ticket.priority === "high" ? "긴급" : "보통"}</div>}</> : <><span className="answer-icon">▤</span><h2>답변이 여기에 표시됩니다</h2><p>업무 중 발생한 IT 문제를 구체적으로 알려주시면 규정과 가이드를 바탕으로 안내해 드려요.</p><span className="answer-time">실제 처리 시간은 문의 내용과 서비스 상태에 따라 달라질 수 있습니다.</span></>}
          </section>
        </div>
      </div>
    </section>
  </main>;
}
