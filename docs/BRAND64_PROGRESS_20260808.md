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

## 公式現行性・位置づけ確認: 64 / 64

2026-08-08に64件すべてを現行公式ソースで確認した。

- Batch 1: 24件
  - `data/brand-research/2026-08-08-official-verification-batch1.csv`
- Batch 2: 40件
  - `data/brand-research/2026-08-08-official-verification-batch2.csv`

ここでいう「確認済み」は、ブランドまたは現行ラインの存在・公式な位置づけを確認したという意味。商品単位の糸・混率・機能・価格調査完了を意味しない。

### 特殊な位置づけ

- `BR-00020 any FAM`: 公式ANYページでANYへのリブランドを確認。`LEGACY_REBRANDED` として履歴保持。
- `BR-00059 ANY`: 現行ANYブランドとして確認。`CURRENT_BRAND_IDENTITY_RESOLVED`。
- `BR-00061 MATINEE LINE`: GLOBAL WORK公式内の女性向けラインとして確認。`SUBLINE_RESOLVED`。独立ブランドとして一般化しない。
- `BR-00043 J.Press`: canonical名は維持し、今回の女性調査は公式 `J.PRESS LADIES` を対象にする。
- `BR-00044 五大陸` / `BR-00048 TAKEO KIKUCHI`: 現行公式ブランドであることは確認済み。ただしメンズ対象外運用により商品調査から除外。
- `BR-00060 MUJI Labo`: MUJI本体とは別行を維持し、2026現行ラインとして確認。

### 公式現行性は確認したが、女性向け範囲を商品単位で追加確認する8件

JEANASIS / HARE / Heather / PAGEBOY / A part by / mysty woman / Andemiu / ALAND。

これらは現行ブランド一覧・公式ニュースで存在確認済みだが、女性ニットの対象範囲を商品単位で確定する次工程を残すため、Batch 2では `VERIFIED_OFFICIAL_CURRENT_SCOPE_PENDING` とした。

## 現在の64件分類

| 状態 | 件数 | 意味 |
|---|---:|---|
| PRODUCT_EVIDENCE_PRESENT | 6 | 既存商品stagingあり。公式URL・Human Reviewを進める |
| PRIORITY20_STAGED | 15 | 重点20プロフィールあり。商品単位ニット調査を補完する |
| OFFICIAL_BRAND_VERIFIED_PRODUCT_PENDING | 38 | 公式現行性確認済み。商品単位ニット調査をこれから進める |
| EXCLUDED_MENS_ONLY | 2 | 五大陸 / TAKEO KIKUCHI。現行性確認済みだが今回の商品調査対象外 |
| LEGACY_REBRANDED | 1 | any FAM。ANYへのリブランド履歴 |
| CURRENT_BRAND_IDENTITY_RESOLVED | 1 | ANY。現行ブランドとして確認済み |
| SUBLINE_RESOLVED | 1 | MATINEE LINE。GLOBAL WORK内ラインとして確認済み |

合計64件。

## 商品78件の内訳

- GLOBAL WORK: 23
- ROPÉ PICNIC: 22
- DoCLASSE: 20
- Te chichi: 6
- GU: 4
- MUJI: 3

既存78件の多くは `REVIEW_REQUIRED` であり、商品レコードがあるだけでは公式確認完了としない。次工程ではこの78件を先に公式商品URLへ照合し、その後、商品stagingがないブランドへ広げる。

## 次工程

1. 既存78商品を公式商品URLへ照合し、混率・価格・機能・商品状態を商品単位で確定
2. 女性向け範囲保留8ブランドを商品単位で確定
3. 重点20のうち商品stagingがない15ブランドへ女性ニット商品を追加
4. `OFFICIAL_BRAND_VERIFIED_PRODUCT_PENDING` のブランドを企業グループ単位で順次商品調査

## 安全ルール

- メンズ対象外
- 公式サイト優先
- 商品単位の混率・機能をブランド全体へ一般化しない
- 公式確認できない項目は `NOT AVAILABLE` / `REVIEW REQUIRED`
- `ANY` / `any FAM` / `any SiS` は履歴・現行ブランドを区別し、自動統合しない
- `MATINEE LINE` はGLOBAL WORK内ラインとして扱う
- `MUJI` と `MUJI Labo` は別行を維持
