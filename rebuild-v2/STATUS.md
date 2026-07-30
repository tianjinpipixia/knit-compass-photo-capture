# Knit Compass Material Photo Rebuild v2.0

Status: QA-passed reconstruction candidate prepared on 2026-07-30 (Asia/Tokyo).

## Scope

- Rebuild target: material photo / Photo Capture site
- Knit Compass V04: unchanged
- Runtime: local IndexedDB, DRAFT first, append-only history
- Automatic master update: OFF
- Automatic publish: OFF
- External API/network calls: none

## Implemented

- Initial-capture flow instead of technical-classification-heavy form
- Field order: 担当者名 → 部署 → 入手先 → 資料区分 → 糸商 → 糸名・素材名 → 略称 → 番手 → 混率 → シーズン
- Exact 資料区分 options
- Five photo categories: 表紙・全体 / 編地・質感 / 色見本 / 混率・規格 / その他
- Dashboard shows 番手 / 混率 / ゲージ
- 編集・修正 / 保存 / 新規登録 controls
- Legacy portable ZIP import
- Existing technical fields preserved as compatibility data and moved to the next-stage flow

## QA

- JavaScript syntax: PASS
- CREATE and UPDATE: PASS
- Photo save/orientation: PASS
- Portable ZIP export and fresh import: PASS
- Console errors: 0
- External HTTP/HTTPS requests: 0

The complete reviewed ZIP is stored in the user's ChatGPT Library under `/Knit Compass/Rebuild/` and is not published to production yet.
