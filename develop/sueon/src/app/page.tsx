"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
export default function Home() { const router = useRouter(); useEffect(() => { router.replace("/login"); }, [router]); return <main className="center"><p>세션을 확인하고 있습니다…</p></main>; }
