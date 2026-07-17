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
  StatusTag,
  TabButton,
  Tabs,
  TextareaInput,
  TextInput,
  Toast
} from "@/components/ui";
import {
  completeConsultation,
  addPrescriptionItem,
  confirmPrescription,
  createVitalSign,
  deletePrescriptionItem,
  getClinicQueueItem,
  getConsultation,
  getPrescription,
  listMedications,
  listVitalSigns,
  sendPrescriptionToPharmacy,
  startClinicVisit,
  updateConsultationClinical,
  updateConsultationIntake,
  type ClinicQueueItem,
  type Consultation,
  type Medication,
  type Prescription,
  type VitalSign
} from "@/lib/api";
import { getAccessToken, getStoredUser } from "@/lib/auth";

type ActiveTab = "summary" | "vitals" | "intake" | "clinical" | "prescription" | "finish";

function text(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "");
}

function optionalNumber(formData: FormData, key: string): number | undefined {
  const value = String(formData.get(key) ?? "").trim();
  return value ? Number(value) : undefined;
}

function optionalText(formData: FormData, key: string): string | undefined {
  const value = String(formData.get(key) ?? "").trim();
  return value || undefined;
}

function prescriptionStatusLabel(status: Prescription["status"]): string {
  const labels: Record<Prescription["status"], string> = {
    DRAFT: "草稿",
    CONFIRMED: "已確認",
    SENT_TO_PHARMACY: "已送藥局",
    DISPENSING: "調劑中",
    WAITING_FOR_VERIFICATION: "待藥局核對",
    VERIFIED: "已核對",
    WAITING_FOR_PICKUP: "待領藥",
    DISPENSED: "已發藥",
    RETURNED_TO_CLINIC: "藥局退回",
    VOIDED: "已作廢"
  };
  return labels[status];
}

function canEditPrescription(status: Prescription["status"]): boolean {
  return status === "DRAFT" || status === "RETURNED_TO_CLINIC";
}

