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
- `2026-08-19-winning-textile-levita-batch10.json` — Winning Textile Levita / 利维纱 1件（1/40 Nm・R78/P22・bright/dull・交撚、Viscose側フィラメントはSupplier説明として保持）
- `2026-10-07-qiyuan-qysmart-comfy-batch11.json` — 青岛绮源 QYSMART-COMFY 1件（40s/1、VIS80/P10/機能繊維10、通常3浴→今回2浴、改質アクリル白残しメランジ、ウールライク外観）

## 一括取込

`/owner-yarns/` の現行取込からは、batch1–11の合計26件を `kc_v04_handoff_queue_v1` へ重複なく追加できます。batch10のWinning Textile Levitaとbatch11の青岛绮源 QYSMART-COMFYも `PENDING` 候補として同じHuman Review導線に含めます。QYSMART-COMFYは、展示会スワッチで確認した40s/1・VIS80/P10/機能繊維10、調湿・吸湿発熱・消臭に加え、Supplier説明の「通常3浴、今回2浴」「改質アクリルは染めず白残しでメランジ効果」を保持します。カードの「アクリレート」とSupplier説明の「改性腈纶／改質アクリル」は同一視せず、正式な日本表示分類はHuman Reviewで確認します。AMERICAN HOLICは8/13の2件に加え、8/14現物確認の2件（0H001683100 / 0H002151200）も同じHuman Review導線に含まれます。鼎宏は会社候補とMZ100 ID 25139の糸候補を別レコードで保持し、MZ100掲載会社を製造者へ自動昇格しません。取込後も全件 `PENDING` のままで、承認前に正式マスターへ自動昇格しません。
