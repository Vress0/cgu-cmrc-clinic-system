"use client";

import { CalendarDays, MapPin } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import {
  Alert,
  Button,
  Card,
  EmptyState,
  FormField,
  LoadingState,
  SectionHeader,
  SelectInput,
  StatusTag,
  TextareaInput,
  TextInput,
  Toast
} from "@/components/ui";
import { createClinicSession, listClinicSessions, type ClinicSession } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function SessionsPage() {
  const [sessions, setSessions] = useState<ClinicSession[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  async function loadSessions() {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setLoading(true);
    try {
      setSessions(await listClinicSessions(token));
    } catch {
      setError("無法載入義診場次。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSessions();
  }, []);

  async function handleSubmit(formData: FormData) {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setSubmitting(true);
    try {
      await createClinicSession(token, {
        name: String(formData.get("name") ?? ""),
        session_date: String(formData.get("session_date") ?? ""),
        start_time: String(formData.get("start_time") || "") || null,
        end_time: String(formData.get("end_time") || "") || null,
        location: String(formData.get("location") ?? ""),
        owner: String(formData.get("owner") ?? ""),
        notes: String(formData.get("notes") ?? ""),
        status: String(formData.get("status") ?? "ACTIVE") as ClinicSession["status"]
      });
      await loadSessions();
      setToast("場次已建立");
      window.setTimeout(() => setToast(null), 2400);
    } catch {
      setError("場次建立失敗，請確認必填欄位。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <PageHeader title="義診場次" description="建立與管理每一次義診服務場次，供掛號與診間流程使用。" />
      <AuthRequired>
        <Toast message={toast} />
        {error ? <Alert tone="danger" className="mb-4">{error}</Alert> : null}

        <Card className="mb-6">
          <SectionHeader title="新增場次" description="建議先確認日期、地點與負責人，再開放掛號。" />
          <form action={handleSubmit} className="grid gap-4 md:grid-cols-2">
            <FormField label="場次名稱"><TextInput name="name" required placeholder="例：2026 春季義診" /></FormField>
            <FormField label="日期"><TextInput name="session_date" required type="date" /></FormField>
            <FormField label="開始時間"><TextInput name="start_time" type="time" /></FormField>
            <FormField label="結束時間"><TextInput name="end_time" type="time" /></FormField>
            <FormField label="地點"><TextInput name="location" required placeholder="服務據點或教室" /></FormField>
            <FormField label="負責人"><TextInput name="owner" required placeholder="社團負責人或現場主任" /></FormField>
            <FormField label="狀態">
              <SelectInput name="status" defaultValue="ACTIVE">
                <option value="ACTIVE">進行中</option>
                <option value="DRAFT">草稿</option>
                <option value="ENDED">已結束</option>
              </SelectInput>
            </FormField>
            <FormField label="備註"><TextareaInput name="notes" placeholder="交通、設備、現場注意事項" /></FormField>
            <Button type="submit" className="md:col-span-2" disabled={submitting}>
              {submitting ? "建立中..." : "建立場次"}
            </Button>
          </form>
        </Card>

        <SectionHeader title="場次列表" description={loading ? "資料載入中" : `共 ${sessions.length} 筆場次`} />
        {loading && sessions.length === 0 ? <LoadingState label="載入場次資料" /> : null}
        {!loading || sessions.length > 0 ? (
          <section className="grid gap-4 lg:grid-cols-2">
            {sessions.map((session) => (
              <Card key={session.id} className="relative">
                <div className="absolute right-4 top-4 rounded-md border border-cinnabar bg-cinnabar px-3 py-1 font-serif text-sm font-bold text-white">
                  義診
                </div>
                <div className="pr-20">
                  <h3 className="font-serif text-2xl font-bold">{session.name}</h3>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <StatusTag status={session.status} />
                    <span className="inline-flex items-center gap-1 text-sm font-semibold text-muted">
                      <CalendarDays className="h-4 w-4" />
                      {session.session_date}
                    </span>
                    <span className="inline-flex items-center gap-1 text-sm font-semibold text-muted">
                      <MapPin className="h-4 w-4" />
                      {session.location}
                    </span>
                  </div>
                  <p className="mt-3 text-muted">負責人：{session.owner}</p>
                  {session.notes ? <p className="mt-2 rounded-md bg-paper p-3 text-sm text-muted">{session.notes}</p> : null}
                </div>
              </Card>
            ))}
          </section>
        ) : null}
        {!loading && sessions.length === 0 ? <EmptyState title="尚未建立場次" description="建立場次後，掛號頁就能選擇該場次。" /> : null}
      </AuthRequired>
    </AppShell>
  );
}
