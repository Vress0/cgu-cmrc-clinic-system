# Data Mode: LIVE and DEMO

The system supports two isolated data modes:

- `LIVE`: formal production records
- `DEMO`: sample records for teaching, rehearsal, and demonstrations

This is implemented as row-level tenant isolation. Business tables include a required `data_mode` column, and SQLAlchemy applies the current mode automatically through the backend session. The frontend may display the current mode, but it is not trusted as an authorization source.

## Scoped Tables

The following tables are mode-scoped:

- `clinic_sessions`
- `patients`
- `consents`
- `health_histories`
- `visits`
- `queue_records`
- `vital_signs`
- `consultations`
- `prescriptions`
- `prescription_items`
- `dispensing_records`
- `dispensing_items`
- `inventory_batches`
- `inventory_transactions`
- `audit_logs`

`medications` remains a shared master table. Inventory batches and transactions are still isolated, so DEMO dispensing cannot deduct LIVE stock.

## Backend Behavior

- Current mode is stored on the user as `current_data_mode`.
- Auth dependencies resolve the user's effective mode and write it into `db.info["data_mode"]`.
- New mode-scoped rows automatically receive the effective mode.
- Reads in the wrong mode return no result, which surfaces as `404` in resource-detail APIs.
- Unique constraints that represent business identity include `data_mode`, such as patient case number and queue number.
- Audit logs include `data_mode`, including `DATA_MODE_SWITCHED` and DEMO seed/reset/delete actions.

## API

```text
GET    /api/v1/data-mode
POST   /api/v1/data-mode/switch
GET    /api/v1/demo-data/status
POST   /api/v1/demo-data/seed
POST   /api/v1/demo-data/reset
DELETE /api/v1/demo-data
```

Switch requests require a confirmation phrase:

```json
{ "mode": "DEMO", "confirmation": "SWITCH TO DEMO" }
```

```json
{ "mode": "LIVE", "confirmation": "SWITCH TO LIVE" }
```

Deleting all DEMO data requires:

```json
{ "confirmation": "DELETE DEMO DATA" }
```

## Permissions

The default admin role can switch and manage DEMO data. Role permissions include:

- `data_mode.live.access`
- `data_mode.demo.access`
- `data_mode.switch`
- `demo_data.manage`

Users also have access flags:

- `can_access_live`
- `can_access_demo`
- `default_data_mode`
- `current_data_mode`

## Environment Variables

```text
ENABLE_DEMO_MODE=true
DEFAULT_DATA_MODE=LIVE
ALLOW_DEMO_RESET=true
```

Set `ENABLE_DEMO_MODE=false` to disable DEMO access. Set `ALLOW_DEMO_RESET=false` when a deployed site should allow viewing existing DEMO data but not bulk resetting it.

## Manual Smoke Test

1. Login as admin.
2. Confirm the sidebar shows `LIVE 正式資料`.
3. Create one LIVE patient.
4. Switch to `DEMO`.
5. Confirm the patient list is empty.
6. Create or seed DEMO data.
7. Confirm DEMO records are visible and LIVE records are hidden.
8. Switch back to `LIVE`.
9. Confirm the original LIVE patient is visible and DEMO records are hidden.
10. Delete DEMO data from `/settings/demo-data` and confirm LIVE records remain.
