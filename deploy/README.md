# One-Click Deployment

This folder contains the deployment kit for the clinic system.

## Fresh Install

Linux/macOS:

```bash
git clone https://github.com/Vress0/cgu-cmrc-clinic-system.git
cd cgu-cmrc-clinic-system
chmod +x install.sh deploy/*.sh
./install.sh
```

Windows PowerShell:

```powershell
git clone https://github.com/Vress0/cgu-cmrc-clinic-system.git
cd cgu-cmrc-clinic-system
.\install.ps1
```

The installer creates `.env.production`, generates secrets, builds images, starts PostgreSQL/backend/frontend/Nginx, runs migrations through backend startup, creates the initial admin account, and checks health.

## Daily Operations

```bash
./deploy/health-check.sh
./deploy/backup.sh
./deploy/update.sh
```

Windows:

```powershell
.\deploy\health-check.ps1
.\deploy\backup.ps1
.\deploy\update.ps1
```

Restore requires an explicit confirmation phrase. For Windows automation, use `-Force` only after selecting the correct backup file:

```powershell
.\deploy\restore.ps1 -BackupPath .\backups\clinic-backup-YYYYMMDDHHMMSS.dump -Force
```

## Safety Rules

- `.env.production` is never committed.
- Backups are never committed.
- Scripts do not run `docker compose down -v`.
- Uninstall requires the confirmation phrase `DELETE ALL CLINIC DATA` before removing volumes.
- Do not run `npm audit fix --force` as part of deployment.
