"use client";

import { KeyRound, RefreshCw, Save, ShieldCheck, UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

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
  LoadingState,
  SectionHeader,
  TableRow,
  TextInput,
  Toast
} from "@/components/ui";
import { createUser, listRoles, listUsers, resetUserPassword, updateUser, type ManagedUser, type Role } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

function roleLabel(role: string): string {
  const labels: Record<string, string> = {
    admin: "系統管理",
    registration: "掛號組",
    clinic_student: "診間學生",
    clinician: "醫師/指導老師",
    pharmacy: "藥局組"
  };
  return labels[role] ?? role;
}

export default function UsersPage() {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [roleDrafts, setRoleDrafts] = useState<Record<string, string[]>>({});
  const [activeDrafts, setActiveDrafts] = useState<Record<string, boolean>>({});

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 2400);
  }, []);

  const loadUsers = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [nextRoles, nextUsers] = await Promise.all([listRoles(token), listUsers(token)]);
      setRoles(nextRoles);
      setUsers(nextUsers);
      setRoleDrafts(Object.fromEntries(nextUsers.map((user) => [user.id, user.roles])));
      setActiveDrafts(Object.fromEntries(nextUsers.map((user) => [user.id, user.is_active])));
    } catch {
      setError("無法載入使用者資料，請確認目前帳號具備 users:manage 權限。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  async function handleCreate(formData: FormData) {
    const token = getAccessToken();
    if (!token) return;
    const selectedRoles = roles
      .map((role) => role.name)
      .filter((roleName) => formData.get(`role:${roleName}`) === "on");
    setSubmitting(true);
    setError(null);
    try {
      await createUser(token, {
        username: String(formData.get("username") ?? ""),
        email: String(formData.get("email") ?? ""),
        full_name: String(formData.get("full_name") ?? ""),
        password: String(formData.get("password") ?? ""),
        roles: selectedRoles,
        is_active: true
      });
      await loadUsers();
      showToast("使用者已建立");
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立使用者失敗，請檢查欄位與權限。");
    } finally {
      setSubmitting(false);
    }
  }

  function toggleRole(userId: string, roleName: string, checked: boolean) {
    setRoleDrafts((current) => {
      const next = new Set(current[userId] ?? []);
      if (checked) {
        next.add(roleName);
      } else {
        next.delete(roleName);
      }
      return { ...current, [userId]: Array.from(next) };
    });
  }

  async function handleSave(user: ManagedUser) {
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      await updateUser(token, user.id, {
        roles: roleDrafts[user.id] ?? [],
        is_active: activeDrafts[user.id] ?? user.is_active,
        unlock: true
      });
      await loadUsers();
      showToast("使用者設定已更新");
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新使用者失敗。");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResetPassword(user: ManagedUser) {
    const token = getAccessToken();
    if (!token) return;
    const password = window.prompt(`請輸入 ${user.username} 的新密碼，至少 8 個字元`);
    if (!password) return;
    if (password.length < 8) {
      setError("新密碼至少需要 8 個字元。");
      return;
    }
    if (!window.confirm(`確定要重設 ${user.username} 的密碼？`)) return;
    setSubmitting(true);
    setError(null);
    try {
      await resetUserPassword(token, user.id, password);
      await loadUsers();
      showToast("密碼已重設，帳號鎖定狀態已解除");
    } catch (err) {
      setError(err instanceof Error ? err.message : "重設密碼失敗。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        title="使用者管理"
        description="管理義診現場工作人員帳號、角色、啟用狀態與鎖定解除，所有重要變更會寫入稽核紀錄。"
      />
      <AuthRequired>
        <Toast message={toast} />
        {error ? (
          <Alert tone="danger" className="mb-4">
            {error}
          </Alert>
        ) : null}

        <Card className="mb-6">
          <CardHeader title="新增使用者" description="建立帳號後，請只授予現場工作所需的最小角色。" />
          <form action={handleCreate} className="grid gap-4 lg:grid-cols-4">
            <FormField label="帳號">
              <TextInput name="username" required minLength={3} autoComplete="off" />
            </FormField>
            <FormField label="姓名">
              <TextInput name="full_name" required />
            </FormField>
            <FormField label="Email">
              <TextInput name="email" type="email" required />
            </FormField>
            <FormField label="初始密碼" hint="至少 8 個字元">
              <TextInput name="password" type="password" required minLength={8} autoComplete="new-password" />
            </FormField>
            <div className="lg:col-span-4">
              <p className="mb-2 font-bold text-ink">角色</p>
              <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-5">
                {roles.map((role) => (
                  <label key={role.id} className="flex min-h-12 items-center gap-2 rounded-md border border-line bg-paper/70 px-3 font-bold">
                    <input name={`role:${role.name}`} type="checkbox" className="h-4 w-4" defaultChecked={role.name === "registration"} />
                    {roleLabel(role.name)}
                  </label>
                ))}
              </div>
            </div>
            <Button type="submit" disabled={submitting} className="lg:col-span-4">
              <UserPlus className="h-4 w-4" />
              {submitting ? "建立中" : "建立使用者"}
            </Button>
          </form>
        </Card>

        <SectionHeader
          title="帳號清單"
          description={loading ? "正在載入使用者資料" : `共 ${users.length} 個帳號`}
          action={
            <Button type="button" variant="outline" size="sm" onClick={() => void loadUsers()}>
              <RefreshCw className="h-4 w-4" />
              重新整理
            </Button>
          }
        />

        {loading ? <LoadingState label="正在載入使用者" /> : null}
        {!loading && users.length === 0 ? <EmptyState title="尚未建立使用者" description="請先建立管理員以外的現場工作帳號。" /> : null}
        {!loading && users.length > 0 ? (
          <DataTable>
            <div className="hidden grid-cols-[1.2fr_1fr_2fr_1fr_220px] gap-3 border-b border-line bg-paper px-4 py-3 font-bold xl:grid">
              <span>使用者</span>
              <span>狀態</span>
              <span>角色</span>
              <span>登入狀態</span>
              <span>操作</span>
            </div>
            {users.map((user) => (
              <TableRow key={user.id} className="grid gap-4 px-4 py-4 xl:grid-cols-[1.2fr_1fr_2fr_1fr_220px]">
                <div>
                  <p className="font-bold text-ink">{user.full_name}</p>
                  <p className="text-sm text-muted">{user.username}</p>
                  <p className="text-sm text-muted">{user.email}</p>
                </div>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 font-bold">
                    <input
                      type="checkbox"
                      className="h-4 w-4"
                      checked={activeDrafts[user.id] ?? user.is_active}
                      onChange={(event) => setActiveDrafts((current) => ({ ...current, [user.id]: event.target.checked }))}
                    />
                    啟用
                  </label>
                  <Badge tone={user.is_active ? "success" : "danger"}>{user.is_active ? "目前啟用" : "目前停用"}</Badge>
                </div>
                <div className="grid gap-2 md:grid-cols-2">
                  {roles.map((role) => (
                    <label key={role.id} className="flex items-center gap-2 rounded-md border border-line bg-paper/70 px-3 py-2 text-sm font-bold">
                      <input
                        type="checkbox"
                        className="h-4 w-4"
                        checked={(roleDrafts[user.id] ?? []).includes(role.name)}
                        onChange={(event) => toggleRole(user.id, role.name, event.target.checked)}
                      />
                      {roleLabel(role.name)}
                    </label>
                  ))}
                </div>
                <div className="space-y-2">
                  <Badge tone={user.locked_until ? "danger" : "success"}>{user.locked_until ? "已鎖定" : "未鎖定"}</Badge>
                  <p className="text-sm text-muted">失敗 {user.failed_login_count} 次</p>
                </div>
                <div className="flex flex-col gap-2">
                  <Button type="button" variant="secondary" size="sm" disabled={submitting} onClick={() => void handleSave(user)}>
                    <Save className="h-4 w-4" />
                    儲存設定
                  </Button>
                  <Button type="button" variant="outline" size="sm" disabled={submitting} onClick={() => void handleResetPassword(user)}>
                    <KeyRound className="h-4 w-4" />
                    重設密碼
                  </Button>
                  <Badge tone="info" className="justify-center">
                    <ShieldCheck className="mr-1 h-4 w-4" />
                    稽核保留
                  </Badge>
                </div>
              </TableRow>
            ))}
          </DataTable>
        ) : null}
      </AuthRequired>
    </AppShell>
  );
}
