# 長庚大學中國醫學研究社義診健康紀錄系統

義診健康紀錄與流程管理系統。第一版採前後端分離與模組化單體架構：Next.js、FastAPI、PostgreSQL、Docker Compose 與 Nginx。

## Phase 1 內容

- 10 項設計文件：`docs/`
- FastAPI 後端骨架：`backend/`
- Next.js 前端骨架與指定路由 placeholder：`frontend/`
- PostgreSQL 與 Docker Compose：`docker-compose.yml`
- Nginx 反向代理設定：`nginx/nginx.conf`
- 環境變數範本：`.env.example`
- 健康檢查 API：`GET /api/v1/health`
- 後端健康檢查測試：`backend/tests/test_health.py`

## Phase 2 內容

- User、Role、Permission、RefreshToken 資料模型
- Auth/RBAC migration：`backend/alembic/versions/202607170002_auth_rbac.py`
- JWT Access Token 與 Refresh Token rotation
- Argon2 密碼雜湊
- 登入失敗計數與暫時鎖定
- 預設管理員 seed：`python -m app.modules.auth.seed_admin`
- Auth API：`POST /api/v1/auth/login`、`POST /api/v1/auth/refresh`、`POST /api/v1/auth/logout`、`GET /api/v1/auth/me`
- 前端登入頁串接與登出
- Auth 測試：`backend/tests/test_auth.py`

## Phase 3 內容

- ClinicSession、Patient、HealthHistory、Consent、Visit、QueueRecord 資料模型
- Registration migration：`backend/alembic/versions/202607170003_registration.py`
- RBAC 保護的場次、個案、健康背景、同意紀錄與掛號 API
- 同一個個案在同一場次不可重複掛號
- 候診號碼自動依場次遞增
- Visit 狀態機基礎驗證
- 前端最小可用頁面：
  - `/sessions` 建立與查看義診場次
  - `/patients` 建立與搜尋個案
  - `/registration` 建立掛號並顯示候診號碼
- 掛號流程測試：`backend/tests/test_registration.py`

## 啟動方式

1. 建立環境變數：

```powershell
Copy-Item .env.example .env
```

2. 啟動服務：

```powershell
docker compose up --build
```

3. 開啟服務：

- 前端：http://localhost:3000
- 後端健康檢查：http://localhost:8000/api/v1/health
- Nginx 入口：http://localhost

Docker 啟動後，後端容器會自動執行 migration 並建立預設管理員：

- 帳號：`admin`
- 密碼：`ChangeMe123!`

正式或共享環境必須先修改 `.env` 中的 `SECRET_KEY` 與 `DEFAULT_ADMIN_PASSWORD`。

Phase 3 操作順序：

1. 用預設管理員登入 `/login`。
2. 到 `/sessions` 建立一筆義診場次。
3. 到 `/patients` 建立一筆個案。
4. 到 `/registration` 選擇場次與個案建立掛號。

## 本機後端測試

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

## 本機資料庫初始化

若使用本機 PostgreSQL，設定 `.env` 後執行：

```powershell
cd backend
alembic upgrade head
python -m app.modules.auth.seed_admin
```

## 本機前端檢查

```powershell
cd frontend
npm install
npm run typecheck
npm run build
```

## 設計文件

- [專案需求分析](docs/01-requirements-analysis.md)
- [系統架構圖](docs/02-system-architecture.md)
- [使用者流程圖](docs/03-user-flows.md)
- [ERD 與資料表設計](docs/04-erd-and-tables.md)
- [API 規格](docs/05-api-spec.md)
- [頁面與元件架構](docs/06-frontend-architecture.md)
- [權限矩陣](docs/07-permission-matrix.md)
- [狀態機設計](docs/08-state-machine.md)
- [MVP 開發排程](docs/09-mvp-roadmap.md)
- [完整目錄結構](docs/10-directory-structure.md)

## Phase 4 預計內容

- 候診列表
- VitalSign
- Consultation
- TreatmentOrder
- 診間工作台
- 狀態轉換驗證擴充
