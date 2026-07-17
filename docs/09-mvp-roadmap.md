# MVP 開發排程

## Phase 1：專案初始化

- 前端與後端專案骨架。
- Docker Compose、PostgreSQL、環境變數。
- 健康檢查 API。
- README 啟動方式。

## Phase 2：登入與權限

- User、Role、Permission。
- JWT Access Token、Refresh Token、RBAC。
- 預設管理員建立方式。

## Phase 3：義診場次與掛號

- ClinicSession、Patient、HealthHistory、Consent、Visit、QueueRecord。
- 掛號組頁面與重複掛號驗證。

## Phase 4：診間

- 候診列表、VitalSign、Consultation、TreatmentOrder。
- 診間工作台與狀態轉換驗證。

## Phase 5：藥局

- Medication、InventoryBatch、Prescription、DispensingRecord。
- 調劑、核對、發藥、退回與庫存扣除。

## Phase 6：稽核與統計

- AuditLog、今日統計、場次統計、匿名匯出。

## Phase 7：測試與安全

- 單元測試、API 整合測試、E2E、權限、重複掛號、庫存一致性與並發測試。