export default function ClinicVisitPage() {
  const params = useParams<{ visitId: string }>();
  const visitId = params.visitId;
  const [queueItem, setQueueItem] = useState<ClinicQueueItem | null>(null);
  const [vitalSigns, setVitalSigns] = useState<VitalSign[]>([]);
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [prescription, setPrescription] = useState<Prescription | null>(null);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [activeTab, setActiveTab] = useState<ActiveTab>("summary");
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [canConfirmPrescription, setCanConfirmPrescription] = useState(false);

  const loadVisit = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setLoading(true);
    try {
      const [queueData, vitalData, consultationData, prescriptionData, medicationData] = await Promise.all([
        getClinicQueueItem(token, visitId),
        listVitalSigns(token, visitId),
        getConsultation(token, visitId),
        getPrescription(token, visitId),
        listMedications(token, "", true)
      ]);
      setQueueItem(queueData);
      setVitalSigns(vitalData);
      setConsultation(consultationData);
      setPrescription(prescriptionData);
      setMedications(medicationData);
    } catch {
      setError("無法載入看診資料，請回到診間工作台後重新進入。");
    } finally {
      setLoading(false);
    }
  }, [visitId]);

  useEffect(() => {
    void loadVisit();
  }, [loadVisit]);

  useEffect(() => {
    setCanConfirmPrescription(getStoredUser()?.permissions.includes("prescriptions:confirm") ?? false);
  }, []);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [dirty]);

  async function runAction(action: (token: string) => Promise<unknown>, successMessage: string) {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setSubmitting(true);
    try {
      await action(token);
      setDirty(false);
      setToast(successMessage);
      window.setTimeout(() => setToast(null), 2600);
      await loadVisit();
    } catch {
      setError("資料未能儲存，請檢查欄位內容或稍後再試。");
    } finally {
      setSubmitting(false);
    }
  }

  async function saveVitalSigns(formData: FormData) {
    await runAction(
      (token) =>
        createVitalSign(token, visitId, {
          systolic_blood_pressure: optionalNumber(formData, "systolic_blood_pressure"),
          diastolic_blood_pressure: optionalNumber(formData, "diastolic_blood_pressure"),
          pulse: optionalNumber(formData, "pulse"),
          temperature: optionalText(formData, "temperature"),
          oxygen_saturation: optionalNumber(formData, "oxygen_saturation"),
          height_cm: optionalText(formData, "height_cm"),
          weight_kg: optionalText(formData, "weight_kg"),
          blood_glucose: optionalText(formData, "blood_glucose"),
          blood_glucose_context: optionalText(formData, "blood_glucose_context") as VitalSign["blood_glucose_context"],
          notes: text(formData, "notes")
        }),
      "生命徵象已儲存"
    );
  }

  async function saveIntake(formData: FormData) {
    await runAction(
      (token) =>
        updateConsultationIntake(token, visitId, {
          chief_complaint: text(formData, "chief_complaint"),
          symptom_description: text(formData, "symptom_description"),
          symptom_location: text(formData, "symptom_location"),
          symptom_onset: text(formData, "symptom_onset"),
          symptom_duration: text(formData, "symptom_duration"),
          symptom_frequency: text(formData, "symptom_frequency"),
          symptom_severity: text(formData, "symptom_severity"),
          worsening: text(formData, "worsening"),
          previously_sought_care: text(formData, "previously_sought_care"),
          previous_treatment: text(formData, "previous_treatment"),
          student_notes: text(formData, "student_notes")
        }),
      "初步問診已儲存"
    );
  }

  async function saveClinical(formData: FormData) {
    await runAction(
      (token) =>
        updateConsultationClinical(token, visitId, {
          clinical_findings: text(formData, "clinical_findings"),
          assessment_summary: text(formData, "assessment_summary"),
          treatment_recommendation: text(formData, "treatment_recommendation"),
          health_education: text(formData, "health_education"),
          referral_recommendation: text(formData, "referral_recommendation"),
          referral_urgency: text(formData, "referral_urgency"),
          follow_up_recommendation: text(formData, "follow_up_recommendation"),
          requires_pharmacy: formData.get("requires_pharmacy") === "on",
          clinician_notes: text(formData, "clinician_notes"),
          inspection: text(formData, "inspection"),
          auscultation_olfaction: text(formData, "auscultation_olfaction"),
          inquiry: text(formData, "inquiry"),
          palpation: text(formData, "palpation"),
          tongue_notes: text(formData, "tongue_notes"),
          pulse_notes: text(formData, "pulse_notes")
        }),
      "臨床評估已儲存"
    );
  }

  async function addMedicationItem(formData: FormData) {
    if (!prescription) return;
    await runAction(
      (token) =>
        addPrescriptionItem(token, prescription.id, {
          medication_id: text(formData, "medication_id"),
          dose: text(formData, "dose"),
          dose_unit: text(formData, "dose_unit"),
          frequency: text(formData, "frequency"),
          route: text(formData, "route"),
          duration_days: optionalNumber(formData, "duration_days"),
          quantity: text(formData, "quantity"),
          instructions: text(formData, "instructions"),
          notes: text(formData, "notes")
        }),
      "用藥品項已加入"
    );
  }

  async function removeMedicationItem(itemId: string) {
    if (!window.confirm("確定要移除此用藥品項？")) return;
    await runAction((token) => deletePrescriptionItem(token, itemId), "用藥品項已移除");
  }

  async function confirmMedicationOrder() {
    if (!prescription) return;
    await runAction((token) => confirmPrescription(token, prescription.id), "用藥單已確認");
  }

  async function sendMedicationOrder() {
    if (!prescription) return;
    if (!window.confirm("確定要送出用藥單至藥局？送出後診間不可直接修改。")) return;
    await runAction((token) => sendPrescriptionToPharmacy(token, prescription.id), "用藥單已送至藥局");
  }

  async function finishConsultation(formData: FormData) {
    const requiresPharmacy = formData.get("requires_pharmacy") === "on";
    const hasConfirmedPrescription =
      prescription?.status === "CONFIRMED" || prescription?.status === "SENT_TO_PHARMACY";
    if (requiresPharmacy && !hasConfirmedPrescription) {
      setError("本次看診勾選需要藥局，請先完成並確認用藥單。");
      setActiveTab("prescription");
      return;
    }
    if (!window.confirm("確定完成本次看診？完成後會依是否需藥局更新流程狀態。")) return;
    await runAction(
      (token) =>
        completeConsultation(token, visitId, {
          requires_pharmacy: requiresPharmacy,
          clinician_notes: optionalText(formData, "clinician_notes")
        }),
      "看診流程已更新"
    );
  }

  return (
    <AppShell>
      <PageHeader title="看診紀錄" description="整理病人摘要、生命徵象、初步問診與臨床評估，支援平板現場操作。" />
      <AuthRequired>
        <Toast message={toast} />
        <div className="mb-4">
          <ButtonLink href="/clinic" variant="ghost">
            返回診間工作台
          </ButtonLink>
        </div>

        {error ? (
          <Alert tone="danger" className="mb-4" title="看診資料錯誤">
            {error}
          </Alert>
        ) : null}

        {queueItem ? (
          <Card className="mb-5">
            <div className="grid gap-4 md:grid-cols-[120px_1fr_220px] md:items-center">
              <div className="rounded-md border border-line bg-paper p-3 text-center">
                <p className="text-sm font-bold text-muted">號碼</p>
                <p className="font-serif text-4xl font-bold">#{queueItem.queue_number}</p>
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-serif text-3xl font-bold">{queueItem.patient_name}</h3>
                  <StatusTag status={queueItem.status} />
                </div>
                <p className="mt-2 text-muted">
                  {queueItem.patient_case_number} · {queueItem.patient_sex} · {queueItem.clinic_session_name}
                </p>
                <p className="mt-3 rounded-md bg-paper px-3 py-2 text-sm font-semibold text-muted">
                  特殊提醒：{queueItem.notes || "目前無掛號備註。若有過敏或特殊需求，請於問診中補記。"}
                </p>
              </div>
              <div className="space-y-2">
                {queueItem.status === "WAITING_FOR_CLINIC" ? (
                  <Button
                    type="button"
                    className="w-full"
                    size="lg"
                    disabled={submitting}
                    onClick={() => runAction((token) => startClinicVisit(token, visitId), "已開始看診")}
                  >
                    開始看診
                  </Button>
                ) : null}
                <p className="text-sm leading-6 text-muted">最後生命徵象：{queueItem.latest_vital_sign_at ? new Date(queueItem.latest_vital_sign_at).toLocaleString() : "尚未記錄"}</p>
              </div>
            </div>
          </Card>
        ) : loading ? (
          <EmptyState title="看診資料載入中" />
        ) : null}

        <Tabs className="mb-5">
          {[
            ["summary", "摘要"],
            ["vitals", "生命徵象"],
            ["intake", "初步問診"],
            ["clinical", "臨床評估"],
            ["prescription", "用藥單"],
            ["finish", "完成看診"]
          ].map(([value, label]) => (
            <TabButton key={value} type="button" active={activeTab === value} onClick={() => setActiveTab(value as ActiveTab)}>
              {label}
            </TabButton>
          ))}
        </Tabs>

        {activeTab === "summary" && queueItem ? (
          <section className="grid gap-4 lg:grid-cols-3">
            <Card>
              <CardHeader title="病人摘要" description="目前由掛號資料與本次 Visit 組成。" />
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-bold text-muted">姓名</dt>
                  <dd className="text-xl font-bold">{queueItem.patient_name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-bold text-muted">病歷號</dt>
                  <dd>{queueItem.patient_case_number}</dd>
                </div>
                <div>
                  <dt className="text-sm font-bold text-muted">性別</dt>
                  <dd>{queueItem.patient_sex}</dd>
                </div>
              </dl>
            </Card>
            <Card>
              <CardHeader title="本次掛號" description="現場流程狀態" />
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-bold text-muted">場次</dt>
                  <dd>{queueItem.clinic_session_name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-bold text-muted">日期</dt>
                  <dd>{queueItem.session_date}</dd>
                </div>
                <div>
                  <dt className="text-sm font-bold text-muted">狀態</dt>
                  <dd>
                    <StatusTag status={queueItem.status} />
                  </dd>
                </div>
              </dl>
            </Card>
            <Card>
              <CardHeader title="風險提醒" description="過敏史與特殊需求請於後續資料欄位補足。" />
              <Alert tone={queueItem.notes ? "warning" : "info"}>{queueItem.notes || "目前沒有掛號備註。"}</Alert>
            </Card>
          </section>
        ) : null}

        {activeTab === "vitals" ? (
          <Card>
            <SectionHeader title="生命徵象" description="身高與體重填入後，系統會由後端自動計算 BMI。" />
            <form action={saveVitalSigns} onChange={() => setDirty(true)} className="grid gap-4 md:grid-cols-4">
              <FormField label="收縮壓"><TextInput name="systolic_blood_pressure" type="number" /></FormField>
              <FormField label="舒張壓"><TextInput name="diastolic_blood_pressure" type="number" /></FormField>
              <FormField label="脈搏"><TextInput name="pulse" type="number" /></FormField>
              <FormField label="體溫"><TextInput name="temperature" type="number" step="0.1" /></FormField>
              <FormField label="血氧"><TextInput name="oxygen_saturation" type="number" /></FormField>
              <FormField label="身高 cm"><TextInput name="height_cm" type="number" step="0.1" /></FormField>
              <FormField label="體重 kg"><TextInput name="weight_kg" type="number" step="0.1" /></FormField>
              <FormField label="血糖"><TextInput name="blood_glucose" type="number" step="0.1" /></FormField>
              <FormField label="血糖時機">
                <SelectInput name="blood_glucose_context">
                  <option value="">未指定</option>
                  <option value="fasting">空腹</option>
                  <option value="before_meal">飯前</option>
                  <option value="after_meal">飯後</option>
                  <option value="random">隨機</option>
                  <option value="unknown">未知</option>
                </SelectInput>
              </FormField>
              <FormField label="備註">
                <TextInput name="notes" className="md:col-span-2" />
              </FormField>
              <div className="flex items-end">
                <Button type="submit" disabled={submitting} className="w-full">
                  儲存生命徵象
                </Button>
              </div>
            </form>
            <div className="mt-5 divide-y divide-line rounded-md border border-line">
              {vitalSigns.map((vital) => (
                <div key={vital.id} className="grid gap-2 p-3 md:grid-cols-5">
                  <p className="font-bold">{new Date(vital.measured_at).toLocaleString()}</p>
                  <p>血壓 {vital.systolic_blood_pressure ?? "-"} / {vital.diastolic_blood_pressure ?? "-"}</p>
                  <p>脈搏 {vital.pulse ?? "-"}</p>
                  <p>BMI {vital.bmi ?? "-"}</p>
                  <p>血糖 {vital.blood_glucose ?? "-"}</p>
                </div>
              ))}
              {vitalSigns.length === 0 ? <p className="p-4 text-muted">尚未記錄生命徵象。</p> : null}
            </div>
          </Card>
        ) : null}

        {activeTab === "intake" && consultation ? (
          <Card>
            <SectionHeader title="初步問診" description="提供學生與工作人員先行整理主訴與症狀脈絡。" />
            <form action={saveIntake} onChange={() => setDirty(true)} className="grid gap-4 md:grid-cols-2">
              <FormField label="主訴"><TextInput name="chief_complaint" defaultValue={consultation.chief_complaint} /></FormField>
              <FormField label="部位"><TextInput name="symptom_location" defaultValue={consultation.symptom_location} /></FormField>
              <FormField label="開始時間"><TextInput name="symptom_onset" defaultValue={consultation.symptom_onset} /></FormField>
              <FormField label="持續時間"><TextInput name="symptom_duration" defaultValue={consultation.symptom_duration} /></FormField>
              <FormField label="頻率"><TextInput name="symptom_frequency" defaultValue={consultation.symptom_frequency} /></FormField>
              <FormField label="嚴重度"><TextInput name="symptom_severity" defaultValue={consultation.symptom_severity} /></FormField>
              <FormField label="症狀描述"><TextareaInput name="symptom_description" defaultValue={consultation.symptom_description} /></FormField>
              <FormField label="加重或緩解因素"><TextareaInput name="worsening" defaultValue={consultation.worsening} /></FormField>
              <FormField label="是否曾就醫"><TextareaInput name="previously_sought_care" defaultValue={consultation.previously_sought_care} /></FormField>
              <FormField label="過去處置"><TextareaInput name="previous_treatment" defaultValue={consultation.previous_treatment} /></FormField>
              <FormField label="學生備註"><TextareaInput name="student_notes" defaultValue={consultation.student_notes} /></FormField>
              <div className="flex items-end">
                <Button type="submit" disabled={submitting} className="w-full">
                  儲存問診
                </Button>
              </div>
            </form>
          </Card>
        ) : null}

        {activeTab === "clinical" && consultation ? (
          <Card>
            <SectionHeader title="臨床評估" description="中醫四診與處置建議集中記錄。" />
            <form action={saveClinical} onChange={() => setDirty(true)} className="grid gap-4 md:grid-cols-2">
              <FormField label="臨床發現"><TextareaInput name="clinical_findings" defaultValue={consultation.clinical_findings} /></FormField>
              <FormField label="評估摘要"><TextareaInput name="assessment_summary" defaultValue={consultation.assessment_summary} /></FormField>
              <FormField label="望診"><TextareaInput name="inspection" defaultValue={consultation.inspection} /></FormField>
              <FormField label="聞診"><TextareaInput name="auscultation_olfaction" defaultValue={consultation.auscultation_olfaction} /></FormField>
              <FormField label="問診補充"><TextareaInput name="inquiry" defaultValue={consultation.inquiry} /></FormField>
              <FormField label="切診"><TextareaInput name="palpation" defaultValue={consultation.palpation} /></FormField>
              <FormField label="舌象"><TextareaInput name="tongue_notes" defaultValue={consultation.tongue_notes} /></FormField>
              <FormField label="脈象"><TextareaInput name="pulse_notes" defaultValue={consultation.pulse_notes} /></FormField>
              <FormField label="處置建議"><TextareaInput name="treatment_recommendation" defaultValue={consultation.treatment_recommendation} /></FormField>
              <FormField label="衛教"><TextareaInput name="health_education" defaultValue={consultation.health_education} /></FormField>
              <FormField label="轉介建議"><TextInput name="referral_recommendation" defaultValue={consultation.referral_recommendation} /></FormField>
              <FormField label="轉介急迫性"><TextInput name="referral_urgency" defaultValue={consultation.referral_urgency} /></FormField>
              <FormField label="追蹤建議"><TextareaInput name="follow_up_recommendation" defaultValue={consultation.follow_up_recommendation} /></FormField>
              <FormField label="醫師備註"><TextareaInput name="clinician_notes" defaultValue={consultation.clinician_notes} /></FormField>
              <label className="flex min-h-12 items-center gap-3 rounded-md border border-line bg-paper px-4 font-bold">
                <input name="requires_pharmacy" type="checkbox" defaultChecked={consultation.requires_pharmacy} />
                需要藥局流程
              </label>
              <Button type="submit" disabled={submitting}>
                儲存臨床評估
              </Button>
            </form>
          </Card>
        ) : null}

        {activeTab === "prescription" && prescription ? (
          <Card>
            <SectionHeader
              title="用藥單"
              description="處方確認後才可送藥局；送出後診間不可直接修改，需由藥局退回。"
              action={
                <div className="flex flex-wrap gap-2">
                  <Badge tone={prescription.status === "SENT_TO_PHARMACY" ? "success" : "info"}>
                    {prescriptionStatusLabel(prescription.status)}
                  </Badge>
                  <Badge>第 {prescription.version} 版</Badge>
                </div>
              }
            />

            {prescription.returned_reason ? (
              <Alert tone="warning" title="藥局退回原因" className="mb-4">
                {prescription.returned_reason}
              </Alert>
            ) : null}

            <div className="mb-5 divide-y divide-line rounded-md border border-line bg-panel">
              {prescription.items.map((item) => (
                <div key={item.id} className="grid gap-3 p-4 lg:grid-cols-[1fr_140px_120px] lg:items-center">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-lg font-bold text-ink">{item.medication.name}</p>
                      <Badge tone={item.medication.is_active ? "success" : "default"}>{item.medication.code}</Badge>
                      {item.medication.warnings ? <Badge tone="danger">警示</Badge> : null}
                    </div>
                    <p className="mt-1 text-sm leading-6 text-muted">
                      {item.dose}
                      {item.dose_unit} · {item.frequency} · {item.route || item.medication.route || "未填途徑"} ·{" "}
                      {item.duration_days ? `${item.duration_days} 天` : "未填天數"}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-muted">
                      {item.instructions || "未填用法說明"}
                      {item.notes ? `；${item.notes}` : ""}
                    </p>
                    {item.medication.warnings ? (
                      <p className="mt-2 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm font-bold text-danger">
                        {item.medication.warnings}
                      </p>
                    ) : null}
                  </div>
                  <div className="font-bold">總量 {item.quantity}</div>
                  {canEditPrescription(prescription.status) ? (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={submitting}
                      onClick={() => void removeMedicationItem(item.id)}
                    >
                      移除
                    </Button>
                  ) : (
                    <span className="text-sm font-bold text-muted">已鎖定</span>
                  )}
                </div>
              ))}
              {prescription.items.length === 0 ? (
                <div className="p-4">
                  <EmptyState title="尚未加入用藥品項" description="至少加入一項藥品後，才能確認並送往藥局。" />
                </div>
              ) : null}
            </div>

            {canEditPrescription(prescription.status) ? (
              <form
                action={addMedicationItem}
                onChange={() => setDirty(true)}
                className="grid gap-4 rounded-md border border-line bg-paper/70 p-4 md:grid-cols-3"
              >
                <FormField label="藥品">
                  <SelectInput name="medication_id" required>
                    <option value="">選擇藥品</option>
                    {medications.map((medication) => (
                      <option key={medication.id} value={medication.id}>
                        {medication.code} {medication.name} {medication.strength}
                      </option>
                    ))}
                  </SelectInput>
                </FormField>
                <FormField label="每次劑量">
                  <TextInput name="dose" placeholder="例：1" required />
                </FormField>
                <FormField label="劑量單位">
                  <TextInput name="dose_unit" placeholder="例：包、錠、克" required />
                </FormField>
                <FormField label="頻次">
                  <TextInput name="frequency" placeholder="例：每日三次" required />
                </FormField>
                <FormField label="途徑">
                  <TextInput name="route" placeholder="例：口服" />
                </FormField>
                <FormField label="天數">
                  <TextInput name="duration_days" type="number" min="1" placeholder="例：3" />
                </FormField>
                <FormField label="總量">
                  <TextInput name="quantity" type="number" step="0.01" min="0.01" placeholder="例：9" required />
                </FormField>
                <FormField label="用法說明">
                  <TextInput name="instructions" placeholder="例：飯後溫水服用" />
                </FormField>
                <FormField label="備註">
                  <TextInput name="notes" />
                </FormField>
                <div className="flex items-end md:col-span-3">
                  <Button type="submit" disabled={submitting || medications.length === 0} className="w-full md:w-auto">
                    加入用藥品項
                  </Button>
                </div>
              </form>
            ) : (
              <Alert tone="info" className="mb-4">
                此用藥單目前已鎖定，需藥局退回後才能修改。
              </Alert>
            )}

            <div className="mt-5 flex flex-wrap gap-3">
              <Button
                type="button"
                variant="secondary"
                disabled={
                  !canConfirmPrescription ||
                  submitting ||
                  !canEditPrescription(prescription.status) ||
                  prescription.items.length === 0
                }
                onClick={() => void confirmMedicationOrder()}
              >
                確認用藥單
              </Button>
              <Button
                type="button"
                variant="danger"
                disabled={!canConfirmPrescription || submitting || prescription.status !== "CONFIRMED" || prescription.items.length === 0}
                onClick={() => void sendMedicationOrder()}
              >
                送至藥局
              </Button>
              {!canConfirmPrescription ? (
                <p className="flex items-center text-sm font-bold text-muted">目前帳號沒有確認處方權限。</p>
              ) : null}
            </div>
          </Card>
        ) : null}

        {activeTab === "finish" && consultation ? (
          <Card className="border-cinnabar/40">
            <SectionHeader title="完成看診" description="完成後，系統會依是否需要藥局更新 Visit 狀態。" />
            <form action={finishConsultation} onChange={() => setDirty(true)} className="grid gap-4 md:grid-cols-[1fr_260px]">
              <FormField label="完成備註"><TextareaInput name="clinician_notes" defaultValue={consultation.clinician_notes} /></FormField>
              <div className="space-y-3">
                <label className="flex min-h-12 items-center gap-3 rounded-md border border-line bg-paper px-4 font-bold">
                  <input name="requires_pharmacy" type="checkbox" defaultChecked={consultation.requires_pharmacy} />
                  完成後轉藥局
                </label>
                <Button type="submit" variant="danger" size="lg" disabled={submitting} className="w-full">
                  完成看診
                </Button>
              </div>
            </form>
          </Card>
        ) : null}
      </AuthRequired>
    </AppShell>
  );
}
