"use client";

import { ArrowLeft, FileCheck2, Save, ShieldAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import {
  Alert,
  Badge,
  Button,
  ButtonLink,
  Card,
  CardHeader,
  DataTable,
  EmptyState,
  FormField,
  LoadingState,
  SectionHeader,
  TableRow,
  TextareaInput,
  TextInput,
  Toast
} from "@/components/ui";
import {
  createPatientConsent,
  getHealthHistory,
  getPatient,
  listPatientConsents,
  upsertHealthHistory,
  withdrawResearchConsent,
  type Consent,
  type HealthHistory,
  type Patient
} from "@/lib/api";
import { getAccessToken, getStoredUser } from "@/lib/auth";

const emptyHistory: Omit<HealthHistory, "id" | "patient_id"> = {
  chronic_diseases: "",
  allergies: "",
  current_medications: "",
  surgery_history: "",
  fall_history: "",
  smoking_status: "",
  alcohol_status: "",
  sleep_status: "",
  diet_status: "",
  notes: ""
};

function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("zh-TW", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function consentStatus(consent: Consent): { label: string; tone: "success" | "warning" | "danger" } {
  if (consent.withdrawn_at) return { label: "已撤回", tone: "danger" };
  if (!consent.research_consent || consent.research_withdrawn_at) return { label: "僅服務同意", tone: "warning" };
  return { label: "服務與研究同意", tone: "success" };
}

export default function PatientDetailPage() {
  const params = useParams<{ id: string }>();
  const patientId = params.id;
  const [patient, setPatient] = useState<Patient | null>(null);
  const [history, setHistory] = useState<HealthHistory | null>(null);
  const [historyDraft, setHistoryDraft] = useState(emptyHistory);
  const [consents, setConsents] = useState<Consent[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 2400);
  }, []);

  const loadPatient = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !patientId) return;
    setLoading(true);
    setError(null);
    try {
      const [nextPatient, nextConsents, nextHistory] = await Promise.all([
        getPatient(token, patientId),
        listPatientConsents(token, patientId),
        getHealthHistory(token, patientId).catch(() => null)
      ]);
      setPatient(nextPatient);
      setConsents(nextConsents);
      setHistory(nextHistory);
      setHistoryDraft(nextHistory ?? emptyHistory);
    } catch {
      setError("無法載入病人詳細資料，請確認權限或稍後再試。");
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    void loadPatient();
  }, [loadPatient]);

  async function handleHistorySubmit(formData: FormData) {
    const token = getAccessToken();
    if (!token || !patientId) return;
    setSubmitting(true);
    setError(null);
    try {
      await upsertHealthHistory(token, patientId, {
        chronic_diseases: String(formData.get("chronic_diseases") ?? ""),
        allergies: String(formData.get("allergies") ?? ""),
        current_medications: String(formData.get("current_medications") ?? ""),
        surgery_history: String(formData.get("surgery_history") ?? ""),
        fall_history: String(formData.get("fall_history") ?? ""),
        smoking_status: String(formData.get("smoking_status") ?? ""),
        alcohol_status: String(formData.get("alcohol_status") ?? ""),
        sleep_status: String(formData.get("sleep_status") ?? ""),
        diet_status: String(formData.get("diet_status") ?? ""),
        notes: String(formData.get("notes") ?? "")
      });
      await loadPatient();
      showToast("健康史已更新");
    } catch (err) {
      setError(err instanceof Error ? err.message : "健康史儲存失敗。");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConsentSubmit(formData: FormData) {
    const token = getAccessToken();
    if (!token || !patientId) return;
    setSubmitting(true);
    setError(null);
    try {
      await createPatientConsent(token, patientId, {
        version: "2026-07",
        method: String(formData.get("method") ?? "paper"),
        consented_at: new Date().toISOString(),
        staff_name: String(formData.get("staff_name") || getStoredUser()?.full_name || "現場工作人員"),
        service_consent: formData.get("service_consent") === "on",
        research_consent: formData.get("research_consent") === "on",
        notes: String(formData.get("notes") ?? "")
      });
      await loadPatient();
      showToast("同意紀錄已建立");
    } catch (err) {
      setError(err instanceof Error ? err.message : "同意紀錄建立失敗，服務同意為必填。");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleWithdraw(consent: Consent) {
    const token = getAccessToken();
    if (!token || !patientId) return;
    const notes = window.prompt("請輸入撤回研究同意的原因或備註", "病人要求撤回研究資料使用同意");
    if (notes === null) return;
    if (!window.confirm("確定要撤回此筆研究同意？服務同意不會被撤回。")) return;
    setSubmitting(true);
    setError(null);
    try {
      await withdrawResearchConsent(token, patientId, consent.id, notes);
      await loadPatient();
      showToast("研究同意已撤回");
    } catch (err) {
      setError(err instanceof Error ? err.message : "撤回研究同意失敗。");
    } finally {
      setSubmitting(false);
    }
  }

  const hasAllergy = Boolean(history?.allergies?.trim());
  const hasChronicDisease = Boolean(history?.chronic_diseases?.trim());

  return (
    <AppShell>
      <PageHeader
        title={patient ? `${patient.name} 病人紀錄` : "病人紀錄"}
        description="集中查看個人基本資料、健康史、過敏慢病警示與個資同意狀態。"
        action={
          <ButtonLink href="/patients" variant="outline">
            <ArrowLeft className="h-4 w-4" />
            返回病人列表
          </ButtonLink>
        }
      />
      <AuthRequired>
        <Toast message={toast} />
        {error ? (
          <Alert tone="danger" className="mb-4">
            {error}
          </Alert>
        ) : null}
        {loading ? <LoadingState label="正在載入病人紀錄" /> : null}

        {!loading && patient ? (
          <>
            <section className="mb-6 grid gap-4 lg:grid-cols-[1.2fr_1fr]">
              <Card>
                <CardHeader title="病人摘要" description="義診現場辨識與聯絡資訊" />
                <div className="grid gap-3 md:grid-cols-2">
                  <InfoItem label="病歷號" value={patient.case_number} />
                  <InfoItem label="姓名" value={patient.name} />
                  <InfoItem label="性別" value={patient.sex || "-"} />
                  <InfoItem label="生日" value={patient.birth_date ?? "-"} />
                  <InfoItem label="電話" value={patient.phone || "-"} />
                  <InfoItem label="居住區域" value={patient.residence_area || "-"} />
                  <InfoItem label="主要語言" value={patient.primary_language || "-"} />
                  <InfoItem label="緊急聯絡" value={`${patient.emergency_contact || "-"} ${patient.emergency_contact_phone || ""}`} />
                </div>
              </Card>
              <Card>
                <CardHeader title="重點提醒" description="掛號、診間與藥局需優先注意" />
                <div className="space-y-3">
                  {hasAllergy ? (
                    <Alert tone="danger" title="過敏史">
                      {history?.allergies}
                    </Alert>
                  ) : (
                    <Badge tone="success">未登錄過敏史</Badge>
                  )}
                  {hasChronicDisease ? (
                    <Alert tone="warning" title="慢性病">
                      {history?.chronic_diseases}
                    </Alert>
                  ) : (
                    <Badge tone="default">未登錄慢性病</Badge>
                  )}
                  {patient.assistance_needs ? (
                    <Alert tone="info" title="特殊協助">
                      {patient.assistance_needs}
                    </Alert>
                  ) : (
                    <Badge tone="default">無特殊協助需求</Badge>
                  )}
                </div>
              </Card>
            </section>

            <Card className="mb-6">
              <CardHeader title="健康史" description="供診間評估與藥局核對使用，請維持簡明可讀。" />
              <form action={handleHistorySubmit} className="grid gap-4 md:grid-cols-2">
                <FormField label="慢性病">
                  <TextareaInput name="chronic_diseases" defaultValue={historyDraft.chronic_diseases} />
                </FormField>
                <FormField label="過敏史">
                  <TextareaInput name="allergies" defaultValue={historyDraft.allergies} />
                </FormField>
                <FormField label="目前用藥">
                  <TextareaInput name="current_medications" defaultValue={historyDraft.current_medications} />
                </FormField>
                <FormField label="手術史">
                  <TextareaInput name="surgery_history" defaultValue={historyDraft.surgery_history} />
                </FormField>
                <FormField label="跌倒史">
                  <TextInput name="fall_history" defaultValue={historyDraft.fall_history} />
                </FormField>
                <FormField label="抽菸狀態">
                  <TextInput name="smoking_status" defaultValue={historyDraft.smoking_status} />
                </FormField>
                <FormField label="飲酒狀態">
                  <TextInput name="alcohol_status" defaultValue={historyDraft.alcohol_status} />
                </FormField>
                <FormField label="睡眠狀態">
                  <TextInput name="sleep_status" defaultValue={historyDraft.sleep_status} />
                </FormField>
                <FormField label="飲食狀態">
                  <TextInput name="diet_status" defaultValue={historyDraft.diet_status} />
                </FormField>
                <FormField label="其他備註">
                  <TextareaInput name="notes" defaultValue={historyDraft.notes} />
                </FormField>
                <Button type="submit" disabled={submitting} className="md:col-span-2">
                  <Save className="h-4 w-4" />
                  {submitting ? "儲存中" : "儲存健康史"}
                </Button>
              </form>
            </Card>

            <section className="mb-6 grid gap-4 lg:grid-cols-[1fr_1.1fr]">
              <Card>
                <CardHeader title="新增同意紀錄" description="服務同意為義診紀錄必要條件，研究同意可獨立撤回。" />
                <form action={handleConsentSubmit} className="space-y-4">
                  <FormField label="取得方式">
                    <TextInput name="method" defaultValue="paper" required />
                  </FormField>
                  <FormField label="紀錄人員">
                    <TextInput name="staff_name" defaultValue={getStoredUser()?.full_name ?? ""} required />
                  </FormField>
                  <label className="flex min-h-12 items-center gap-2 rounded-md border border-line bg-paper/70 px-3 font-bold">
                    <input name="service_consent" type="checkbox" className="h-4 w-4" defaultChecked />
                    已取得個資與義診服務同意
                  </label>
                  <label className="flex min-h-12 items-center gap-2 rounded-md border border-line bg-paper/70 px-3 font-bold">
                    <input name="research_consent" type="checkbox" className="h-4 w-4" />
                    同意去識別化研究使用
                  </label>
                  <FormField label="備註">
                    <TextareaInput name="notes" />
                  </FormField>
                  <Button type="submit" disabled={submitting}>
                    <FileCheck2 className="h-4 w-4" />
                    建立同意紀錄
                  </Button>
                </form>
              </Card>

              <div>
                <SectionHeader title="同意紀錄" description={`共 ${consents.length} 筆`} />
                {consents.length === 0 ? (
                  <EmptyState title="尚無同意紀錄" description="請於掛號或病人詳細頁補登服務同意。" />
                ) : (
                  <DataTable>
                    {consents.map((consent) => {
                      const status = consentStatus(consent);
                      return (
                        <TableRow key={consent.id} className="grid gap-3 px-4 py-4">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <p className="font-bold text-ink">版本 {consent.version}</p>
                              <p className="text-sm text-muted">
                                {consent.method} · {formatDate(consent.consented_at)} · {consent.staff_name}
                              </p>
                            </div>
                            <Badge tone={status.tone}>{status.label}</Badge>
                          </div>
                          {consent.notes ? <p className="text-sm leading-6 text-muted">{consent.notes}</p> : null}
                          {consent.research_consent && !consent.research_withdrawn_at ? (
                            <Button type="button" variant="danger" size="sm" disabled={submitting} onClick={() => void handleWithdraw(consent)}>
                              <ShieldAlert className="h-4 w-4" />
                              撤回研究同意
                            </Button>
                          ) : null}
                        </TableRow>
                      );
                    })}
                  </DataTable>
                )}
              </div>
            </section>
          </>
        ) : null}
      </AuthRequired>
    </AppShell>
  );
}

function InfoItem({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div className="rounded-md border border-line bg-paper/70 px-3 py-2">
      <p className="text-sm font-bold text-muted">{label}</p>
      <p className="mt-1 font-bold text-ink">{value}</p>
    </div>
  );
}
