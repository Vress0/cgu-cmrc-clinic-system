# Testing Guide

## Automated Checks

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
```

Security:

```powershell
cd frontend
npm audit --audit-level=moderate
cd ..\backend
uvx pip-audit
```

Migration:

```powershell
cd backend
alembic current
alembic upgrade head
alembic current
```

Docker:

```powershell
docker compose down
docker compose up --build -d
docker compose ps
docker compose logs backend --tail=200
docker compose logs frontend --tail=200
docker compose logs nginx --tail=100
```

## Current Script Coverage

The frontend currently has no `npm run test` or `npm run test:e2e` script. Treat those as not configured until a test runner is added. Do not report E2E as passed unless Playwright or another browser test runner is actually implemented and executed.

## Manual Workflow Checks

1. Admin login.
2. Create an active clinic session.
3. Create patient data, health history, and service consent.
4. Create registration visit.
5. Start clinic consultation.
6. Record intake, vital signs, clinical assessment, and prescription.
7. Send prescription to pharmacy.
8. Start dispensing, verify, and hand out medication.
9. Confirm FEFO stock deduction and inventory transactions.
10. Confirm dashboard counts and audit logs.
11. Switch from LIVE to DEMO and confirm LIVE patients, visits, prescriptions, inventory batches, and audit logs are hidden.
12. Seed or create DEMO records, switch back to LIVE, and confirm DEMO records are hidden and LIVE records remain unchanged.

## Responsive Smoke Test Viewports

- `1440 x 900`
- `1024 x 768`
- `768 x 1024`
- `390 x 844`

Check these pages:

- `/login`
- `/dashboard`
- `/sessions`
- `/patients`
- `/patients/[id]`
- `/registration`
- `/clinic`
- `/clinic/[visitId]`
- `/medications`
- `/inventory`
- `/pharmacy`
- `/pharmacy/[visitId]`
- `/users`
- `/audit-logs`

Look for overlap, clipped controls, broken cards, raw `undefined`, raw `null`, enum leakage, and unreadable table layouts.
