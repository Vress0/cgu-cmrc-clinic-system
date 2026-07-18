# 長庚大學中國醫學研究社義診健康紀錄與流程管理系統

這是一套給「長庚大學中國醫學研究社」義診現場使用的 Web 系統，目標是把掛號、診間、藥局、庫存、個資同意、使用者管理、統計與稽核紀錄集中在同一套流程中。

系統使用 Next.js、FastAPI、PostgreSQL、Docker Compose 與 Nginx 建置，可用於本機開發、社團展示、教學演練與正式義診部署。

## 主要功能

- 登入與角色權限控管
- Dashboard 統計
- 義診場次管理
- 病人基本資料、健康史與特殊協助需求
- 個資與服務同意、研究同意撤回
- 掛號、候診與叫號流程
- 診間問診、生命徵象、臨床評估與處方
- 藥局工作台、調劑、核對與發藥
- 藥品主檔、庫存批次、庫存異動與 FEFO 扣庫存
- LIVE 正式資料模式與 DEMO 假資料模式隔離
- 使用者管理與 Audit Log 稽核紀錄
- Docker 一鍵部署、備份、還原、更新與解除安裝

## 技術架構

| Layer | Tech |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Auth | JWT access token, refresh token, RBAC |
| Runtime | Docker Compose |
| Reverse Proxy | Nginx |

## 快速開始：開發環境

需求：

- Docker Desktop
- Docker Compose
- Git

Windows PowerShell：

```powershell
git clone https://github.com/Vress0/cgu-cmrc-clinic-system.git
cd cgu-cmrc-clinic-system
Copy-Item .env.example .env
docker compose up --build -d
```

Linux/macOS：

```bash
git clone https://github.com/Vress0/cgu-cmrc-clinic-system.git
cd cgu-cmrc-clinic-system
cp .env.example .env
docker compose up --build -d
```

本機網址：

- 系統入口：http://localhost:8080
- Frontend direct：http://localhost:3000
- Backend health：http://localhost:8081/api/v1/health

預設開發帳號：

```text
帳號：admin
密碼：ChangeMe123!
```

正式部署請不要沿用開發密碼。

## 一鍵部署：正式環境

Windows PowerShell：

```powershell
git clone https://github.com/Vress0/cgu-cmrc-clinic-system.git
cd cgu-cmrc-clinic-system
.\install.ps1
```

Linux/macOS：

```bash
git clone https://github.com/Vress0/cgu-cmrc-clinic-system.git
cd cgu-cmrc-clinic-system
chmod +x install.sh deploy/*.sh
./install.sh
```

安裝腳本會自動：

- 檢查 Docker 與 Docker Compose
- 建立 `.env.production`
- 產生 `SECRET_KEY`、PostgreSQL 密碼與初始管理員密碼
- 建置並啟動 PostgreSQL、backend、frontend、Nginx
- 執行 Alembic migration
- 建立初始 admin 帳號
- 執行 Health API 檢查

安裝完成後，終端機會顯示系統網址與管理員帳號。若密碼由腳本產生，會只顯示一次，請立即保存。

## LIVE / DEMO 資料模式

系統支援兩種資料模式：

- `LIVE`：正式資料模式
- `DEMO`：假資料／示範模式

這不是只在前端切換顯示資料，而是後端 row-level tenant isolation。義診業務資料表會以 `data_mode` 隔離，後端查詢會自動套用目前使用者的模式。

隔離範圍包含：

- 義診場次
- 病人資料
- 健康史與同意紀錄
- 掛號與候診
- 診間紀錄
- 處方與藥局調劑
- 庫存批次與庫存異動
- Audit Log

藥品主檔共用，但庫存批次與庫存異動會依 LIVE / DEMO 隔離，所以 DEMO 發藥不會扣到 LIVE 庫存。

管理員可在側邊欄切換資料模式，也可到：

```text
/settings/demo-data
```

建立、重置或刪除 DEMO 假資料。

相關環境變數：

```env
ENABLE_DEMO_MODE=true
DEFAULT_DATA_MODE=LIVE
ALLOW_DEMO_RESET=true
```

完整說明見 [docs/data-mode.md](docs/data-mode.md)。

## 常用部署指令

健康檢查：

```powershell
.\deploy\health-check.ps1
```

更新：

```powershell
.\deploy\update.ps1
```

備份：

```powershell
.\deploy\backup.ps1
```

還原：

```powershell
.\deploy\restore.ps1 .\backups\clinic-backup-YYYYMMDDHHMMSS.dump
```

解除安裝：

```powershell
.\deploy\uninstall.ps1
```

Linux/macOS 對應腳本位於 `deploy/*.sh`。

## 開發與驗證

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
alembic current
python -m app.modules.auth.seed_admin
```

Docker：

```powershell
docker compose up --build -d
docker compose ps
docker compose logs backend --tail=200
docker compose logs frontend --tail=200
```

## 專案目錄

```text
backend/      FastAPI 後端、SQLAlchemy models、Alembic migrations、pytest
frontend/     Next.js 前端、Tailwind UI、API client
deploy/       一鍵部署、更新、備份、還原、解除安裝腳本
docs/         系統文件、部署、測試、安全、資料模式與使用手冊
nginx/        Nginx reverse proxy 設定
```

## 安全注意事項

- 正式部署必須使用強密碼與新的 `SECRET_KEY`。
- 不要公開 PostgreSQL `5432`、backend `8000` 或 frontend `3000` debug port。
- 對外只應公開 Nginx HTTP/HTTPS port。
- 備份檔可能包含敏感資料，請妥善保存。
- DEMO 模式僅供展示與教學，不可取代正式環境與測試環境隔離。
- 若瀏覽器出現 `Invalid token`，重新登入即可；前端會自動清除過期 session。

## 文件

- [部署指南](docs/deployment.md)
- [LIVE / DEMO 資料模式](docs/data-mode.md)
- [測試指南](docs/testing.md)
- [安全說明](docs/security.md)
- [備份與還原](docs/backup-and-restore.md)
- [使用手冊](docs/user-guide.md)
- [API 規格](docs/05-api-spec.md)
- [系統架構](docs/02-system-architecture.md)
- [權限矩陣](docs/07-permission-matrix.md)
- [狀態機](docs/08-state-machine.md)
- [一鍵部署說明](deploy/README.md)

## GitHub Actions

- `.github/workflows/test.yml`：backend pytest、frontend lint/typecheck/build、migration validation
- `.github/workflows/build-images.yml`：建置 backend/frontend/nginx images 並推送 GHCR
- `.github/workflows/release.yml`：打包 release deployment artifact 與 checksum
