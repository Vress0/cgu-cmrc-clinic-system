# ERD 與資料表設計

```mermaid
erDiagram
  Patient ||--|| HealthHistory : has
  Patient ||--o{ Consent : has
  Patient ||--o{ Visit : has
  ClinicSession ||--o{ Visit : includes
  Visit ||--|| QueueRecord : has
  Visit ||--o{ VitalSign : has
  Visit ||--o{ Consultation : has
  Visit ||--o{ TreatmentOrder : has
  Visit ||--o{ Prescription : has
  Prescription ||--o{ PrescriptionItem : has
  Visit ||--o{ DispensingRecord : has
  DispensingRecord ||--o{ DispensingItem : has
  Visit ||--o{ FollowUp : has
  Medication ||--o{ InventoryBatch : has
  Medication ||--o{ InventoryTransaction : has
  Medication ||--o{ DispensingItem : dispensed
  User }o--o{ Role : assigned
  Role }o--o{ Permission : grants
  User ||--o{ AuditLog : writes
```

## 共通欄位

核心資料表使用 `UUID` 主鍵，並包含：

- `created_at`
- `updated_at`
- `created_by`
- `updated_by`
- `deleted_at` 或 `is_active`

## 主要唯一限制

- `users.username`
- `users.email`
- `patients.case_number`
- `clinic_sessions.name + date`
- `visits.clinic_session_id + patient_id`
- `queue_records.clinic_session_id + queue_number`
- `medications.code`
- `inventory_batches.medication_id + batch_number`

## 核心索引

- `visits.status`
- `visits.clinic_session_id, status`
- `audit_logs.actor_id, created_at`
- `audit_logs.patient_id, created_at`
- `inventory_batches.medication_id, expires_at`
