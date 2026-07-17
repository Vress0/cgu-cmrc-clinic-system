"use client";

import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import {
  Alert,
  Badge,
  Button,
  Card,
  CardHeader,
  DataTable,
  EmptyState,
  FormField,
  SectionHeader,
  SelectInput,
  TableRow,
  TextareaInput,
  TextInput,
  Toast
} from "@/components/ui";
import {
  createInventoryAdjustment,
  createInventoryBatch,
  getInventorySummary,
  listInventoryBatches,
  listInventoryTransactions,
  listMedications,
  type InventoryBatch,
  type InventorySummary,
  type InventoryTransaction,
  type InventoryTransactionType,
  type Medication
} from "@/lib/api";
import { getAccessToken, getStoredUser } from "@/lib/auth";

const adjustmentTypes: Array<[InventoryTransactionType, string]> = [
  ["ADJUST_INCREASE", "盤增"],
  ["ADJUST_DECREASE", "盤減"],
  ["EXPIRE", "標記過期"],
  ["DISCARD", "報廢"]
];

function todayPlus(days: number): Date {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date;
}

function batchTone(batch: InventoryBatch): "default" | "success" | "warning" | "danger" | "info" | "cinnabar" {
  const expiry = new Date(batch.expiry_date);
  const today = new Date();
  if (!batch.is_active || expiry < today) return "danger";
  if (expiry <= todayPlus(30)) return "warning";
  if (Number(batch.available_quantity) <= 10) return "warning";
  return "success";
}

function batchLabel(batch: InventoryBatch): string {
  const expiry = new Date(batch.expiry_date);
  const today = new Date();
  if (!batch.is_active) return "停用";
  if (expiry < today) return "已過期";
  if (expiry <= todayPlus(30)) return "近效期";
  if (Number(batch.available_quantity) <= 10) return "低庫存";
  return "正常";
}

