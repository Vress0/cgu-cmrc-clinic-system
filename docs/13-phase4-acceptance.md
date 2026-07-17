# Phase 4 驗收清單

## 後端

- `pytest` 通過。
- Alembic migration 可升級到最新版本。
- `/api/v1/dashboard/summary` 可回傳流程與庫存統計。
- `/api/v1/users` 可建立、更新、停用、解鎖使用者。
- `/api/v1/users/{id}/reset-password` 可重設密碼並寫入稽核。
- `/api/v1/audit-logs` 可依 action、entity type、關鍵字與 limit 查詢。
- 同意紀錄可新增，研究同意可撤回。

## 前端

- `npm run lint` 通過。
- `npm run typecheck` 通過。
- `npm run build` 通過。
- `/dashboard` 顯示即時摘要與系統健康。
- `/patients/[id]` 顯示健康史、過敏、慢病、特殊協助與同意紀錄。
- `/users` 可完成帳號與角色管理。
- `/audit-logs` 可查詢稽核紀錄。

## Docker

- `docker compose up --build -d` 可正常啟動。
- backend container 啟動時 migration 升級成功。
- `GET /api/v1/health` 回傳 `status=ok` 與 `database=ok`。

## 人工流程驗收

1. 以 admin 登入。
2. 建立或確認一個 ACTIVE 義診場次。
3. 建立病人、健康史與服務同意。
4. 建立掛號 Visit，進入診間並完成問診。
5. 建立處方，送出至藥局。
6. 藥局開始調劑、核對、發藥，確認庫存扣減。
7. 到 dashboard 確認統計變化。
8. 到 audit log 查詢使用者、同意、處方、調劑與庫存操作。
