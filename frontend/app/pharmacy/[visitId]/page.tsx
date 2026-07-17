"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

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
  EmptyState,
  FormField,
  SectionHeader,
  SelectInput,
  TextareaInput,
  TextInput,
  Toast
} from "@/components/ui";
import {
  getPharmacyVisit,
  handOutMedication,
  returnDispensingToClinic,
  startDispensing,
  submitDispensingForVerification,
  updateDispensingItems,
  verifyDispensing,
  type DispensingRecord,
  type PharmacyVisitDetail,
  type ReturnReason
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const returnReasons: Array<[ReturnReason, string]> = [
  ["OUT_OF_STOCK", "缺藥"],
  ["UNCLEAR_DOSAGE", "劑量不清"],
  ["UNCLEAR_INSTRUCTIONS", "用法不清"],
  ["INCORRECT_QUANTITY", "數量疑義"],
  ["ALLERGY_RISK", "過敏風險"],
  ["DUPLICATE_MEDICATION", "疑似重複用藥"],
  ["OTHER", "其他"]
];

function statusLabel(status: string | null | undefined): string {
  const labels: Record<string, string> = {
    SENT_TO_PHARMACY: "待調劑",
    DISPENSING: "調劑中",
    IN_PROGRESS: "調劑中",
    WAITING_FOR_VERIFICATION: "待核對",
    VERIFIED: "已核對",
    WAITING_FOR_PICKUP: "待領藥",
    DISPENSED: "已發藥",
    RETURNED_TO_CLINIC: "退回診間",
    RETURNED: "已退回",
    COMPLETED: "已完成"
  };
  return status ? labels[status] ?? status : "未開始";
}

function idempotencyKey(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `handout-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function PharmacyVisitPage() {
  const params = useParams<{ visitId: string }>();
  const visitId = params.visitId;
  const [detail, setDetail] = useState<PharmacyVisitDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadDetail = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setDetail(await getPharmacyVisit(token, visitId));
    } catch {
      setError("藥局個案資料載入失敗，請回工作台重新進入。");
    } finally {
      setLoading(false);
    }
  }, [visitId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  async function runAction(action: (token: string) => Promise<unknown>, successMessage: string) {
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      await action(token);
      setToast(successMessage);
      window.setTimeout(() => setToast(null), 2600);
      await loadDetail();
    } catch {
      setError("藥局流程更新失敗，請確認目前狀態與權限後再試。");
    } finally {
      setSubmitting(false);
    }
  }

  async function start() {
    await runAction((token) => startDispensing(token, visitId), "已開始調劑");
  }

  async function saveItems(formData: FormData) {
    const dispensing = detail?.dispensing;
    if (!dispensing) return;
    await runAction(
      (token) =>
        updateDispensingItems(token, dispensing.id, {
          items: dispensing.items.map((item) => ({
            id: item.id,
            dispensed_quantity: String(formData.get(`quantity_${item.id}`) ?? ""),
            notes: String(formData.get(`notes_${item.id}`) ?? "")
          })),
          notes: String(formData.get("notes") ?? "")
        }),
      "調劑內容已儲存"
    );
  }

  async function submitForVerification() {
    const dispensing = detail?.dispensing;
    if (!dispensing) return;
    await runAction((token) => submitDispensingForVerification(token, dispensing.id), "已送交核對");
  }

  async function verify(formData: FormData) {
    const dispensing = detail?.dispensing;
    if (!dispensing) return;
    await runAction(
      (token) =>
        verifyDispensing(token, dispensing.id, {
          allow_self_verification: formData.get("allow_self_verification") === "on",
          exception_reason: String(formData.get("exception_reason") ?? "")
        }),
      "核對完成，已進入待領藥"
    );
  }

  async function handOut(formData: FormData) {
    const dispensing = detail?.dispensing;
    if (!dispensing) return;
    if (!window.confirm("確定完成發藥？完成後本次 visit 會進入 COMPLETED。")) return;
    await runAction(
      (token) =>
        handOutMedication(token, dispensing.id, {
          patient_counseling: String(formData.get("patient_counseling") ?? ""),
          notes: String(formData.get("notes") ?? ""),
          idempotency_key: String(formData.get("idempotency_key") ?? idempotencyKey())
        }),
      "發藥完成"
    );
  }

  async function returnToClinic(formData: FormData) {
    const dispensing = detail?.dispensing;
    if (!dispensing) return;
    if (!window.confirm("確定退回診間？診間將重新開放修改用藥單。")) return;
    await runAction(
      (token) =>
        returnDispensingToClinic(token, dispensing.id, {
          reason: String(formData.get("reason") ?? "OTHER") as ReturnReason,
          details: String(formData.get("details") ?? "")
        }),
      "已退回診間"
    );
  }

  const dispensing: DispensingRecord | null = detail?.dispensing ?? null;
  const canEditItems = dispensing?.status === "IN_PROGRESS";
  const canSubmit = dispensing?.status === "IN_PROGRESS";
  const canVerify = dispensing?.status === "WAITING_FOR_VERIFICATION";
  const canHandOut = dispensing?.status === "WAITING_FOR_PICKUP";
  const canReturn = dispensing ? ["IN_PROGRESS", "WAITING_FOR_VERIFICATION", "WAITING_FOR_PICKUP"].includes(dispensing.status) : false;

  return (
    <AppShell>
      <PageHeader title="藥局調劑紀錄" description="核對個案與用藥單，完成調劑、複核、衛教與發藥。" />
      <AuthRequired>
        <Toast message={toast} />
        <div className="mb-4">
          <ButtonLink href="/pharmacy" variant="ghost">
            返回藥局工作台
          </ButtonLink>
        </div>

        {error ? (
          <Alert tone="danger" title="藥局流程錯誤" className="mb-4">
            {error}
          </Alert>
        ) : null}

        {detail ? (
          <>
            <Card className="mb-5">
              <div className="grid gap-4 md:grid-cols-[120px_1fr_220px] md:items-center">
                <div className="rounded-md border border-line bg-paper p-3 text-center">
                  <p className="text-sm font-bold text-muted">號碼</p>
                  <p className="font-serif text-4xl font-bold">#{detail.queue_item.queue_number}</p>
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-serif text-3xl font-bold">{detail.queue_item.patient_name}</h3>
                    <Badge tone="info">{statusLabel(detail.queue_item.prescription_status)}</Badge>
                    <Badge>{statusLabel(detail.queue_item.dispensing_status)}</Badge>
                  </div>
                  <p className="mt-2 text-muted">
                    {detail.queue_item.patient_case_number} · {detail.queue_item.patient_sex} · {detail.queue_item.clinic_session_name}
                  </p>
                  {detail.queue_item.notes ? (
                    <Alert tone="warning" className="mt-3">
                      {detail.queue_item.notes}
                    </Alert>
                  ) : null}
                </div>
                <div>
                  {!dispensing && detail.prescription.status === "SENT_TO_PHARMACY" ? (
                    <Button type="button" size="lg" className="w-full" disabled={submitting} onClick={() => void start()}>
                      開始調劑
                    </Button>
                  ) : (
                    <p className="rounded-md border border-line bg-paper px-3 py-2 text-sm font-bold text-muted">
                      調劑狀態：{statusLabel(dispensing?.status)}
                    </p>
                  )}
                </div>
              </div>
            </Card>

            <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
              <section className="space-y-5">
                <Card>
                  <CardHeader title="處方內容" description="請逐項核對藥名、劑量、頻次、天數與警示。" />
                  <div className="divide-y divide-line rounded-md border border-line">
                    {detail.prescription.items.map((item) => (
                      <div key={item.id} className="p-4">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-lg font-bold">{item.medication.name}</p>
                          <Badge>{item.medication.code}</Badge>
                          {item.medication.warnings ? <Badge tone="danger">警示</Badge> : null}
                        </div>
                        <p className="mt-1 text-sm leading-6 text-muted">
                          {item.dose}
                          {item.dose_unit} · {item.frequency} · {item.route || item.medication.route || "未填途徑"} ·{" "}
                          {item.duration_days ? `${item.duration_days} 天` : "未填天數"} · 總量 {item.quantity}
                        </p>
                        {item.instructions ? <p className="mt-1 text-sm font-bold text-ink">{item.instructions}</p> : null}
                        {item.medication.warnings ? (
                          <p className="mt-2 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm font-bold text-danger">
                            {item.medication.warnings}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </Card>

                <Card>
                  <SectionHeader title="調劑內容" description="調劑數量不可超過處方數量；送核對前每一項都必須填入實際調劑量。" />
                  {dispensing ? (
                    <form action={saveItems} className="space-y-4">
                      <div className="divide-y divide-line rounded-md border border-line bg-panel">
                        {dispensing.items.map((item) => (
                          <div key={item.id} className="grid gap-3 p-4 md:grid-cols-[1fr_160px_1fr] md:items-end">
                            <div>
                              <p className="font-bold">{item.medication.name}</p>
                              <p className="text-sm text-muted">
                                處方量 {item.prescribed_quantity} {item.unit}
                              </p>
                              {item.inventory_batch ? (
                                <p className="mt-1 text-sm font-bold text-brand">
                                  批號 {item.inventory_batch.batch_number} · 效期 {item.inventory_batch.expiry_date} ·{" "}
                                  {item.inventory_batch.location || "未填庫位"}
                                </p>
                              ) : (
                                <p className="mt-1 text-sm font-bold text-danger">尚未分配庫存批次</p>
                              )}
                            </div>
                            <FormField label="實際調劑量">
                              <TextInput
                                name={`quantity_${item.id}`}
                                type="number"
                                min="0.01"
                                max={item.prescribed_quantity}
                                step="0.01"
                                defaultValue={Number(item.dispensed_quantity) > 0 ? item.dispensed_quantity : item.prescribed_quantity}
                                disabled={!canEditItems || submitting}
                              />
                            </FormField>
                            <FormField label="調劑備註">
                              <TextInput name={`notes_${item.id}`} defaultValue={item.notes} disabled={!canEditItems || submitting} />
                            </FormField>
                          </div>
                        ))}
                      </div>
                      <FormField label="調劑總備註">
                        <TextareaInput name="notes" defaultValue={dispensing.notes} disabled={!canEditItems || submitting} />
                      </FormField>
                      <div className="flex flex-wrap gap-3">
                        <Button type="submit" disabled={!canEditItems || submitting}>
                          儲存調劑內容
                        </Button>
                        <Button type="button" variant="secondary" disabled={!canSubmit || submitting} onClick={() => void submitForVerification()}>
                          送交核對
                        </Button>
                      </div>
                    </form>
                  ) : (
                    <EmptyState title="尚未開始調劑" description="按下開始調劑後，系統會依用藥單建立調劑品項。" />
                  )}
                </Card>
              </section>

              <aside className="space-y-5">
                <Card>
                  <SectionHeader title="核對" description="原則上不可由同一位藥師自我核對；admin 可登錄例外原因。" />
                  <form action={verify} className="space-y-3">
                    <label className="flex min-h-12 items-center gap-3 rounded-md border border-line bg-paper px-4 font-bold">
                      <input name="allow_self_verification" type="checkbox" disabled={!canVerify || submitting} />
                      admin 自我核對例外
                    </label>
                    <FormField label="例外原因">
                      <TextareaInput name="exception_reason" disabled={!canVerify || submitting} />
                    </FormField>
                    <Button type="submit" disabled={!canVerify || submitting} className="w-full">
                      完成核對並待領藥
                    </Button>
                  </form>
                </Card>

                <Card>
                  <SectionHeader title="發藥" description="完成衛教與發藥後，本次 visit 會結案。" />
                  <form action={handOut} className="space-y-3">
                    <input type="hidden" name="idempotency_key" value={idempotencyKey()} readOnly />
                    <FormField label="用藥衛教">
                      <TextareaInput name="patient_counseling" disabled={!canHandOut || submitting} required />
                    </FormField>
                    <FormField label="發藥備註">
                      <TextareaInput name="notes" disabled={!canHandOut || submitting} />
                    </FormField>
                    <Button type="submit" variant="danger" disabled={!canHandOut || submitting} className="w-full">
                      完成發藥
                    </Button>
                  </form>
                </Card>

                <Card className="border-cinnabar/40">
                  <SectionHeader title="退回診間" description="用藥疑義、過敏風險或缺藥時，退回診間重新處理。" />
                  <form action={returnToClinic} className="space-y-3">
                    <FormField label="退回原因">
                      <SelectInput name="reason" disabled={!canReturn || submitting}>
                        {returnReasons.map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </SelectInput>
                    </FormField>
                    <FormField label="退回說明">
                      <TextareaInput name="details" disabled={!canReturn || submitting} required />
                    </FormField>
                    <Button type="submit" variant="outline" disabled={!canReturn || submitting} className="w-full">
                      退回診間
                    </Button>
                  </form>
                </Card>
              </aside>
            </div>
          </>
        ) : loading ? (
          <EmptyState title="藥局資料載入中" />
        ) : null}
      </AuthRequired>
    </AppShell>
  );
}
