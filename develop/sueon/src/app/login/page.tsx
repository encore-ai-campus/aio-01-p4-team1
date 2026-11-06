"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "../../lib/api/auth";
export default function LoginPage() { const router = useRouter(); const [loginId,setLoginId]=useState(""); const [password,setPassword]=useState(""); const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
  async function submit(e: FormEvent) { e.preventDefault(); if (!loginId.trim() || !password) { setError("로그인 ID와 비밀번호를 입력해 주세요."); return; } setBusy(true); setError(""); try { const { user } = await login(loginId.trim(), password); router.replace(user.must_change_password ? "/change-password" : user.role === "admin" ? "/admin/tickets" : "/ask"); } catch (err) { setError(err instanceof Error ? err.message : "로그인에 실패했습니다."); } finally { setBusy(false); } }
  return <main className="center"><section className="card" style={{width:"min(420px, calc(100% - 32px))"}}><p className="muted">오케퐁 IT 헬프데스크</p><h1>로그인</h1><form onSubmit={submit}><label className="field">로그인 ID<input value={loginId} onChange={e=>setLoginId(e.target.value)} autoComplete="username" /></label><label className="field">비밀번호<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" /></label>{error && <p className="error" role="alert">{error}</p>}<button className="button" disabled={busy}>{busy ? "확인 중…" : "로그인"}</button></form></section></main>;
}
