# 長庚大學中國醫學研究社義診健康紀錄與流程管理系統

這是一套以 Next.js、FastAPI、PostgreSQL、Docker Compose 與 Nginx 建立的義診流程系統。系統支援掛號組、診間組、藥局組與管理者的現場工作流程，並逐步加入處方、調劑、庫存、個資同意、使用者管理與稽核功能。

## 目前狀態

- Phase 1-3 已完成 MVP、處方藥局流程、庫存批次、FEFO 與發藥扣庫存。
- Phase 4 已加入個資同意撤回、病人詳細健康史、使用者管理、dashboard 統計、稽核查詢與完整驗收測試。
- 目前開發分支：`feat/system-administration`。

## 主要路由

- `/login`：登入
- `/dashboard`：現場營運儀表板
- `/sessions`：義診場次
- `/registration`：掛號工作台
- `/patients`、`/patients/[id]`：病人清單、健康史與個資同意
- `/clinic`、`/clinic/[visitId]`：診間佇列與看診紀錄
- `/pharmacy`、`/pharmacy/[visitId]`：藥局調劑、核對與發藥
- `/medications`：藥品主檔
- `/inventory`：庫存批次與異動
- `/users`：使用者與角色管理
- `/audit-logs`：稽核紀錄查詢

## Docker 執行

1. 建立環境檔：

```powershell
Copy-Item .env.example .env
```

2. 啟動服務：

```powershell
docker compose up --build
```

3. 開啟：

- Frontend: http://localhost:3000
- Backend health: http://localhost:8081/api/v1/health
- Nginx: http://localhost:8080

預設管理員會由 backend 啟動流程建立：

- 帳號：`admin`
- 密碼：`ChangeMe123!`

正式環境請務必修改 `.env` 的 `SECRET_KEY` 與 `DEFAULT_ADMIN_PASSWORD`。

## 本機驗證

後端：

```powershell
cd backend
pip install -e ".[dev]"
pytest
```

前端：

```powershell
cd frontend
npm install
npm run lint
npm run typecheck
npm run build
```

資料庫 migration：

```powershell
cd backend
alembic upgrade head
python -m app.modules.auth.seed_admin
```

## Phase 4 驗收重點

- 個資與服務同意可新增，研究同意可單獨撤回並寫入稽核。
- 管理員可建立使用者、調整角色、停用/啟用帳號、解除鎖定與重設密碼。
- Dashboard 顯示掛號、候診、看診、藥局、完成、場次、病人、藥品與庫存警示統計。
- 稽核頁可依操作、資料類型、關鍵字與筆數查詢。
- 病人詳細頁集中管理基本資料、健康史、過敏、慢性病、特殊協助與同意紀錄。

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
