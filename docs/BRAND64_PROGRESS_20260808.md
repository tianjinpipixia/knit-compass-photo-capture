# 64ブランド調査進捗 — 2026-08-08

## 正本復元

64ブランド原本は、重複監査台帳 `Knit_Compass_Deduplication_Audit_v0_1.xlsx` の Document Review から正本Drive IDを逆引きした。

- 64ブランドID/別名マッピング正本
  - file: `brand_id_alias_mapping_v1.csv`
  - canonical Drive ID: `1qUfaDXmaVmiYN2D0a2TGyKsetKpi42lo`
  - canonical path: `Knit Compass/99_Developer/KC_SANDBOX_MAIN/SANDBOX_20260711_PHASE2/brand_id_alias_mapping_v1.csv`
  - rows: 64
- 重点20ブランド正本
  - file: `brand_core_staging_priority20_v4_upl_provider.csv`
  - canonical Drive ID: `1JIKFcNy6o_nJWTBzJhXkHKsOCUHgyRag`
  - canonical path: `Knit Compass/99_Developer/KC_SANDBOX_MAIN/SANDBOX_20260711_PHASE2/brand_core_staging_priority20_v4_upl_provider.csv`
  - rows: 20
- 商品staging既存値
  - `brand_product_staging_trial_350_500_v1_publish.csv`
  - rows: 78
  - brands: GU / MUJI / ROPÉ PICNIC / GLOBAL WORK / DoCLASSE / Te chichi

## 現在の64件分類

| 状態 | 件数 | 意味 |
|---|---:|---|
| PRODUCT_EVIDENCE_PRESENT | 6 | 商品stagingが既にある。URL/公式根拠をHuman Reviewする |
| PRIORITY20_STAGED | 15 | 重点20に基本プロフィールはあるが商品stagingはない |
| MASTER_ONLY_UNCHECKED | 39 | 64件原本にはあるが今回の重点20・商品78件に未接続 |
| EXCLUDED_MENS_ONLY | 2 | 五大陸 / TAKEO KIKUCHI。今回の「メンズ対象外」運用により調査対象外 |
| IDENTITY_REVIEW_REQUIRED | 2 | ANY / MATINEE LINE。ブランド同一性・公式範囲を先に確認する |

合計64件。

## 商品78件の内訳

- GLOBAL WORK: 23
- ROPÉ PICNIC: 22
- DoCLASSE: 20
- Te chichi: 6
- GU: 4
- MUJI: 3

商品レコードが存在することと、公式根拠確認済みは別扱いとする。既存78件には `REVIEW_REQUIRED` が多いため、件数だけで「ブランド調査完了」としない。

## 調査順

1. `PRODUCT_EVIDENCE_PRESENT` 6ブランドの既存商品URLを公式根拠で再確認
2. `PRIORITY20_STAGED` 15ブランドの公式ブランドURL・女性向けニット商品URLを補完
3. `IDENTITY_REVIEW_REQUIRED` 2件を先に解決
4. `MASTER_ONLY_UNCHECKED` 39件から、女性向けニット対象を順に公式確認
5. メンズ専業2件は母数には残し、今回の調査実働から除外

## 安全ルール

- メンズ対象外
- 公式サイト優先
- 商品単位の混率・機能をブランド全体へ一般化しない
- 公式確認できない項目は `NOT AVAILABLE` / `REVIEW REQUIRED`
- `ANY` を any SiS / any FAM に自動統合しない
- `MUJI` と `MUJI Labo` は別行を維持
