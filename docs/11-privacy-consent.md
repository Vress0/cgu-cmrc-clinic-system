# 個資同意與隱私

## 同意範圍

系統將同意紀錄分為兩個層次：

- 服務同意：用於義診掛號、診間紀錄、藥局調劑與後續流程管理。未取得服務同意時，不應建立正式義診流程紀錄。
- 研究同意：用於去識別化後的統計、教學或研究分析。研究同意可獨立撤回，不影響既有服務同意。

## 實作位置

- 後端：`POST /api/v1/patients/{patient_id}/consents`
- 後端：`POST /api/v1/patients/{patient_id}/consents/{consent_id}/withdraw-research`
- 前端：`/patients/[id]`

## 撤回規則

- 撤回研究同意時，系統會將 `research_consent` 改為 `false`。
- 系統會記錄 `research_withdrawn_at`、`withdrawn_by` 與備註。
- 撤回操作會寫入 audit log，action 為 `CONSENT_RESEARCH_WITHDRAWN`。

## 操作原則

- 現場工作人員應以病人能理解的方式說明資料用途。
- 研究同意不得作為接受義診服務的必要條件。
- 匯出或統計資料應優先使用去識別化資料。
- 不應在備註欄記錄與服務無關的敏感資訊。
