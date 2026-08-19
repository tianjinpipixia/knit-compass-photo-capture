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
- `2026-08-18-american-holic-products-batch8.json` — AMERICAN HOLIC 2件（0H001683100 / 0H002151200、2026-08-14現物タグ）
- `2026-08-18-dinghong-mz100-25139-batch9.json` — 东莞市鼎宏纺织品有限公司 会社候補＋MZ100 25139 羊毛马海毛 2件
- `2026-08-19-winning-textile-levita-batch10.json` — Winning Textile Levita / 利维纱 1件（現物BOOK：Nm 1/40、Viscose 78% / Polyester 22%、bright / dull）

## 一括取込

`/owner-yarns/` の現行「未反映24件の取込」はbatch1〜9・合計24件を `kc_v04_handoff_queue_v1` へ重複なく追加します。batch10のWinning Textile LevitaはこのブランチでPENDING候補として追加済みですが、現行の一括取込ボタンにはまだ含めません。AMERICAN HOLICは8/13の2件に加え、8/14現物確認の2件（0H001683100 / 0H002151200）も同じHuman Review導線に含まれます。鼎宏は会社候補とMZ100 ID 25139の糸候補を別レコードで保持し、MZ100掲載会社を製造者へ自動昇格しません。取込後も全件 `PENDING` のままで、承認前に正式マスターへ自動昇格しません。
