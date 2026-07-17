# API 規格

## 共通格式

- Base path: `/api/v1`
- Auth: `Authorization: Bearer <access_token>`，Phase 2 啟用。
- Error response:

```json
{
  "detail": "安全且不暴露系統內部資訊的錯誤訊息"
}
```

## Phase 1

| Method | Path | 說明 |
| --- | --- | --- |
| GET | `/health` | API 與資料庫健康檢查 |

## Phase 2 之後規劃

| Module | Endpoint |
| --- | --- |
| Auth | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| Users | `GET /users`, `POST /users`, `PATCH /users/{id}` |
| Sessions | `GET /clinic-sessions`, `POST /clinic-sessions` |
| Patients | `GET /patients`, `POST /patients`, `GET /patients/{id}`, `PATCH /patients/{id}` |
| Visits | `POST /visits`, `GET /visits`, `PATCH /visits/{id}/status` |
| Clinic | `GET /clinic/queue`, `POST /consultations` |
| Pharmacy | `GET /pharmacy/queue`, `POST /dispensing-records` |
| Inventory | `GET /inventory`, `POST /inventory/transactions` |
| Audit | `GET /audit-logs` |

## Phase 2 已實作

| Method | Path | 說明 |
| --- | --- | --- |
| POST | `/auth/login` | 帳號密碼登入 |
| POST | `/auth/refresh` | Refresh Token rotation |
| POST | `/auth/logout` | 撤銷 Refresh Token |
| GET | `/auth/me` | 取得目前使用者 |

## Phase 3 已實作

| Method | Path | 說明 |
| --- | --- | --- |
| GET | `/clinic-sessions` | 列出義診場次 |
| POST | `/clinic-sessions` | 建立義診場次 |
| GET | `/patients?q=` | 搜尋或列出個案 |
| POST | `/patients` | 建立個案 |
| GET | `/patients/{patient_id}` | 取得個案 |
| PATCH | `/patients/{patient_id}` | 更新個案 |
| GET | `/patients/{patient_id}/health-history` | 取得健康背景 |
| PUT | `/patients/{patient_id}/health-history` | 建立或更新健康背景 |
| GET | `/patients/{patient_id}/consents` | 列出同意紀錄 |
| POST | `/patients/{patient_id}/consents` | 建立同意紀錄 |
| GET | `/visits` | 列出掛號紀錄，可依場次與狀態篩選 |
| POST | `/visits` | 建立掛號與候診號碼 |
| PATCH | `/visits/{visit_id}/status` | 更新 Visit 狀態 |
