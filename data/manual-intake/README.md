# Manual Intake

Human Reviewへ安全に投入するための手動候補バッチを保存します。

## ルール

- ファイル形式は `KC_V04_INBOX_EXPORT` schema `1.0`
- `review_status` は必ず `PENDING`
- 現物・一次資料で確認できた項目だけを格納する
- 不明項目は推定で埋めない
- 同じ候補は `dedupe_key` を固定して重複取込を防ぐ
- V04マスターへの確定反映はHuman Reviewでのみ行う

## 現在のバッチ

- `2026-08-08-weijie-hesheng-batch1.json` — 10件
- `2026-08-08-weihai-yaxin-chengyun-batch2.json` — 2件
- `2026-08-10-mz100-yarn-research-batch3.json` — 3件
- `2026-08-12-twin-win-company-factory-batch4.json` — 1件
- `2026-08-12-rope-picnic-gdm56050-batch5.json` — 1件
- `2026-08-13-american-holic-products-batch6.json` — AMERICAN HOLIC 2件
- `2026-08-17-minghai-wool-silk-core-spun-batch7.json` — MINGHAI 羊毛绢丝包芯纱 1件

## 一括取込

`/owner-yarns/` の「未反映19件の取込」から、上記7バッチ・合計20件を `kc_v04_handoff_queue_v1` へ重複なく追加できます。AMERICAN HOLIC 2件も同じHuman Review導線に含まれます。取込後も全件 `PENDING` のままで、承認前に正式マスターへ自動昇格しません。
