"use client";

import { LogOut, UserRound } from "lucide-react";
import { useEffect, useState } from "react";

import { Button, ButtonLink } from "@/components/ui";
import { logout } from "@/lib/api";
import { clearSession, getRefreshToken, getStoredUser } from "@/lib/auth";
import type { UserProfile } from "@/lib/api";

export function AuthStatus() {
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    const syncUser = () => setUser(getStoredUser());
    syncUser();
    window.addEventListener("auth:changed", syncUser);
    window.addEventListener("storage", syncUser);
    return () => {
      window.removeEventListener("auth:changed", syncUser);
      window.removeEventListener("storage", syncUser);
    };
  }, []);

  async function handleLogout() {
    const refreshToken = getRefreshToken();
    clearSession();
    await logout(refreshToken).catch(() => undefined);
    window.location.href = "/login";
  }

  if (!user) {
    return (
      <div className="border-t border-line px-6 py-5">
        <ButtonLink href="/login" className="w-full" variant="outline">
          登入系統
        </ButtonLink>
      </div>
    );
  }

  return (
    <div className="space-y-3 border-t border-line px-6 py-5">
      <div className="flex items-center gap-3 rounded-md bg-paper/80 p-3">
        <UserRound aria-hidden="true" className="h-5 w-5 text-brand" />
        <div>
          <p className="font-bold">{user.full_name}</p>
          <p className="text-sm text-muted">{user.roles.join(", ") || "尚未指定角色"}</p>
        </div>
      </div>
      <Button type="button" variant="outline" className="w-full" onClick={handleLogout}>
        <LogOut aria-hidden="true" className="h-5 w-5" />
        登出
      </Button>
    </div>
  );
}
