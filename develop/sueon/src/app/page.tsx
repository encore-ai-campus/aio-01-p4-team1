"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { me } from "../lib/api/auth";
export default function Home() { const router = useRouter(); useEffect(() => { let active = true; me().then((user) => { if (active) router.replace(user.must_change_password ? "/change-password" : user.role === "admin" ? "/admin/tickets" : "/ask"); }).catch(() => { if (active) router.replace("/login"); }); return () => { active = false; }; }, [router]); return <main className="center"><p>로그인 상태를 확인하고 있습니다…</p></main>; }
