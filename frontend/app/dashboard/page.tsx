"use client";

import { Activity, ClipboardList, HeartPulse, PackageCheck, Pill, UsersRound } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import { Alert, Badge, Card, CardHeader, LoadingState, SectionHeader, StatusTag } from "@/components/ui";
import { getDashboardSummary, getHealth, type DashboardSummary } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

type HealthView = {
  api: string;
  database: string;
  status: "COMPLETED" | "CANCELLED";
};

const defaultHealth: HealthView = {
  api: "檢查中",
  database: "檢查中",
  status: "CANCELLED"
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [health, setHealth] = useState<HealthView>(defaultHealth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [nextSummary, healthResponse] = await Promise.all([
        getDashboardSummary(token),
        getHealth().catch(() => null)
      ]);
      setSummary(nextSummary);
      setHealth({
        api: healthResponse?.status === "ok" ? "API 正常" : "API 需檢查",
        database: healthResponse?.database === "ok" ? "資料庫正常" : "資料庫需檢查",
        status: healthResponse?.status === "ok" && healthResponse.database === "ok" ? "COMPLETED" : "CANCELLED"
      });
    } catch {
      setError("無法載入儀表板資料，請稍後再試或確認登入權限。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const workflowCards = useMemo(
    () => [
      {
        label: "掛號完成",
        value: summary?.registered ?? 0,
        icon: ClipboardList,
        status: "REGISTERED",
        description: "已完成基本資料與掛號，等待分流。"
      },
      {
        label: "候診中",
        value: summary?.waiting_for_clinic ?? 0,
        icon: UsersRound,
        status: "WAITING_FOR_CLINIC",
        description: "診間組可從候診佇列開始看診。"
      },
      {
        label: "看診中",
        value: summary?.in_consultation ?? 0,
        icon: HeartPulse,
        status: "IN_CONSULTATION",
        description: "正在進行問診、評估或處方確認。"
      },
      {
        label: "藥局流程",
        value:
          (summary?.waiting_for_pharmacy ?? 0) +
          (summary?.dispensing ?? 0) +
          (summary?.waiting_for_verification ?? 0) +
          (summary?.waiting_for_pickup ?? 0),
        icon: Pill,
        status: "WAITING_FOR_PHARMACY",
        description: "含待調劑、核對與待發藥個案。"
      },
      {
        label: "已完成",
        value: summary?.completed ?? 0,
        icon: PackageCheck,
        status: "COMPLETED",
        description: "本輪流程已結案。"
      }
    ],
    [summary]
  );

  return (
    <AppShell>
      <PageHeader
        title="營運儀表板"
        description="即時掌握掛號、診間、藥局、庫存與系統健康狀態，提供義診現場工作人員快速判斷。"
      />
      <AuthRequired>
        {error ? (
          <Alert tone="danger" className="mb-4">
            {error}
          </Alert>
        ) : null}

        {loading && !summary ? <LoadingState label="正在整理儀表板資料" /> : null}

        {summary ? (
          <>
            <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              {workflowCards.map((item) => {
                const Icon = item.icon;
                return (
                  <Card key={item.label} className="shan-shui-mark">
                    <div className="relative z-10">
                      <div className="mb-4 flex items-start justify-between gap-3">
                        <Icon aria-hidden="true" className="h-7 w-7 text-brand" />
                        <StatusTag status={item.status} />
                      </div>
                      <p className="font-serif text-4xl font-bold text-ink">{item.value}</p>
                      <p className="mt-2 font-bold text-brand-deep">{item.label}</p>
                      <p className="mt-2 text-sm leading-6 text-muted">{item.description}</p>
                    </div>
                  </Card>
                );
              })}
            </section>

            <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card>
                <CardHeader title="活躍場次" description="目前狀態為 ACTIVE 的義診場次" />
                <p className="font-serif text-3xl font-bold text-brand">{summary.active_sessions}</p>
              </Card>
              <Card>
                <CardHeader title="病人總數" description="系統中已建立的病人基本資料" />
                <p className="font-serif text-3xl font-bold text-brand">{summary.patient_count}</p>
              </Card>
              <Card>
                <CardHeader title="藥品品項" description="藥品主檔數量" />
                <p className="font-serif text-3xl font-bold text-brand">{summary.medication_count}</p>
              </Card>
              <Card>
                <CardHeader title="可用庫存" description="扣除保留量後的總可用量" />
                <p className="font-serif text-3xl font-bold text-brand">
                  {Number(summary.inventory_available).toLocaleString("zh-TW")}
                </p>
              </Card>
            </section>

            <section className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader title="系統健康" description="FastAPI、資料庫與反向代理狀態" action={<StatusTag status={health.status} />} />
                <div className="grid gap-3 sm:grid-cols-2">
                  <Badge tone={health.status === "COMPLETED" ? "success" : "danger"}>{health.api}</Badge>
                  <Badge tone={health.status === "COMPLETED" ? "success" : "danger"}>{health.database}</Badge>
                </div>
              </Card>
              <Card>
                <CardHeader title="庫存警示" description="FEFO 發藥前需要優先處理的批次狀態" />
                <div className="grid gap-3 sm:grid-cols-3">
                  <Badge tone={summary.low_stock_count > 0 ? "warning" : "success"}>低庫存 {summary.low_stock_count}</Badge>
                  <Badge tone={summary.expiring_count > 0 ? "warning" : "success"}>即將效期 {summary.expiring_count}</Badge>
                  <Badge tone={summary.expired_count > 0 ? "danger" : "success"}>已過期 {summary.expired_count}</Badge>
                </div>
              </Card>
            </section>
          </>
        ) : null}

        <div className="mt-6">
          <SectionHeader
            title="現場提醒"
            description="若候診、待調劑或庫存警示數字異常，請優先確認對應工作台與稽核紀錄。"
            action={
              <button className="inline-flex min-h-10 items-center gap-2 rounded-md border border-line bg-panel px-3 font-bold text-brand" onClick={() => void loadDashboard()}>
                <Activity className="h-4 w-4" />
                重新整理
              </button>
            }
          />
        </div>
      </AuthRequired>
    </AppShell>
  );
}
