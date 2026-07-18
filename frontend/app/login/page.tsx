"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle, LockKeyhole, ScrollText } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Alert, Button, Card, FormField, TextInput } from "@/components/ui";
import { login } from "@/lib/api";
import { dashboardPathForUser, saveSession } from "@/lib/auth";

const loginSchema = z.object({
  username: z.string().min(1, "請輸入帳號").max(80, "帳號長度過長"),
  password: z.string().min(1, "請輸入密碼").max(255, "密碼長度過長")
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" }
  });

  useEffect(() => {
    if (window.location.search.includes("expired=1")) {
      setNotice("登入已失效，請重新登入。");
    }
  }, []);

  async function onSubmit(values: LoginFormValues) {
    setError(null);
    setNotice(null);
    try {
      const tokenResponse = await login(values.username, values.password);
      saveSession(tokenResponse);
      router.push(dashboardPathForUser(tokenResponse.user));
    } catch {
      setError("登入失敗，請確認帳號與密碼是否正確。");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4 py-8">
      <div className="grid w-full max-w-6xl gap-6 lg:grid-cols-[1fr_460px] lg:items-center">
        <section className="shan-shui-mark hidden min-h-[520px] rounded-md border border-line bg-paper p-10 shadow-soft lg:block">
          <div className="relative z-10 max-w-xl">
            <div className="mb-6 grid h-16 w-16 place-items-center rounded-md bg-cinnabar font-serif text-3xl font-black text-white">
              義
            </div>
            <p className="mb-3 text-sm font-bold tracking-wide text-brand">長庚大學中國醫學研究社</p>
            <h1 className="font-serif text-5xl font-bold leading-tight text-ink">義診健康紀錄與流程管理系統</h1>
            <p className="mt-5 text-xl leading-9 text-muted">
              以掛號、診間、藥局三組流程為核心，讓義診現場的健康紀錄清楚、穩定、可追蹤。
            </p>
            <div className="mt-10 grid gap-3 text-base text-muted">
              <p className="flex items-center gap-2">
                <ScrollText className="h-5 w-5 text-brand" />
                宣紙留白、墨綠主色、長者友善字級
              </p>
              <p className="flex items-center gap-2">
                <LockKeyhole className="h-5 w-5 text-brand" />
                角色權限控管與醫療紀錄保護
              </p>
            </div>
          </div>
        </section>

        <Card className="w-full p-8">
          <div className="mb-7">
            <p className="text-sm font-bold tracking-wide text-cinnabar">系統登入</p>
            <h2 className="mt-2 font-serif text-3xl font-bold">義診工作台</h2>
            <p className="mt-2 leading-7 text-muted">請使用管理員或工作人員帳號登入。</p>
          </div>

          {error ? (
            <Alert tone="danger" className="mb-5" title="無法登入">
              {error}
            </Alert>
          ) : null}
          {notice ? (
            <Alert tone="warning" className="mb-5" title="請重新登入">
              {notice}
            </Alert>
          ) : null}

          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
            <FormField label="帳號" error={errors.username?.message}>
              <TextInput id="username" type="text" autoComplete="username" {...register("username")} />
            </FormField>

            <FormField label="密碼" error={errors.password?.message}>
              <TextInput id="password" type="password" autoComplete="current-password" {...register("password")} />
            </FormField>

            <Button type="submit" disabled={isSubmitting} className="w-full" size="lg">
              {isSubmitting ? "登入中..." : "登入"}
            </Button>
          </form>

          <div className="mt-6 rounded-md border border-line bg-paper/70 p-4 text-sm leading-6 text-muted">
            <div className="mb-1 flex items-center gap-2 font-bold text-ink">
              <AlertTriangle aria-hidden="true" className="h-4 w-4 text-cinnabar" />
              測試帳號
            </div>
            帳號 admin，密碼 ChangeMe123!
          </div>
        </Card>
      </div>
    </main>
  );
}
