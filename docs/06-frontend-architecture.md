# 頁面與元件架構

## 路由

- `/login`
- `/dashboard`
- `/registration`
- `/registration/new`
- `/patients`
- `/patients/[id]`
- `/clinic`
- `/clinic/[visitId]`
- `/pharmacy`
- `/pharmacy/[visitId]`
- `/sessions`
- `/medications`
- `/inventory`
- `/users`
- `/audit-logs`
- `/settings`

## 元件分層

- `components/layout`：AppShell、Sidebar、Topbar。
- `components/forms`：欄位、錯誤提示、自動暫存提示。
- `components/status`：流程狀態、警示、載入與錯誤狀態。
- `features/*`：依業務模組放置頁面內部元件與 hooks。
- `lib/api`：TanStack Query client 與 API client。
- `lib/auth`：登入狀態、token 儲存與閒置登出。

## UI 原則

- 工作台第一屏顯示可操作資訊。
- 名單使用清楚狀態文字與圖示，不只依靠顏色。
- 過敏與退回原因使用明顯警示區塊。
- 平板可點選尺寸至少 44px。
- 表單禁止重複送出，並顯示載入、成功與錯誤狀態。
