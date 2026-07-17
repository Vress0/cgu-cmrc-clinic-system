"use client";

import { Search, UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import {
  Alert,
  Button,
  Card,
  DataTable,
  EmptyState,
  FormField,
  LoadingState,
  SectionHeader,
  TableRow,
  TextInput,
  Toast
} from "@/components/ui";
import { createPatient, listPatients, type Patient } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const loadPatients = useCallback(async (nextQuery: string) => {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setLoading(true);
    try {
      setPatients(await listPatients(token, nextQuery));
    } catch {
      setError("無法載入個案資料。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPatients("");
  }, [loadPatients]);

  async function handleSubmit(formData: FormData) {
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    setSubmitting(true);
    try {
      await createPatient(token, {
        case_number: String(formData.get("case_number") ?? ""),
        name: String(formData.get("name") ?? ""),
        sex: String(formData.get("sex") ?? ""),
        birth_date: String(formData.get("birth_date") || "") || null,
        phone: String(formData.get("phone") ?? ""),
        residence_area: String(formData.get("residence_area") ?? ""),
        emergency_contact: String(formData.get("emergency_contact") ?? ""),
        emergency_contact_phone: String(formData.get("emergency_contact_phone") ?? ""),
        primary_language: String(formData.get("primary_language") ?? ""),
        assistance_needs: String(formData.get("assistance_needs") ?? "")
      });
      await loadPatients("");
      setToast("個案已建立");
      window.setTimeout(() => setToast(null), 2400);
    } catch {
      setError("個案建立失敗，請確認必填欄位與病歷號是否重複。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <PageHeader title="個案資料" description="管理義診服務個案基本資料，提供掛號與診間快速查找。" />
      <AuthRequired>
        <Toast message={toast} />
        {error ? <Alert tone="danger" className="mb-4">{error}</Alert> : null}

        <Card className="mb-6">
          <SectionHeader title="搜尋個案" description="可用姓名或病歷號快速搜尋。" />
          <form
            className="flex flex-col gap-3 md:flex-row"
            onSubmit={(event) => {
              event.preventDefault();
              void loadPatients(query);
            }}
          >
            <TextInput value={query} onChange={(event) => setQuery(event.target.value)} placeholder="輸入姓名或病歷號" />
            <Button type="submit" disabled={loading} className="md:w-40">
              <Search className="h-4 w-4" />
              {loading ? "搜尋中" : "搜尋"}
            </Button>
          </form>
        </Card>

        <Card className="mb-6">
          <SectionHeader title="新增個案" description="特殊協助需求會在後續診間流程作為提醒。" />
          <form action={handleSubmit} className="grid gap-4 md:grid-cols-2">
            <FormField label="病歷號"><TextInput name="case_number" required /></FormField>
            <FormField label="姓名"><TextInput name="name" required /></FormField>
            <FormField label="性別"><TextInput name="sex" required placeholder="例：男、女、其他" /></FormField>
            <FormField label="生日"><TextInput name="birth_date" type="date" /></FormField>
            <FormField label="電話"><TextInput name="phone" /></FormField>
            <FormField label="居住區域"><TextInput name="residence_area" /></FormField>
            <FormField label="緊急聯絡人"><TextInput name="emergency_contact" /></FormField>
            <FormField label="緊急聯絡電話"><TextInput name="emergency_contact_phone" /></FormField>
            <FormField label="主要語言"><TextInput name="primary_language" /></FormField>
            <FormField label="特殊協助需求"><TextInput name="assistance_needs" placeholder="例：行動不便、聽力協助、需家屬陪同" /></FormField>
            <Button type="submit" className="md:col-span-2" disabled={submitting}>
              <UserPlus className="h-4 w-4" />
              {submitting ? "建立中..." : "建立個案"}
            </Button>
          </form>
        </Card>

        <SectionHeader title="個案列表" description={loading ? "資料載入中" : `共 ${patients.length} 筆資料`} />
        {loading && patients.length === 0 ? <LoadingState label="載入個案資料" /> : null}
        {(!loading || patients.length > 0) ? <DataTable>
          <div className="hidden grid-cols-[150px_1fr_140px_1fr] gap-3 border-b border-line bg-paper px-4 py-3 font-bold md:grid">
            <span>病歷號</span>
            <span>姓名</span>
            <span>語言</span>
            <span>特殊需求</span>
          </div>
          {patients.map((patient) => (
            <TableRow key={patient.id} className="grid gap-2 px-4 py-4 md:grid-cols-[150px_1fr_140px_1fr]">
              <p className="font-bold">{patient.case_number}</p>
              <p>{patient.name}</p>
              <p>{patient.primary_language || "未填寫"}</p>
              <p className={patient.assistance_needs ? "font-bold text-cinnabar" : "text-muted"}>
                {patient.assistance_needs || "無特殊需求"}
              </p>
            </TableRow>
          ))}
        </DataTable> : null}
        {!loading && patients.length === 0 ? <EmptyState title="尚無個案資料" description="可先建立個案，再前往掛號頁建立本次 Visit。" /> : null}
      </AuthRequired>
    </AppShell>
  );
}
