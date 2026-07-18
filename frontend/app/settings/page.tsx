import { Database } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { AuthRequired } from "@/components/auth-required";
import { PageHeader } from "@/components/page-header";
import { ButtonLink, Card, CardHeader } from "@/components/ui";

export default function SettingsPage() {
  return (
    <AppShell>
      <PageHeader title="系統設定" description="管理系統級設定、測試資料與部署後維護項目。" />
      <AuthRequired>
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader title="DEMO 假資料模式" description="建立、重置或刪除 DEMO 資料，供教學、演練與展示使用。" />
            <ButtonLink href="/settings/demo-data" variant="primary">
              <Database aria-hidden="true" className="h-5 w-5" />
              管理 DEMO 資料
            </ButtonLink>
          </Card>
        </div>
      </AuthRequired>
    </AppShell>
  );
}
