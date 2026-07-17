"use client";

import { useEffect, useState } from "react";

import { ButtonLink, Card, LoadingState } from "@/components/ui";
import { getAccessToken } from "@/lib/auth";

export function AuthRequired({ children }: Readonly<{ children: React.ReactNode }>) {
  const [hasToken, setHasToken] = useState<boolean | null>(null);

  useEffect(() => {
    setHasToken(Boolean(getAccessToken()));
  }, []);

  if (hasToken === null) {
    return <LoadingState label="確認登入狀態" />;
  }

  if (!hasToken) {
    return (
      <Card>
        <p className="font-serif text-xl font-bold">請先登入後再使用此功能</p>
        <p className="mt-2 text-muted">系統需要確認您的角色與權限，才能開啟義診資料。</p>
        <ButtonLink href="/login" className="mt-4" variant="primary">
          前往登入
        </ButtonLink>
      </Card>
    );
  }

  return children;
}
