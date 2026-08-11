# Manual Intake

Human Reviewへ安全に投入するための手動候補バッチを保存します。

## ルール

- ファイル形式は `KC_V04_INBOX_EXPORT` schema `1.0`
- `review_status` は必ず `PENDING`
- 現物・一次資料で確認できた項目だけを格納する
- 不明項目は推定で埋めない
- 同じ候補は `dedupe_key` を固定して重複取込を防ぐ
- V04マスターへの確定反映は既存Human Reviewでのみ行う

## 2026-08-08

- `2026-08-08-weijie-hesheng-batch1.json` — WEIJIE 5件 + 東莞合升5件

## 2026-08-10

- `2026-08-10-mz100-yarn-research-batch3.json` — MZ100 69586・69587・52482の3件。業界プラットフォーム表示は `candidate`、合計102%の52482混率は `conflicting` のままHuman Reviewへ渡す
- 調査根拠Bundle: `../yarn-research/2026-08-10-mz100-evidence.json`
- `月兔毛` は同名で異なる番手・混率が存在するため、一般名だけの受信箱候補は作成しない
