"use client";

import { useCallback, useEffect, useState } from "react";
import { Pill, Search } from "lucide-react";

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
  TableRow,
  TextareaInput,
  TextInput,
  Toast
} from "@/components/ui";
import {
  activateMedication,
  createMedication,
  deactivateMedication,
  listMedications,
  updateMedication,
  type Medication,
  type MedicationPayload
} from "@/lib/api";
import { getAccessToken, getStoredUser } from "@/lib/auth";

const emptyPayload: MedicationPayload = {
  code: "",
  name: "",
  generic_name: "",
  brand_name: "",
  dosage_form: "",
  strength: "",
  unit: "",
  route: "",
  manufacturer: "",
  notes: "",
  warnings: "",
  is_active: true
};

function payloadFromForm(formData: FormData): MedicationPayload {
  return {
    code: String(formData.get("code") ?? "").trim(),
    name: String(formData.get("name") ?? "").trim(),
    generic_name: String(formData.get("generic_name") ?? "").trim(),
    brand_name: String(formData.get("brand_name") ?? "").trim(),
    dosage_form: String(formData.get("dosage_form") ?? "").trim(),
    strength: String(formData.get("strength") ?? "").trim(),
    unit: String(formData.get("unit") ?? "").trim(),
    route: String(formData.get("route") ?? "").trim(),
    manufacturer: String(formData.get("manufacturer") ?? "").trim(),
    notes: String(formData.get("notes") ?? "").trim(),
    warnings: String(formData.get("warnings") ?? "").trim(),
    is_active: formData.get("is_active") === "on"
  };
}

