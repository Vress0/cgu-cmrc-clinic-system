import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "長庚中醫社義診健康紀錄系統",
  description: "長庚大學中國醫學研究社義診流程與健康紀錄管理"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
