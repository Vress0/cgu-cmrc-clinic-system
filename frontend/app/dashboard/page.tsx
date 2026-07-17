import { ClipboardList, HeartPulse, Pill, UserRoundCheck } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Badge, Card, CardHeader, StatusTag } from "@/components/ui";
import { getHealth } from "@/lib/api";

const workflowCards = [
  { label: "今日掛號", value: "待串接", icon: ClipboardList, tone: "info" },
  { label: "候診個案", value: "由診間佇列查看", icon: UserRoundCheck, tone: "warning" },
  { label: "看診中", value: "即時工作台", icon: HeartPulse, tone: "success" },
  { label: "待藥局", value: "藥局流程", icon: Pill, tone: "default" }
] as const;

export default async function DashboardPage() {
  let healthText = "無法確認";
  let databaseText = "無法確認";
  let healthStatus = "CANCELLED";

  try {
    const health = await getHealth();
    healthText = health.status === "ok" ? "API 正常" : "API 異常";
    databaseText = health.database === "ok" ? "資料庫正常" : "資料庫連線異常";
    healthStatus = health.status === "ok" && health.database === "ok" ? "COMPLETED" : "CANCELLED";
  } catch {
    healthText = "API 無回應";
  }

  return (
    <AppShell>
      <PageHeader
        title="義診總覽"
        description="快速確認系統狀態與三組流程入口，適合義診現場桌機與平板操作。"
      />

      <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {workflowCards.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.label} className="shan-shui-mark">
              <div className="relative z-10">
                <div className="mb-4 flex items-center justify-between">
                  <Icon aria-hidden="true" className="h-7 w-7 text-brand" />
                  <Badge tone={item.tone}>{item.label}</Badge>
                </div>
                <p className="font-serif text-2xl font-bold">{item.value}</p>
                <p className="mt-2 text-sm leading-6 text-muted">依實際義診流程逐步累積統計。</p>
              </div>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader title="後端服務" description="FastAPI 與 Nginx 代理狀態" action={<StatusTag status={healthStatus} />} />
          <p className="text-3xl font-bold text-brand">{healthText}</p>
        </Card>
        <Card>
          <CardHeader title="資料庫" description="PostgreSQL 連線與 migration 後狀態" action={<StatusTag status={healthStatus} />} />
          <p className="text-3xl font-bold text-brand">{databaseText}</p>
        </Card>
      </section>
    </AppShell>
  );
}
