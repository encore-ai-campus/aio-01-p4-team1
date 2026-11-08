"use client";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { me } from "../../../lib/api/auth";
import { ApiRequestError } from "../../../lib/api/client";
export default function AdminLayout({ children }: { children: ReactNode }) {
  const router = useRouter(); const [allowed, setAllowed] = useState(false); const [message, setMessage] = useState("관리자 권한을 확인하고 있습니다…");
  useEffect(() => { let active = true; me().then((user) => { if (!active) return; if (user.role !== "admin") { setMessage("관리자 전용 화면입니다."); router.replace("/ask"); } else if (user.must_change_password) router.replace("/change-password"); else setAllowed(true); }).catch((error: unknown) => { if (!active) return; if (error instanceof ApiRequestError && error.status === 401) router.replace("/login"); else setMessage(error instanceof Error ? error.message : "권한을 확인하지 못했습니다."); }); return () => { active = false; }; }, [router]);
  return allowed ? children : <main className="center"><p role="status">{message}</p></main>;
}
