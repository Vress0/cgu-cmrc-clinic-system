# 安全與稽核

## 身分與權限

系統使用 JWT access token、refresh token rotation 與 RBAC 權限控管。Phase 4 的主要角色如下：

| 角色 | 用途 |
| --- | --- |
| `admin` | 系統管理、使用者、稽核、庫存與全流程 |
| `registration` | 場次、病人、掛號 |
| `clinic_student` | 診間紀錄與病人查閱 |
| `clinician` | 診間紀錄、臨床評估與處方確認 |
| `pharmacy` | 藥局調劑、核對、發藥 |

## 重要安全控制

- 密碼以 Argon2 雜湊保存。
- 登入失敗會累計次數並支援鎖定解除。
- 管理員可停用帳號與重設密碼。
- 前端使用者管理頁不顯示既有密碼。
- 所有管理操作需由後端權限檢查，不只依賴前端隱藏 UI。

## 稽核紀錄

稽核紀錄 API：

- `GET /api/v1/audit-logs`
- 支援 `action`、`entity_type`、`q`、`limit` 篩選。

目前 Phase 4 覆蓋的關鍵 action：

- `USER_CREATED`
- `USER_UPDATED`
- `USER_PASSWORD_RESET`
- `CONSENT_CREATED`
- `CONSENT_RESEARCH_WITHDRAWN`
- 處方、調劑、發藥與庫存異動相關 action

## 驗收注意事項

- 以非 admin 帳號測試 `/users` 與 `/audit-logs` 應被拒絕。
- 重設密碼與停用帳號後，應在 audit log 查得到紀錄。
- 發藥扣庫存需保持 idempotency key，避免重複扣庫存。
- 不建議在正式環境直接使用預設管理員密碼。
