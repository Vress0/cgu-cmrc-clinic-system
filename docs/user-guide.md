# User Guide

## Login

Open the system through Nginx or the frontend URL and sign in with an assigned account. Use only personal accounts for operational work; shared accounts should be limited to emergency bootstrap use.

## Registration Team

Use:

- `/sessions` to confirm the active clinic session.
- `/patients` to create or find patient records.
- `/patients/[id]` to review health history and consent.
- `/registration` to create a visit and queue number.

Before creating a visit, confirm service consent and key safety notes such as allergies, chronic diseases, language, and mobility assistance.

## Clinic Team

Use:

- `/clinic` for the waiting queue.
- `/clinic/[visitId]` for intake, vital signs, clinical assessment, prescription, and completion.

Confirm allergies and chronic diseases before prescription work. Send prescriptions to pharmacy only after clinical review.

## Pharmacy Team

Use:

- `/pharmacy` for the pharmacy queue.
- `/pharmacy/[visitId]` for dispensing, verification, return-to-clinic, and hand-out.
- `/inventory` to review stock batches and transactions.

Follow FEFO batch allocation and verify medication, quantity, instructions, and patient counseling before hand-out.

## Administrator

Use:

- `/users` to create accounts, assign roles, unlock users, and reset passwords.
- `/audit-logs` to inspect sensitive operations.
- `/dashboard` to monitor current workflow counts and inventory warnings.

Review audit logs after user management, consent withdrawal, prescription changes, dispensing, and inventory adjustments.
