"use client";

import { RefreshCcw, Trash2, Wand2 } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import { Alert, Button, Card, CardHeader, LoadingState } from "@/components/ui";
import { deleteDemoData, getDemoDataStatus, resetDemoData, seedDemoData, type DemoDataStatus } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const emptyStatus: DemoDataStatus = {
  enabled: false,
  patient_count: 0,
  session_count: 0,
  visit_count: 0,
  prescription_count: 0,
  inventory_batch_count: 0,
  audit_log_count: 0
};

export default function DemoDataSettingsPage() {
  const [status, setStatus] = useState<DemoDataStatus>(emptyStatus);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadStatus() {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      setStatus(await getDemoDataStatus(token));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "無法讀取 DEMO 資料狀態");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  async function runAction(kind: "seed" | "reset" | "delete") {
    const token = getAccessToken();
    if (!token) return;
    const confirmations: Record<"seed" | "reset" | "delete", string> = {
      seed: "建立 DEMO 假資料？",
      reset: "重置會先刪除全部 DEMO 假資料再重新建立，確認繼續？",
      delete: "請確認刪除全部 DEMO 假資料。LIVE 正式資料不會被刪除。"
    };
    if (!window.confirm(confirmations[kind])) return;
    setAction(kind);
    setMessage("");
    setError("");
    try {
      const nextStatus =
        kind === "seed" ? await seedDemoData(token) : kind === "reset" ? await resetDemoData(token) : await deleteDemoData(token);
      setStatus(nextStatus);
      setMessage(kind === "delete" ? "DEMO 假資料已刪除。" : "DEMO 假資料已更新。");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "DEMO 資料操作失敗");
    } finally {
      setAction("");
    }
  }

  const metrics = [
    ["場次", status.session_count],
    ["病人", status.patient_count],
    ["掛號/看診", status.visit_count],
    ["處方", status.prescription_count],
    ["庫存批次", status.inventory_batch_count],
    ["稽核紀錄", status.audit_log_count]
  ];

  return (
    <AppShell>
      <PageHeader title="DEMO 假資料管理" description="建立、重置或刪除測試演練資料；所有操作只作用於 DEMO 模式。" />
      <AuthRequired>
        <div className="space-y-5">
          <Alert tone="warning" title="資料隔離提醒">
            DEMO 資料和 LIVE 正式資料使用 data_mode 隔離。刪除或重置 DEMO 不會刪除 LIVE 資料。
          </Alert>
          {message ? <Alert tone="success">{message}</Alert> : null}
          {error ? <Alert tone="danger">{error}</Alert> : null}

          <Card>
            <CardHeader title="目前 DEMO 資料量" description="用於快速確認假資料是否已建立。" />
            {loading ? (
              <LoadingState label="讀取中..." />
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {metrics.map(([label, value]) => (
                  <div key={label} className="rounded-md border border-line bg-white/65 p-4">
                    <p className="text-sm font-bold text-muted">{label}</p>
                    <p className="mt-2 font-serif text-3xl font-bold text-ink">{value}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <CardHeader title="操作" description="重置與刪除皆會要求瀏覽器確認；後端只允許管理 DEMO 資料。" />
            <div className="flex flex-wrap gap-3">
              <Button type="button" disabled={Boolean(action)} onClick={() => runAction("seed")}>
                <Wand2 aria-hidden="true" className="h-5 w-5" />
                {action === "seed" ? "建立中..." : "建立 DEMO 假資料"}
              </Button>
              <Button type="button" variant="outline" disabled={Boolean(action)} onClick={() => runAction("reset")}>
                <RefreshCcw aria-hidden="true" className="h-5 w-5" />
                {action === "reset" ? "重置中..." : "重置 DEMO"}
              </Button>
              <Button type="button" variant="danger" disabled={Boolean(action)} onClick={() => runAction("delete")}>
                <Trash2 aria-hidden="true" className="h-5 w-5" />
                {action === "delete" ? "刪除中..." : "刪除 DEMO"}
              </Button>
            </div>
          </Card>
        </div>
      </AuthRequired>
    </AppShell>
  );
}
