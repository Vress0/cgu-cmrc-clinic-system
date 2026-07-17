import Link from "next/link";
import { Activity, CalendarDays, ClipboardList, Home, Pill, Settings, Users } from "lucide-react";

import { AuthStatus } from "@/components/auth-status";

const navItems = [
  { href: "/dashboard", label: "總覽", icon: Home },
  { href: "/sessions", label: "場次", icon: CalendarDays },
  { href: "/registration", label: "掛號", icon: ClipboardList },
  { href: "/patients", label: "個案", icon: Users },
  { href: "/clinic", label: "診間", icon: Activity },
  { href: "/medications", label: "藥品", icon: Pill },
  { href: "/pharmacy", label: "藥局", icon: Pill },
  { href: "/settings", label: "設定", icon: Settings }
];

export function AppShell({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[292px_1fr]">
      <aside className="shan-shui-mark border-b border-line bg-panel/95 shadow-soft lg:min-h-screen lg:border-b-0 lg:border-r">
        <div className="relative z-10 px-6 py-6">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-md bg-cinnabar font-serif text-xl font-black text-white shadow-soft">
              義
            </div>
            <div>
              <p className="text-sm font-bold tracking-wide text-brand">CGU CMRC</p>
              <h1 className="font-serif text-xl font-bold leading-tight text-ink">義診健康紀錄系統</h1>
            </div>
          </div>
          <p className="rounded-md border border-line bg-paper/70 px-3 py-2 text-sm leading-6 text-muted">
            掛號、診間、藥局流程整合管理
          </p>
        </div>
        <nav className="relative z-10 flex gap-2 overflow-x-auto px-3 pb-4 lg:block lg:space-y-1 lg:overflow-visible">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex min-h-12 shrink-0 items-center gap-3 rounded-md px-4 py-3 text-base font-bold text-ink transition hover:bg-bamboo/50 hover:text-brand-deep"
              >
                <Icon aria-hidden="true" className="h-5 w-5 text-brand" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="relative z-10">
          <AuthStatus />
        </div>
      </aside>
      <main className="px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">{children}</div>
      </main>
    </div>
  );
}
