"use client";

import { ClipboardCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import { Alert, Button, Card, FormField, SectionHeader, SelectInput, TextareaInput, Toast } from "@/components/ui";
import {
  createVisit,
  listClinicSessions,
  listPatients,
  updateVisitStatus,
  type ClinicSession,
  type Patient,
  type Visit
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function RegistrationPage() {
  const [sessions, setSessions] = useState<ClinicSession[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [createdVisit, setCreatedVisit] = useState<Visit | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function loadOptions() {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    try {
      const [nextSessions, nextPatients] = await Promise.all([listClinicSessions(token), listPatients(token)]);
      setSessions(nextSessions);
      setPatients(nextPatients);
    } catch {
      setError("無法載入場次或個案清單。");
    }
  }

  useEffect(() => {
    void loadOptions();
  }, []);

  async function handleSubmit(formData: FormData) {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setCreatedVisit(null);
    setSubmitting(true);
    try {
      const visit = await createVisit(token, {
        clinic_session_id: String(formData.get("clinic_session_id") ?? ""),
        patient_id: String(formData.get("patient_id") ?? ""),
        registration_staff: String(formData.get("registration_staff") ?? ""),
        notes: String(formData.get("notes") ?? "")
      });
      const queuedVisit = await updateVisitStatus(token, visit.id, "WAITING_FOR_CLINIC");
      setCreatedVisit(queuedVisit);
      setToast(`掛號完成，候診號碼 #${queuedVisit.queue_number}`);
      window.setTimeout(() => setToast(null), 2800);
    } catch {
      setError("掛號失敗，請確認場次、個案與工作人員欄位。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <PageHeader title="掛號作業" description="選擇義診場次與個案後建立 Visit，系統會自動送入診間候診佇列。" />
      <AuthRequired>
        <Toast message={toast} />
        {error ? <Alert tone="danger" className="mb-4">{error}</Alert> : null}
        {createdVisit ? (
          <Alert tone="success" className="mb-4" title="掛號完成">
            候診號碼 #{createdVisit.queue_number}，狀態已送入候診。
          </Alert>
        ) : null}

        <Card>
          <SectionHeader title="建立掛號" description="表單欄位放大，方便現場工作人員快速點選。" />
          <form action={handleSubmit} className="grid gap-4">
            <FormField label="義診場次">
              <SelectInput name="clinic_session_id" required>
                <option value="">請選擇場次</option>
                {sessions.map((session) => (
                  <option key={session.id} value={session.id}>
                    {session.session_date} {session.name}
                  </option>
                ))}
              </SelectInput>
            </FormField>
            <FormField label="個案">
              <SelectInput name="patient_id" required>
                <option value="">請選擇個案</option>
                {patients.map((patient) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.case_number} {patient.name}
                  </option>
                ))}
              </SelectInput>
            </FormField>
            <FormField label="掛號工作人員">
              <SelectInput name="registration_staff" required defaultValue="">
                <option value="">請選擇工作人員</option>
                <option value="registration">掛號組</option>
                <option value="admin">管理員</option>
              </SelectInput>
            </FormField>
            <FormField label="掛號備註" hint="過敏、行動不便、聽力協助等特殊提醒可先填在這裡。">
              <TextareaInput name="notes" placeholder="例：疑似藥物過敏、需輪椅協助、家屬陪同" />
            </FormField>
            <Button type="submit" size="lg" disabled={submitting}>
              <ClipboardCheck className="h-5 w-5" />
              {submitting ? "掛號中..." : "完成掛號並送入候診"}
            </Button>
          </form>
        </Card>
      </AuthRequired>
    </AppShell>
  );
}
