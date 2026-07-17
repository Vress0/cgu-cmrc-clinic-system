"use client";

import { FileText, Search, UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import {
  Alert,
  Button,
  ButtonLink,
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
      setError("無法載入病人資料，請確認權限或稍後再試。");
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
      setToast("病人資料已建立");
      window.setTimeout(() => setToast(null), 2400);
    } catch {
      setError("建立病人失敗，請檢查病歷號是否重複與必填欄位是否完整。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <PageHeader title="病人資料" description="管理義診病人基本資料、搜尋個案，並進入詳細頁維護健康史與個資同意。" />
      <AuthRequired>
        <Toast message={toast} />
        {error ? (
          <Alert tone="danger" className="mb-4">
            {error}
          </Alert>
        ) : null}

        <Card className="mb-6">
          <SectionHeader title="搜尋病人" description="可依姓名或病歷號查詢。" />
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
          <SectionHeader title="新增病人" description="建立基本資料後，可到病人詳細頁補登健康史與個資同意。" />
          <form action={handleSubmit} className="grid gap-4 md:grid-cols-2">
            <FormField label="病歷號">
              <TextInput name="case_number" required />
            </FormField>
            <FormField label="姓名">
              <TextInput name="name" required />
            </FormField>
            <FormField label="性別">
              <TextInput name="sex" required placeholder="男 / 女 / 其他" />
            </FormField>
            <FormField label="生日">
              <TextInput name="birth_date" type="date" />
            </FormField>
            <FormField label="電話">
              <TextInput name="phone" />
            </FormField>
            <FormField label="居住區域">
              <TextInput name="residence_area" />
            </FormField>
            <FormField label="緊急聯絡人">
              <TextInput name="emergency_contact" />
            </FormField>
            <FormField label="緊急聯絡電話">
              <TextInput name="emergency_contact_phone" />
            </FormField>
            <FormField label="主要語言">
              <TextInput name="primary_language" />
            </FormField>
            <FormField label="特殊協助需求">
              <TextInput name="assistance_needs" placeholder="如行動協助、聽力協助、翻譯需求" />
            </FormField>
            <Button type="submit" className="md:col-span-2" disabled={submitting}>
              <UserPlus className="h-4 w-4" />
              {submitting ? "建立中" : "建立病人"}
            </Button>
          </form>
        </Card>

        <SectionHeader title="病人清單" description={loading ? "正在載入病人資料" : `共 ${patients.length} 筆資料`} />
        {loading && patients.length === 0 ? <LoadingState label="正在載入病人資料" /> : null}
        {(!loading || patients.length > 0) && patients.length > 0 ? (
          <DataTable>
            <div className="hidden grid-cols-[150px_1fr_140px_1fr_150px] gap-3 border-b border-line bg-paper px-4 py-3 font-bold md:grid">
              <span>病歷號</span>
              <span>姓名</span>
              <span>語言</span>
              <span>特殊協助</span>
              <span>操作</span>
            </div>
            {patients.map((patient) => (
              <TableRow key={patient.id} className="grid gap-3 px-4 py-4 md:grid-cols-[150px_1fr_140px_1fr_150px]">
                <p className="font-bold">{patient.case_number}</p>
                <p>{patient.name}</p>
                <p>{patient.primary_language || "未填寫"}</p>
                <p className={patient.assistance_needs ? "font-bold text-cinnabar" : "text-muted"}>
                  {patient.assistance_needs || "無特殊協助"}
                </p>
                <ButtonLink href={`/patients/${patient.id}`} size="sm">
                  <FileText className="h-4 w-4" />
                  查看紀錄
                </ButtonLink>
              </TableRow>
            ))}
          </DataTable>
        ) : null}
        {!loading && patients.length === 0 ? (
          <EmptyState title="尚無病人資料" description="請先建立病人基本資料，再於掛號流程建立 Visit。" />
        ) : null}
      </AuthRequired>
    </AppShell>
  );
}
