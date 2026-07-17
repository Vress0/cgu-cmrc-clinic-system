"use client";

import { AlertTriangle, RefreshCcw, Stethoscope } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import {
  Alert,
  Button,
  ButtonLink,
  Card,
  EmptyState,
  SectionHeader,
  StatusTag,
  TabButton,
  Tabs
} from "@/components/ui";
import { cancelClinicVisit, listClinicQueue, startClinicVisit, type ClinicQueueItem } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const statusFilterItems = [
  { value: "ALL", label: "全部" },
  { value: "WAITING_FOR_CLINIC", label: "候診" },
  { value: "IN_CONSULTATION", label: "看診中" },
  { value: "WAITING_FOR_PHARMACY", label: "待藥局" }
] as const;

export default function ClinicPage() {
  const [queue, setQueue] = useState<ClinicQueueItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<ClinicQueueItem["status"] | "ALL">("ALL");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busyVisitId, setBusyVisitId] = useState<string | null>(null);

  async function loadQueue() {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setLoading(true);
    try {
      setQueue(await listClinicQueue(token));
    } catch {
      setError("無法載入看診佇列，請稍後再試。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadQueue();
  }, []);

  const visibleQueue = useMemo(() => {
    if (statusFilter === "ALL") return queue;
    return queue.filter((item) => item.status === statusFilter);
  }, [queue, statusFilter]);

  const counts = useMemo(
    () => ({
      WAITING_FOR_CLINIC: queue.filter((item) => item.status === "WAITING_FOR_CLINIC").length,
      IN_CONSULTATION: queue.filter((item) => item.status === "IN_CONSULTATION").length,
      WAITING_FOR_PHARMACY: queue.filter((item) => item.status === "WAITING_FOR_PHARMACY").length
    }),
    [queue]
  );

  async function runAction(visitId: string, action: (token: string) => Promise<ClinicQueueItem>) {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setBusyVisitId(visitId);
    try {
      await action(token);
      await loadQueue();
    } catch {
      setError("操作未完成，請確認個案狀態後再試一次。");
    } finally {
      setBusyVisitId(null);
    }
  }

  return (
    <AppShell>
      <PageHeader title="診間工作台" description="候診、看診中與待藥局個案集中管理，方便平板與桌機快速操作。" />
      <AuthRequired>
        {error ? (
          <Alert tone="danger" className="mb-4" title="診間佇列錯誤">
            {error}
          </Alert>
        ) : null}

        <section className="mb-5 grid gap-4 md:grid-cols-3">
          <Card>
            <p className="text-sm font-bold text-muted">候診</p>
            <p className="mt-2 text-4xl font-bold text-warning">{counts.WAITING_FOR_CLINIC}</p>
          </Card>
          <Card>
            <p className="text-sm font-bold text-muted">看診中</p>
            <p className="mt-2 text-4xl font-bold text-brand">{counts.IN_CONSULTATION}</p>
          </Card>
          <Card>
            <p className="text-sm font-bold text-muted">待藥局</p>
            <p className="mt-2 text-4xl font-bold text-info">{counts.WAITING_FOR_PHARMACY}</p>
          </Card>
        </section>

        <SectionHeader
          eyebrow="Clinic Queue"
          title="今日看診佇列"
          description="狀態標籤同時使用文字與色彩，避免只靠顏色判讀。"
          action={
            <Button type="button" variant="outline" onClick={loadQueue} disabled={loading}>
              <RefreshCcw aria-hidden="true" className="h-4 w-4" />
              重新整理
            </Button>
          }
        />

        <Tabs className="mb-4">
          {statusFilterItems.map((item) => (
            <TabButton
              key={item.value}
              type="button"
              active={statusFilter === item.value}
              onClick={() => setStatusFilter(item.value)}
            >
              {item.label}
            </TabButton>
          ))}
        </Tabs>

        <div className="space-y-3">
          {visibleQueue.map((item) => (
            <Card key={item.visit_id} className="p-4">
              <div className="grid gap-4 lg:grid-cols-[96px_1fr_180px_260px] lg:items-center">
                <div className="rounded-md border border-line bg-paper p-3 text-center">
                  <p className="text-sm font-bold text-muted">號碼</p>
                  <p className="font-serif text-4xl font-bold">#{item.queue_number}</p>
                </div>
                <div>
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <h3 className="font-serif text-2xl font-bold">{item.patient_name}</h3>
                    <StatusTag status={item.status} />
                  </div>
                  <p className="text-base text-muted">
                    {item.patient_case_number} · {item.patient_sex} · {item.clinic_session_name}
                  </p>
                  <div className="mt-3 grid gap-2 md:grid-cols-2">
                    <p className="rounded-md bg-bamboo/35 px-3 py-2 text-sm font-semibold text-brand-deep">
                      生命徵象：{item.latest_vital_sign_at ? new Date(item.latest_vital_sign_at).toLocaleString() : "尚未記錄"}
                    </p>
                    <p className="rounded-md bg-paper px-3 py-2 text-sm font-semibold text-muted">
                      備註：{item.notes || "無特殊註記"}
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-bold text-muted">場次日期</p>
                  <p className="font-bold">{item.session_date}</p>
                  {item.notes ? (
                    <p className="mt-2 inline-flex items-center gap-1 text-sm font-bold text-cinnabar">
                      <AlertTriangle className="h-4 w-4" />
                      有特殊提醒
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-wrap justify-start gap-2 lg:justify-end">
                  {item.status === "WAITING_FOR_CLINIC" ? (
                    <Button
                      type="button"
                      size="lg"
                      disabled={busyVisitId === item.visit_id}
                      onClick={() => runAction(item.visit_id, (token) => startClinicVisit(token, item.visit_id))}
                    >
                      <Stethoscope aria-hidden="true" className="h-5 w-5" />
                      開始看診
                    </Button>
                  ) : null}
                  {(item.status === "WAITING_FOR_CLINIC" || item.status === "IN_CONSULTATION") ? (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={busyVisitId === item.visit_id}
                      onClick={() => {
                        if (window.confirm("確定要取消此個案看診流程？")) {
                          void runAction(item.visit_id, (token) => cancelClinicVisit(token, item.visit_id));
                        }
                      }}
                    >
                      取消
                    </Button>
                  ) : null}
                  <ButtonLink href={`/clinic/${item.visit_id}`} variant="secondary">
                    詳細紀錄
                  </ButtonLink>
                </div>
              </div>
            </Card>
          ))}

          {visibleQueue.length === 0 ? (
            <EmptyState
              title={loading ? "佇列載入中" : "目前沒有符合條件的個案"}
              description="可先至掛號頁建立 Visit，系統會自動將個案送入候診。"
            />
          ) : null}
        </div>
      </AuthRequired>
    </AppShell>
  );
}
