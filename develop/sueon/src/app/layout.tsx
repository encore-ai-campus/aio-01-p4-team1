import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "오케퐁 IT 헬프데스크", description: "사내 IT 문의 지원" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ko"><body>{children}</body></html>;
}
