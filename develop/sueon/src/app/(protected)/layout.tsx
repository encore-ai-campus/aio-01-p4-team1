"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { logout, me } from "../../lib/api/auth";
import { ApiRequestError } from "../../lib/api/client";
import type { User } from "../../lib/api/types";

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    me().then((value) => { if (active) setUser(value); }).catch((cause: unknown) => {
      if (!active) return;
      if (cause instanceof ApiRequestError && cause.status === 401) router.replace("/login");
      else setError(cause instanceof Error ? cause.message : "로그인 상태를 확인하지 못했습니다.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [router]);

  useEffect(() => {
    if (!user) return;
    if (user.must_change_password && pathname !== "/change-password") router.replace("/change-password");
    else if (!user.must_change_password && pathname === "/change-password") router.replace(user.role === "admin" ? "/admin/tickets" : "/ask");
    else if (user.role === "admin" && pathname !== "/change-password" && !pathname.startsWith("/admin/")) router.replace("/admin/tickets");
  }, [pathname, router, user]);

  const signOut = useCallback(async () => {
    setError("");
    try { await logout(); router.replace("/login"); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "로그아웃에 실패했습니다."); }
  }, [router]);

  if (loading) return <main className="center"><p>로그인 상태를 확인하고 있습니다…</p></main>;
  if (error && !user) return <main className="center"><section className="card"><p className="error" role="alert">{error}</p><button className="button" onClick={() => location.reload()}>다시 확인</button></section></main>;
  if (!user) return <main className="center"><p>로그인 화면으로 이동하고 있습니다…</p></main>;
  if (user.must_change_password && pathname !== "/change-password") return <main className="center"><p>비밀번호 변경 화면으로 이동하고 있습니다…</p></main>;
  if (!user.must_change_password && pathname === "/change-password") return <main className="center"><p>홈 화면으로 이동하고 있습니다…</p></main>;
  if (pathname === "/change-password") return <>{children}</>;
  if (user.role === "admin" && !pathname.startsWith("/admin/")) return <main className="center"><p>관리자 홈으로 이동하고 있습니다…</p></main>;

  const admin = user.role === "admin";
  if (!admin && pathname === "/ask") return <>{children}</>;
  const home = admin ? "/admin/tickets" : "/ask";
  const links = admin
    ? [["티켓", "/admin/tickets"], ["알림", "/admin/alerts"], ["계정", "/admin/users"]]
    : [["질문하기", "/ask"], ["내 문의", "/my-requests"]];
  return <div className={admin ? "admin-shell" : "employee-shell"}>
    <aside className={admin ? "admin-sidebar" : "employee-sidebar"}>
      <Link className={admin ? "admin-logo" : "employee-logo"} href={home}><img src="/assets/okepong-logo.svg" alt="오케퐁 홈" /></Link>
      <nav aria-label={admin ? "관리자 메뉴" : "직원 메뉴"}>{links.map(([label, href]) => <Link key={href} className={`${admin ? "admin-nav" : "employee-nav"} ${pathname === href ? "active" : ""}`} href={href}>{label}</Link>)}</nav>
    </aside>
    <section className={admin ? "admin-main" : "employee-main"}>
      <header className={admin ? "admin-header" : "employee-header"}><span>{user.name} · {user.dept} · {admin ? "관리자" : "직원"}</span><button type="button" onClick={signOut}>로그아웃</button></header>
      {error && <p className="error shell-error" role="alert">{error}</p>}
      {children}
    </section>
  </div>;
}
