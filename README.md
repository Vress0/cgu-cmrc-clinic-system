# 長庚大學中國醫學研究社義診健康紀錄與流程管理系統

這是一套以 Next.js、FastAPI、PostgreSQL、Docker Compose 與 Nginx 建立的義診健康紀錄與流程管理系統。系統支援掛號、診間、藥局、庫存、個資同意、使用者管理、統計與稽核紀錄。

## 一鍵部署

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

安裝腳本會自動：

- 檢查 Docker 與 Docker Compose
- 產生 `.env.production`
- 產生 `SECRET_KEY`、PostgreSQL 密碼與初始管理員密碼
- 建置並啟動 PostgreSQL、backend、frontend、Nginx
- 由 backend 啟動流程執行 Alembic migration
- 建立初始 admin 帳號
- 檢查 Health API

安裝完成後，系統會顯示系統網址、管理員帳號與本次產生的管理員密碼。請立即安全保存密碼，登入後建立具名管理者帳號。

## 部署操作

健康檢查：

```bash
./deploy/health-check.sh
```

Windows:

```powershell
.\deploy\health-check.ps1
```

更新：

```bash
./deploy/update.sh
```

Windows:

```powershell
.\deploy\update.ps1
```

備份：

```bash
./deploy/backup.sh
```

Windows:

```powershell
.\deploy\backup.ps1
```

還原：

```bash
./deploy/restore.sh backups/clinic-backup-YYYYMMDDHHMMSS.dump
```

Windows:

```powershell
.\deploy\restore.ps1 .\backups\clinic-backup-YYYYMMDDHHMMSS.dump
```

自動化驗收可使用：

```powershell
.\deploy\restore.ps1 -BackupPath .\backups\clinic-backup-YYYYMMDDHHMMSS.dump -Force
```

解除安裝：

```bash
./deploy/uninstall.sh
```

Windows:

```powershell
.\deploy\uninstall.ps1
```

解除安裝預設保留資料 volume。只有輸入確認文字 `DELETE ALL CLINIC DATA` 才會刪除 volume。

## Production Compose

部署用 compose 檔案：

- `deploy/docker-compose.production.yml`

特性：

- 只公開 Nginx `HTTP_PORT`，預設 `80`
- 不公開 PostgreSQL、backend、frontend debug ports
- 使用 named volumes：`clinic_postgres_data`、`clinic_uploads`、`clinic_backups`
- 服務皆使用 `restart: unless-stopped`
- 設定 log rotation
- backend/frontend/postgres 具備 healthcheck 或 dependency gate

## 開發環境

Development compose：

```powershell
Copy-Item .env.example .env
docker compose up --build
```

本機網址：

- Frontend: http://localhost:3000
- Nginx: http://localhost:8080
- Backend health: http://localhost:8081/api/v1/health

預設 development admin：

- 帳號：`admin`
- 密碼：`ChangeMe123!`

正式部署請使用一鍵部署產生的新密碼，不要沿用 development 密碼。

## 主要功能

- 登入與 RBAC
- 義診場次
- 病人資料與健康史
- 個資與服務同意、研究同意撤回
- 掛號與候診流程
- 診間問診、生命徵象、臨床評估
- 藥品、處方與藥局調劑
- 核對與發藥
- 庫存批次、庫存異動、FEFO 與扣庫存
- Dashboard 統計
- 使用者管理
- Audit logs

## 驗證

Backend：

```powershell
cd backend
pip install -e ".[dev]"
pytest
```

Frontend：

```powershell
cd frontend
npm install
npm run lint
npm run typecheck
npm run build
```

Migration：

```powershell
cd backend
alembic upgrade head
python -m app.modules.auth.seed_admin
```

安全檢查：

```powershell
cd frontend
npm audit --audit-level=moderate
cd ..\backend
uvx pip-audit
```

不要在部署流程中執行 `npm audit fix --force`。

## GitHub Actions

- `.github/workflows/test.yml`：backend pytest、frontend lint/typecheck/build、migration validation
- `.github/workflows/build-images.yml`：建置 backend/frontend/nginx images 並推送 GHCR
- `.github/workflows/release.yml`：打包 release deployment artifact 與 checksum

## 文件

- [需求分析](docs/01-requirements-analysis.md)
- [系統架構](docs/02-system-architecture.md)
- [使用流程](docs/03-user-flows.md)
- [ERD 與資料表](docs/04-erd-and-tables.md)
- [API 規格](docs/05-api-spec.md)
- [前端架構](docs/06-frontend-architecture.md)
- [權限矩陣](docs/07-permission-matrix.md)
- [狀態機](docs/08-state-machine.md)
- [MVP 路線圖](docs/09-mvp-roadmap.md)
- [目錄結構](docs/10-directory-structure.md)
- [個資同意與隱私](docs/11-privacy-consent.md)
- [安全與稽核](docs/12-security-audit.md)
- [Phase 4 驗收清單](docs/13-phase4-acceptance.md)
- [部署指南](docs/deployment.md)
- [備份與還原](docs/backup-and-restore.md)
- [測試指南](docs/testing.md)
- [安全說明](docs/security.md)
- [隱私與同意操作指南](docs/privacy-and-consent.md)
- [使用手冊](docs/user-guide.md)
- [一鍵部署說明](deploy/README.md)
