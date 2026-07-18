"use client";

import { Database, RefreshCcw, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Alert, Badge, Button, Modal } from "@/components/ui";
import { getDataMode, getMe, switchDataMode, type DataMode, type DataModeStatus } from "@/lib/api";
import { getAccessToken, getStoredUser, updateStoredUser } from "@/lib/auth";

export function DataModeSwitcher() {
  const [status, setStatus] = useState<DataModeStatus | null>(null);
  const [storedMode, setStoredMode] = useState<DataMode>("LIVE");
  const [targetMode, setTargetMode] = useState<DataMode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadStatus = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setStatus(null);
      return;
    }
    setStatus(await getDataMode(token));
  }, []);

  useEffect(() => {
    const sync = () => {
      setStoredMode(getStoredUser()?.data_mode ?? "LIVE");
      loadStatus().catch(() => undefined);
    };
    sync();
    window.addEventListener("auth:changed", sync);
    return () => window.removeEventListener("auth:changed", sync);
  }, [loadStatus]);

  useEffect(() => {
    const current = status?.mode ?? storedMode;
    document.title = current === "DEMO" ? "[DEMO] 義診健康紀錄系統" : "義診健康紀錄系統";
  }, [status?.mode, storedMode]);

  const currentMode = status?.mode ?? storedMode;
  const isDemo = currentMode === "DEMO";
  const unavailableReason = useMemo(() => {
    if (!status) return "";
    if (!status.enable_demo_mode) return "DEMO 模式未啟用";
    if (!status.can_switch) return "目前帳號沒有切換權限";
    return "";
  }, [status]);

  async function confirmSwitch() {
    if (!targetMode) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      await switchDataMode(token, targetMode);
      const user = await getMe(token);
      updateStoredUser(user);
      window.location.href = targetMode === "DEMO" ? "/dashboard?mode=demo" : "/dashboard?mode=live";
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "資料模式切換失敗");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative z-10 border-t border-line px-6 py-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-bold text-muted">
          <Database aria-hidden="true" className="h-4 w-4" />
          資料模式
        </div>
        <Badge tone={isDemo ? "cinnabar" : "success"}>{isDemo ? "DEMO 假資料" : "LIVE 正式資料"}</Badge>
      </div>

      {isDemo ? (
        <Alert tone="warning" className="mb-3 py-3" title="DEMO 模式">
          目前所有查詢與新增資料都會進入假資料區，不會寫入正式資料。
        </Alert>
      ) : (
        <div className="mb-3 rounded-md border border-line bg-paper/70 px-3 py-2 text-sm leading-6 text-muted">
          正式資料模式，請確認現場資料輸入正確。
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        <Button
          type="button"
          variant={isDemo ? "outline" : "primary"}
          size="sm"
          disabled={loading || currentMode === "LIVE" || !status?.can_access_live}
          onClick={() => setTargetMode("LIVE")}
        >
          <ShieldCheck aria-hidden="true" className="h-4 w-4" />
          LIVE
        </Button>
        <Button
          type="button"
          variant={isDemo ? "danger" : "outline"}
          size="sm"
          disabled={loading || currentMode === "DEMO" || Boolean(unavailableReason) || !status?.can_access_demo}
          onClick={() => setTargetMode("DEMO")}
        >
          <RefreshCcw aria-hidden="true" className="h-4 w-4" />
          DEMO
        </Button>
      </div>

      {unavailableReason ? <p className="mt-2 text-xs font-bold text-muted">{unavailableReason}</p> : null}

      <Modal
        open={targetMode !== null}
        title={targetMode === "DEMO" ? "切換到 DEMO 假資料" : "切換到 LIVE 正式資料"}
        onClose={() => {
          if (!loading) setTargetMode(null);
        }}
      >
        <div className="space-y-4">
          <Alert tone={targetMode === "DEMO" ? "warning" : "danger"}>
            {targetMode === "DEMO"
              ? "切換後會看到教學、演練與展示用資料；正式資料會被隱藏且不會被修改。"
              : "切換後會回到正式資料區，請確認這不是練習或展示操作。"}
          </Alert>
          {error ? <Alert tone="danger">{error}</Alert> : null}
          <div className="flex flex-wrap justify-end gap-2">
            <Button type="button" variant="outline" disabled={loading} onClick={() => setTargetMode(null)}>
              取消
            </Button>
            <Button type="button" variant={targetMode === "DEMO" ? "danger" : "primary"} disabled={loading} onClick={confirmSwitch}>
              {loading ? "切換中..." : "確認切換"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
