"use client";

import { FileSearch, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import {
  Alert,
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  FormField,
  LoadingState,
  SectionHeader,
  SelectInput,
  TableRow,
  TextInput
} from "@/components/ui";
import { listAuditLogs, type AuditLog } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const actionOptions = [
  "",
  "USER_CREATED",
  "USER_UPDATED",
  "USER_PASSWORD_RESET",
  "CONSENT_CREATED",
  "CONSENT_RESEARCH_WITHDRAWN",
  "PRESCRIPTION_CONFIRMED",
  "PRESCRIPTION_SENT_TO_PHARMACY",
  "DISPENSING_STARTED",
  "DISPENSING_VERIFIED",
  "DISPENSING_HANDED_OUT",
  "INVENTORY_BATCH_CREATED",
  "INVENTORY_ADJUSTED"
];

const entityOptions = ["", "user", "consent", "prescription", "dispensing", "inventory_batch", "inventory_transaction"];

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-TW", {
    dateStyle: "short",
    timeStyle: "medium"
  }).format(new Date(value));
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState("100");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLogs = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setLogs(
        await listAuditLogs(token, {
          action,
          entity_type: entityType,
          q: query,
          limit: Number(limit) || 100
        })
      );
    } catch {
      setError("無法載入稽核紀錄，請確認目前帳號具備 audit_logs:read 權限。");
    } finally {
      setLoading(false);
    }
  }, [action, entityType, limit, query]);

  useEffect(() => {
    void loadLogs();
  }, [loadLogs]);

  return (
    <AppShell>
      <PageHeader
        title="稽核紀錄"
        description="查詢個資同意、帳號管理、處方、藥局與庫存流程的關鍵操作紀錄，用於事後追蹤與安全驗收。"
      />
      <AuthRequired>
        {error ? (
          <Alert tone="danger" className="mb-4">
            {error}
          </Alert>
        ) : null}

        <Card className="mb-6">
          <form
            className="grid gap-4 lg:grid-cols-[1fr_1fr_1.4fr_180px_160px]"
            onSubmit={(event) => {
              event.preventDefault();
              void loadLogs();
            }}
          >
            <FormField label="操作類型">
              <SelectInput value={action} onChange={(event) => setAction(event.target.value)}>
                {actionOptions.map((option) => (
                  <option key={option || "all"} value={option}>
                    {option || "全部操作"}
                  </option>
                ))}
              </SelectInput>
            </FormField>
            <FormField label="資料類型">
              <SelectInput value={entityType} onChange={(event) => setEntityType(event.target.value)}>
                {entityOptions.map((option) => (
                  <option key={option || "all"} value={option}>
                    {option || "全部資料"}
                  </option>
                ))}
              </SelectInput>
            </FormField>
            <FormField label="關鍵字">
              <TextInput value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜尋摘要或操作類型" />
            </FormField>
            <FormField label="筆數">
              <SelectInput value={limit} onChange={(event) => setLimit(event.target.value)}>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200">200</option>
                <option value="500">500</option>
              </SelectInput>
            </FormField>
            <div className="flex items-end gap-2">
              <Button type="submit" disabled={loading} className="w-full">
                <FileSearch className="h-4 w-4" />
                查詢
              </Button>
              <Button type="button" variant="outline" disabled={loading} onClick={() => void loadLogs()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </form>
        </Card>

        <SectionHeader title="查詢結果" description={loading ? "正在讀取稽核紀錄" : `共 ${logs.length} 筆`} />
        {loading ? <LoadingState label="正在載入稽核紀錄" /> : null}
        {!loading && logs.length === 0 ? <EmptyState title="沒有符合條件的稽核紀錄" description="可放寬條件或增加查詢筆數後再試。" /> : null}
        {!loading && logs.length > 0 ? (
          <DataTable>
            <div className="hidden grid-cols-[180px_190px_180px_1fr] gap-3 border-b border-line bg-paper px-4 py-3 font-bold xl:grid">
              <span>時間</span>
              <span>操作</span>
              <span>資料類型</span>
              <span>摘要</span>
            </div>
            {logs.map((log) => (
              <TableRow key={log.id} className="grid gap-3 px-4 py-4 xl:grid-cols-[180px_190px_180px_1fr]">
                <p className="font-bold text-ink">{formatDate(log.created_at)}</p>
                <Badge tone="info">{log.action}</Badge>
                <Badge tone="default">{log.entity_type}</Badge>
                <div>
                  <p className="leading-7 text-ink">{log.summary || "無摘要"}</p>
                  <p className="mt-1 text-xs text-muted">
                    actor {log.actor_user_id ?? "system"} · entity {log.entity_id ?? "-"}
                  </p>
                </div>
              </TableRow>
            ))}
          </DataTable>
        ) : null}
      </AuthRequired>
    </AppShell>
  );
}
