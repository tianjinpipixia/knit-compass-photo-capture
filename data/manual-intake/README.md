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
- `2026-08-08-weihai-yaxin-chengyun-batch2.json` — 威海雅信 + 威海诚韵の会社候補2件

## 2026-08-10

- `2026-08-10-mz100-yarn-research-batch3.json` — MZ100 69586・69587・52482の3件。業界プラットフォーム表示は `candidate`、合計102%の52482混率は `conflicting` のままHuman Reviewへ渡す
- 調査根拠Bundle: `../yarn-research/2026-08-10-mz100-evidence.json`
- `月兔毛` は同名で異なる番手・混率が存在するため、一般名だけの受信箱候補は作成しない

## 2026-08-12

- `2026-08-12-twin-win-company-factory-batch4.json` — TWIN WIN TEXTILE CO., LTD. / 众瀛纺织品有限公司の会社・工場候補1件。歴史資料値として保持し、現行法人・稼働状況はHuman Reviewで再確認
- `2026-08-12-rope-picnic-gdm56050-batch5.json` — ROPÉ PICNIC GDM56050の商品候補1件。公式URLと品番のみ確定候補とし、商品名・価格・混率・機能等は再取得まで空欄

## 一括取込

`/owner-yarns/` の「未反映17件の取込」から、上記5バッチ・合計17件を `kc_v04_handoff_queue_v1` へ重複なく追加できます。取込後も全件 `PENDING` のままで、正式マスターへの自動昇格は行いません。