export default function MedicationsPage() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Medication | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [canManage, setCanManage] = useState(false);

  const loadMedications = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setLoading(true);
    try {
      setMedications(await listMedications(token, query));
    } catch {
      setError("藥品資料載入失敗，請確認登入狀態或稍後再試。");
    } finally {
      setLoading(false);
    }
  }, [query]);

  useEffect(() => {
    void loadMedications();
  }, [loadMedications]);

  useEffect(() => {
    setCanManage(getStoredUser()?.permissions.includes("inventory:manage") ?? false);
  }, []);

  async function saveMedication(formData: FormData) {
    const token = getAccessToken();
    if (!token) return;
    const payload = payloadFromForm(formData);
    if (!payload.code || !payload.name) {
      setError("藥品代碼與藥品名稱為必填。");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const saved = selected
        ? await updateMedication(token, selected.id, payload)
        : await createMedication(token, payload);
      setSelected(saved);
      setToast(selected ? "藥品資料已更新" : "藥品已建立");
      window.setTimeout(() => setToast(null), 2600);
      await loadMedications();
    } catch {
      setError("藥品儲存失敗，請確認代碼沒有重複且欄位格式正確。");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleActive(medication: Medication) {
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = medication.is_active
        ? await deactivateMedication(token, medication.id)
        : await activateMedication(token, medication.id);
      setSelected(updated);
      setToast(updated.is_active ? "藥品已啟用" : "藥品已停用");
      window.setTimeout(() => setToast(null), 2600);
      await loadMedications();
    } catch {
      setError("藥品狀態更新失敗，請稍後再試。");
    } finally {
      setSubmitting(false);
    }
  }

  const formValue = selected ?? emptyPayload;

  return (
    <AppShell>
      <PageHeader title="藥品主檔" description="維護義診可開立藥品、劑型、規格、警示與啟用狀態。" />
      <AuthRequired>
        <Toast message={toast} />
        {error ? (
          <Alert tone="danger" title="藥品主檔錯誤" className="mb-4">
            {error}
          </Alert>
        ) : null}

        <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
          <Card>
            <CardHeader
              title="藥品清單"
              description="停用藥品會保留歷史紀錄，但不能再加入新的用藥單。"
              action={
                <Button type="button" variant="outline" onClick={() => setSelected(null)}>
                  新增藥品
                </Button>
              }
            />
            <form
              className="mb-4 grid gap-3 md:grid-cols-[1fr_140px]"
              onSubmit={(event) => {
                event.preventDefault();
                void loadMedications();
              }}
            >
              <label className="relative block">
                <Search aria-hidden="true" className="absolute left-4 top-3.5 h-5 w-5 text-muted" />
                <TextInput
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="搜尋代碼、藥名、學名或商品名"
                  className="pl-12"
                />
              </label>
              <Button type="submit" disabled={loading}>
                搜尋
              </Button>
            </form>

            <DataTable>
              <TableRow className="hidden grid-cols-[140px_1fr_160px_110px] bg-paper px-4 py-3 text-sm font-bold text-muted md:grid">
                <span>代碼</span>
                <span>藥品</span>
                <span>規格</span>
                <span>狀態</span>
              </TableRow>
              {medications.map((medication) => (
                <button
                  key={medication.id}
                  type="button"
                  onClick={() => setSelected(medication)}
                  className="block w-full text-left transition hover:bg-bamboo/30"
                >
                  <TableRow className="grid gap-2 px-4 py-4 md:grid-cols-[140px_1fr_160px_110px] md:items-center">
                    <span className="font-mono text-sm font-bold text-brand">{medication.code}</span>
                    <span>
                      <span className="block font-bold text-ink">{medication.name}</span>
                      <span className="block text-sm text-muted">
                        {[medication.generic_name, medication.brand_name].filter(Boolean).join(" / ") || "未填學名或商品名"}
                      </span>
                    </span>
                    <span className="text-sm text-muted">
                      {[medication.dosage_form, medication.strength, medication.unit].filter(Boolean).join(" · ") || "-"}
                    </span>
                    <span>
                      <Badge tone={medication.is_active ? "success" : "default"}>
                        {medication.is_active ? "啟用中" : "已停用"}
                      </Badge>
                    </span>
                  </TableRow>
                </button>
              ))}
            </DataTable>
            {!loading && medications.length === 0 ? (
              <EmptyState title="尚無藥品資料" description="建立第一筆藥品後，診間即可加入用藥單。" />
            ) : null}
          </Card>

          <Card>
            <SectionHeader
              title={selected ? "編輯藥品" : "新增藥品"}
              description={canManage ? "請使用清楚代碼與規格，方便診間快速選藥。" : "目前帳號沒有藥品維護權限。"}
            />
            <form key={selected?.id ?? "new"} action={saveMedication} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="藥品代碼">
                  <TextInput name="code" defaultValue={formValue.code} disabled={!canManage || submitting} required />
                </FormField>
                <FormField label="藥品名稱">
                  <TextInput name="name" defaultValue={formValue.name} disabled={!canManage || submitting} required />
                </FormField>
                <FormField label="學名">
                  <TextInput name="generic_name" defaultValue={formValue.generic_name} disabled={!canManage || submitting} />
                </FormField>
                <FormField label="商品名">
                  <TextInput name="brand_name" defaultValue={formValue.brand_name} disabled={!canManage || submitting} />
                </FormField>
                <FormField label="劑型">
                  <TextInput name="dosage_form" defaultValue={formValue.dosage_form} disabled={!canManage || submitting} />
                </FormField>
                <FormField label="規格">
                  <TextInput name="strength" defaultValue={formValue.strength} disabled={!canManage || submitting} />
                </FormField>
                <FormField label="單位">
                  <TextInput name="unit" defaultValue={formValue.unit} disabled={!canManage || submitting} />
                </FormField>
                <FormField label="給藥途徑">
                  <TextInput name="route" defaultValue={formValue.route} disabled={!canManage || submitting} />
                </FormField>
              </div>
              <FormField label="廠商">
                <TextInput name="manufacturer" defaultValue={formValue.manufacturer} disabled={!canManage || submitting} />
              </FormField>
              <FormField label="警示">
                <TextareaInput name="warnings" defaultValue={formValue.warnings} disabled={!canManage || submitting} />
              </FormField>
              <FormField label="備註">
                <TextareaInput name="notes" defaultValue={formValue.notes} disabled={!canManage || submitting} />
              </FormField>
              <label className="flex min-h-12 items-center gap-3 rounded-md border border-line bg-paper px-4 font-bold">
                <input name="is_active" type="checkbox" defaultChecked={formValue.is_active} disabled={!canManage || submitting} />
                啟用於新用藥單
              </label>
              <div className="flex flex-wrap gap-3">
                <Button type="submit" disabled={!canManage || submitting}>
                  <Pill aria-hidden="true" className="h-5 w-5" />
                  {selected ? "儲存藥品" : "建立藥品"}
                </Button>
                {selected ? (
                  <Button
                    type="button"
                    variant={selected.is_active ? "danger" : "secondary"}
                    disabled={!canManage || submitting}
                    onClick={() => void toggleActive(selected)}
                  >
                    {selected.is_active ? "停用藥品" : "重新啟用"}
                  </Button>
                ) : null}
              </div>
            </form>
          </Card>
        </div>
      </AuthRequired>
    </AppShell>
  );
}
