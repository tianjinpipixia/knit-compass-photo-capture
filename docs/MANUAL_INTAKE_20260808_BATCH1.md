# 2026-08-08 現物糸 Human Review 取込 — Batch 1

Batch ID: `KC-MANUAL-20260808-BATCH1-WEIJIE-HESHENG`

## 方針

ユーザー提供の現物BOOK／サンプルカード写真で、印刷表示を直接確認できた項目だけを `KC_V04_INBOX_EXPORT` に変換する。

- 直接マスターへ書き込まない
- すべて `PENDING` でHuman Review受信箱へ入れる
- Human Review承認後だけV04糸・会社マスターへ昇格する
- 糸構造・紡績方法など写真にない項目は推定しない
- `仿亚麻` / `亚麻爽` の名称から天然麻含有を自動確定しない
- 価格は現行handoffの専用フィールドがないため `notes` に参考価格として保持する

## Batch 1 — 10件

| Supplier | 糸名 / Code | 番手 | 混率 | Gauge | 参考価格 | 根拠写真 |
|---|---|---:|---|---:|---:|---|
| 苏州维杰纺织有限公司 | TL-2251 | 2/32NM | PBT 20 / Wool 10 / Polyester 49 / Acrylic 21 | — | 50元 | IMG_2969.JPG |
| 苏州维杰纺织有限公司 | TL-1352 | 2/32NM | Acrylic 29 / Viscose 37 / Cotton 16 / PTT 18 | — | 未確認 | IMG_2971.jpeg |
| 苏州维杰纺织有限公司 | TL-1353 | 2/48NM | Acrylic 25 / Viscose 33 / Cotton 14 / PTT 28 | — | 未確認 | IMG_2971.jpeg |
| 苏州维杰纺织有限公司 | TL-1502 | 2/50NM | Viscose 72 / PBT 28 | — | 48元 | IMG_2973.JPG |
| 苏州维杰纺织有限公司 | TL-1530 | 2/50NM | Viscose 70 / PTT 30 | 14G / 1END | 未確認 | IMG_2974.jpeg |
| 东莞市合升纺织品有限公司 | 纳米丝麻棉（全精梳） | 2/80NM | Cotton 78 / Polyester 22 | 16G | 未確認 | IMG_4115.jpeg |
| 东莞市合升纺织品有限公司 | 48支纳米丝麻棉 | 2/48NM | Cotton 88 / Polyester 12 | 14G | 47元 | IMG_4117.jpeg |
| 东莞市合升纺织品有限公司 | 58支纳米丝麻棉 | 2/58NM | Cotton 85 / Polyester 15 | 14G | 58元 | IMG_4118.jpeg |
| 东莞市合升纺织品有限公司 | 超高捻仿亚麻 | 1/24NM | Viscose 89 / Nylon 11 | 14G | 33元 | IMG_4120.jpeg |
| 东莞市合升纺织品有限公司 | 高端亚麻爽 | 1/24NM | Viscose 89 / Polyester 11 | 14G | 33元 | IMG_4121.jpeg |

混率はすべて `%` としてJSONへ格納し、合計100として確認済み。Supplierごとに同じ一時会社IDを使うため、Human Review承認時に同一会社へ集約される。

## 今回あえて除外

### 东莞市合升纺织品有限公司 — 30S/4 / 61元

`IMG_4119.jpeg`。12% Linenまでは見えるが、反射で残り混率と商品名が完全に読めないためBatch 1には含めない。

### 苏州维杰纺织 — 雀羽绒 / Ologeal 2.0

価格49元の記録はあるが、番手・混率の現物根拠がまだ揃っていないためBatch 1には含めない。

## 取込ファイル

`data/manual-intake/2026-08-08-weijie-hesheng-batch1.json`

形式は既存Human Reviewが対応している `KC_V04_INBOX_EXPORT` / schema `1.0`。同じ `dedupe_key` は再取込しても重複しない。

## 完了条件

1. Human Review画面でJSONを取り込む
2. 10件がPENDING表示される
3. 内容を確認し、糸として承認する
4. WEIJIE 5糸・合升5糸が糸マスターへ反映される
5. 会社マスターはWEIJIE／合升それぞれ1社に集約される