export default function InventoryPage() {
  const [batches, setBatches] = useState<InventoryBatch[]>([]);
  const [transactions, setTransactions] = useState<InventoryTransaction[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [summary, setSummary] = useState<InventorySummary | null>(null);
  const [query, setQuery] = useState("");
  const [selectedBatch, setSelectedBatch] = useState<InventoryBatch | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const loadInventory = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [batchData, summaryData, transactionData, medicationData] = await Promise.all([
        listInventoryBatches(token, query),
        getInventorySummary(token),
        listInventoryTransactions(token),
        listMedications(token, "", true)
      ]);
      setBatches(batchData);
      setSummary(summaryData);
      setTransactions(transactionData);
      setMedications(medicationData);
    } catch {
      setError("庫存資料載入失敗，請確認權限或稍後再試。");
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    setCanManage(getStoredUser()?.permissions.includes("inventory:manage") ?? false);
    void loadInventory();
  }, [loadInventory]);

  async function runAction(action: (token: string) => Promise<unknown>, successMessage: string) {
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      await action(token);
      setToast(successMessage);
      window.setTimeout(() => setToast(null), 2600);
      await loadInventory();
    } catch {
      setError("庫存操作失敗，請確認欄位、權限與目前庫存狀態。");
    } finally {
      setSubmitting(false);
    }
  }

  async function createBatch(formData: FormData) {
    await runAction(
      (token) =>
        createInventoryBatch(token, {
          medication_id: String(formData.get("medication_id") ?? ""),
          batch_number: String(formData.get("batch_number") ?? ""),
          expiry_date: String(formData.get("expiry_date") ?? ""),
          quantity: String(formData.get("quantity") ?? ""),
          unit: String(formData.get("unit") ?? ""),
          location: String(formData.get("location") ?? "")
        }),
      "庫存批次已建立"
    );
  }

  async function adjustBatch(formData: FormData) {
    if (!selectedBatch) {
      setError("請先從清單選擇要調整的庫存批次。");
      return;
    }
    await runAction(
      (token) =>
        createInventoryAdjustment(token, {
          batch_id: selectedBatch.id,
          adjustment_type: String(formData.get("adjustment_type") ?? "ADJUST_DECREASE") as InventoryTransactionType,
          quantity: String(formData.get("quantity") ?? ""),
          reason: String(formData.get("reason") ?? "")
        }),
      "庫存調整已完成"
    );
  }

  return (
    <AppShell>
      <PageHeader title="庫存管理" description="管理藥品批次、效期、庫位、庫存調整與不可變庫存異動紀錄。" />
      <AuthRequired>
        <Toast message={toast} />
        {error ? (
          <Alert tone="danger" title="庫存錯誤" className="mb-4">
            {error}
          </Alert>
        ) : null}

        <section className="mb-5 grid gap-3 md:grid-cols-5">
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">批次數</p>
            <p className="font-serif text-3xl font-bold">{summary?.batch_count ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">總庫存</p>
            <p className="font-serif text-3xl font-bold">{summary?.total_on_hand ?? "0.00"}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">已預留</p>
            <p className="font-serif text-3xl font-bold">{summary?.total_reserved ?? "0.00"}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">低庫存</p>
            <p className="font-serif text-3xl font-bold">{summary?.low_stock_count ?? 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm font-bold text-muted">近效期/過期</p>
            <p className="font-serif text-3xl font-bold">
              {summary?.expiring_count ?? 0}/{summary?.expired_count ?? 0}
            </p>
          </Card>
        </section>

        <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
          <Card>
            <CardHeader title="庫存批次" description="批次依效期排序，藥局調劑會採 FEFO 先到期先預留。" />
            <form
              className="mb-4 grid gap-3 md:grid-cols-[1fr_140px]"
              onSubmit={(event) => {
                event.preventDefault();
                void loadInventory();
              }}
            >
              <label className="relative block">
                <Search aria-hidden="true" className="absolute left-4 top-3.5 h-5 w-5 text-muted" />
                <TextInput
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="搜尋藥名、代碼或批號"
                  className="pl-12"
                />
              </label>
              <Button type="submit" disabled={loading}>
                搜尋
              </Button>
            </form>

            <DataTable>
              <TableRow className="hidden grid-cols-[1fr_120px_120px_120px_100px] bg-paper px-4 py-3 text-sm font-bold text-muted md:grid">
                <span>藥品 / 批號</span>
                <span>效期</span>
                <span>可用</span>
                <span>預留</span>
                <span>狀態</span>
              </TableRow>
              {batches.map((batch) => (
                <button key={batch.id} type="button" className="block w-full text-left hover:bg-bamboo/30" onClick={() => setSelectedBatch(batch)}>
                  <TableRow className="grid gap-2 px-4 py-4 md:grid-cols-[1fr_120px_120px_120px_100px] md:items-center">
                    <span>
                      <span className="block font-bold">{batch.medication.name}</span>
                      <span className="block text-sm text-muted">
                        {batch.medication.code} · {batch.batch_number} · {batch.location || "未填庫位"}
                      </span>
                    </span>
                    <span className="font-bold">{batch.expiry_date}</span>
                    <span className="font-bold">
                      {batch.available_quantity} {batch.unit}
                    </span>
                    <span className="text-muted">
                      {batch.reserved_quantity} / {batch.quantity_on_hand}
                    </span>
                    <span>
                      <Badge tone={batchTone(batch)}>{batchLabel(batch)}</Badge>
                    </span>
                  </TableRow>
                </button>
              ))}
            </DataTable>
            {!loading && batches.length === 0 ? <EmptyState title="尚無庫存批次" description="建立批次後，藥局調劑即可依 FEFO 預留庫存。" /> : null}
          </Card>

          <section className="space-y-5">
            <Card>
              <SectionHeader title="新增庫存批次" description={canManage ? "入庫時會同步建立 RECEIVE 庫存異動。" : "目前帳號沒有庫存維護權限。"} />
              <form action={createBatch} className="space-y-4">
                <FormField label="藥品">
                  <SelectInput name="medication_id" disabled={!canManage || submitting} required>
                    <option value="">選擇藥品</option>
                    {medications.map((medication) => (
                      <option key={medication.id} value={medication.id}>
                        {medication.code} {medication.name}
                      </option>
                    ))}
                  </SelectInput>
                </FormField>
                <div className="grid gap-4 md:grid-cols-2">
                  <FormField label="批號">
                    <TextInput name="batch_number" disabled={!canManage || submitting} required />
                  </FormField>
                  <FormField label="效期">
                    <TextInput name="expiry_date" type="date" disabled={!canManage || submitting} required />
                  </FormField>
                  <FormField label="數量">
                    <TextInput name="quantity" type="number" min="0.01" step="0.01" disabled={!canManage || submitting} required />
                  </FormField>
                  <FormField label="單位">
                    <TextInput name="unit" defaultValue="包" disabled={!canManage || submitting} required />
                  </FormField>
                </div>
                <FormField label="庫位">
                  <TextInput name="location" disabled={!canManage || submitting} />
                </FormField>
                <Button type="submit" disabled={!canManage || submitting} className="w-full">
                  建立批次
                </Button>
              </form>
            </Card>

            <Card>
              <SectionHeader
                title="庫存調整"
                description={selectedBatch ? `目前選擇：${selectedBatch.medication.name} / ${selectedBatch.batch_number}` : "請先從左側清單選擇批次。"}
              />
              <form action={adjustBatch} className="space-y-4">
                <FormField label="調整類型">
                  <SelectInput name="adjustment_type" disabled={!canManage || submitting || !selectedBatch}>
                    {adjustmentTypes.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </SelectInput>
                </FormField>
                <FormField label="數量">
                  <TextInput name="quantity" type="number" min="0.01" step="0.01" disabled={!canManage || submitting || !selectedBatch} required />
                </FormField>
                <FormField label="原因">
                  <TextareaInput name="reason" disabled={!canManage || submitting || !selectedBatch} required />
                </FormField>
                <Button type="submit" variant="secondary" disabled={!canManage || submitting || !selectedBatch} className="w-full">
                  送出調整
                </Button>
              </form>
            </Card>

            <Card>
              <CardHeader title="最近庫存異動" />
              <div className="space-y-3">
                {transactions.slice(0, 8).map((transaction) => (
                  <div key={transaction.id} className="rounded-md border border-line bg-paper/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <Badge>{transaction.transaction_type}</Badge>
                      <span className="text-sm text-muted">{new Date(transaction.created_at).toLocaleString()}</span>
                    </div>
                    <p className="mt-2 text-sm font-bold">
                      數量 {transaction.quantity}，庫存 {transaction.quantity_before} → {transaction.quantity_after}
                    </p>
                    <p className="text-sm text-muted">
                      預留 {transaction.reserved_before} → {transaction.reserved_after}
                    </p>
                    {transaction.reason ? <p className="mt-1 text-sm text-muted">{transaction.reason}</p> : null}
                  </div>
                ))}
                {transactions.length === 0 ? <p className="text-sm text-muted">尚無異動紀錄。</p> : null}
              </div>
            </Card>
          </section>
        </div>
      </AuthRequired>
    </AppShell>
  );
}
