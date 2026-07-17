"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import { Alert, Badge, ButtonLink, Card, CardHeader, DataTable, EmptyState, FormField, SelectInput, TableRow, TextInput } from "@/components/ui";
import { listPharmacyQueue, type PharmacyQueueItem } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const statusFilters = [
  ["", "全部"],
  ["SENT_TO_PHARMACY", "待調劑"],
  ["DISPENSING", "調劑中"],
  ["WAITING_FOR_VERIFICATION", "待核對"],
  ["WAITING_FOR_PICKUP", "待領藥"]
];

function statusLabel(status: string | null): string {
  const labels: Record<string, string> = {
    WAITING_FOR_PHARMACY: "待藥局",
    SENT_TO_PHARMACY: "待調劑",
    DISPENSING: "調劑中",
    WAITING_FOR_VERIFICATION: "待核對",
    VERIFIED: "已核對",
    WAITING_FOR_PICKUP: "待領藥",
    DISPENSED: "已發藥",
    RETURNED_TO_CLINIC: "退回診間",
    RETURNED: "已退回"
  };
  return status ? labels[status] ?? status : "未開始";
}

function statusTone(status: string | null): "default" | "success" | "warning" | "danger" | "info" | "cinnabar" {
  if (!status) return "default";
  if (status === "WAITING_FOR_PICKUP" || status === "DISPENSED") return "success";
  if (status === "RETURNED" || status === "RETURNED_TO_CLINIC") return "danger";
  if (status === "WAITING_FOR_VERIFICATION") return "warning";
  if (status === "DISPENSING") return "info";
  return "default";
}

export default function PharmacyPage() {
  const [queue, setQueue] = useState<PharmacyQueueItem[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setQueue(await listPharmacyQueue(token, query, status));
    } catch {
      setError("藥局工作台載入失敗，請確認登入狀態或稍後重試。");
    } finally {
      setLoading(false);
    }
  }, [query, status]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  const counts = useMemo(
    () => ({
      waiting: queue.filter((item) => item.prescription_status === "SENT_TO_PHARMACY").length,
      dispensing: queue.filter((item) => item.dispensing_status === "IN_PROGRESS").length,
      verification: queue.filter((item) => item.dispensing_status === "WAITING_FOR_VERIFICATION").length,
      pickup: queue.filter((item) => item.dispensing_status === "WAITING_FOR_PICKUP").length
    }),
    [queue]
  );

  return (
    <AppShell>
      <PageHeader title="藥局工作台" description="接收診間送出的用藥單，管理調劑、核對、領藥與退回診間流程。" />
      <AuthRequired>
        {error ? (
          <Alert tone="danger" title="藥局資料錯誤" className="mb-4">
            {error}
          </Alert>
        ) : null}

        <section className="mb-5 grid gap-3 md:grid-cols-4">
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">待調劑</p>
            <p className="font-serif text-3xl font-bold">{counts.waiting}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">調劑中</p>
            <p className="font-serif text-3xl font-bold">{counts.dispensing}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">待核對</p>
            <p className="font-serif text-3xl font-bold">{counts.verification}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">待領藥</p>
            <p className="font-serif text-3xl font-bold">{counts.pickup}</p>
          </Card>
        </section>

        <Card>
          <CardHeader title="藥局佇列" description="依場次與號碼排序，優先處理已送藥局的用藥單。" />
          <form
            className="mb-4 grid gap-3 md:grid-cols-[1fr_180px_140px]"
            onSubmit={(event) => {
              event.preventDefault();
              void loadQueue();
            }}
          >
            <label className="relative block">
              <Search aria-hidden="true" className="absolute left-4 top-3.5 h-5 w-5 text-muted" />
              <TextInput value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋姓名或個案編號" className="pl-12" />
            </label>
            <FormField label="狀態">
              <SelectInput value={status} onChange={(event) => setStatus(event.target.value)}>
                {statusFilters.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </SelectInput>
            </FormField>
            <div className="flex items-end">
              <button className="hidden" type="submit" />
              <ButtonLink href="/pharmacy" className="w-full" onClick={() => void loadQueue()}>
                重新整理
              </ButtonLink>
            </div>
          </form>

          <DataTable>
            <TableRow className="hidden grid-cols-[90px_1fr_150px_130px_120px] bg-paper px-4 py-3 text-sm font-bold text-muted md:grid">
              <span>號碼</span>
              <span>個案</span>
              <span>狀態</span>
              <span>品項</span>
              <span>操作</span>
            </TableRow>
            {queue.map((item) => (
              <TableRow key={item.visit_id} className="grid gap-3 px-4 py-4 md:grid-cols-[90px_1fr_150px_130px_120px] md:items-center">
                <div className="font-serif text-2xl font-bold">#{item.queue_number}</div>
                <div>
                  <p className="text-lg font-bold">{item.patient_name}</p>
                  <p className="text-sm text-muted">
                    {item.patient_case_number} · {item.clinic_session_name} · {item.session_date}
                  </p>
                  {item.notes ? <p className="mt-1 text-sm font-bold text-danger">備註：{item.notes}</p> : null}
                </div>
                <div className="space-y-2">
                  <Badge tone={statusTone(item.dispensing_status ?? item.prescription_status)}>
                    {statusLabel(item.dispensing_status ?? item.prescription_status)}
                  </Badge>
                  <p className="text-sm text-muted">Visit：{statusLabel(item.visit_status)}</p>
                </div>
                <div className="text-sm font-bold">
                  {item.item_count} 項
                  <span className="block text-muted">總量 {item.total_quantity}</span>
                </div>
                <ButtonLink href={`/pharmacy/${item.visit_id}`} variant="primary" className="w-full">
                  處理
                </ButtonLink>
              </TableRow>
            ))}
          </DataTable>
          {!loading && queue.length === 0 ? <EmptyState title="目前沒有藥局待辦" description="診間送出已確認用藥單後，會出現在這裡。" /> : null}
          {loading ? <p className="mt-4 text-sm font-bold text-muted">藥局佇列載入中...</p> : null}
        </Card>
      </AuthRequired>
    </AppShell>
  );
}
