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

## 公式確認 Batch 1

2026-08-08に24件を現行公式サイトで確認し、`data/brand-research/2026-08-08-official-verification-batch1.csv` に固定した。

対象: UNIQLO / GU / MUJI / ROPÉ PICNIC / VIS / GLOBAL WORK / LOWRYS FARM / studio CLIP / niko and ... / earth music&ecology / Green Parks / OPAQUE.CLIP / index / SHOO・LA・RUE / grove / ikka / DoCLASSE / any SiS / any FAM / Te chichi / ANY / MATINEE LINE / ROPÉ / ADAM ET ROPÉ。

### 同一性レビューの解決

- `BR-00059 ANY`: 現行の独立ブランドとして公式確認。`any FAM` から `ANY` へのリブランド履歴を保持する。
- `BR-00020 any FAM`: 現行成人ブランドとして追わず `LEGACY_REBRANDED`。履歴行は削除しない。
- `BR-00061 MATINEE LINE`: GLOBAL WORK公式内の女性向けラインとして確認。`SUBLINE_RESOLVED` とし、独立ブランド集計から分離する。

64ブランド正本自体は履歴・監査のため上書きせず、今回の進捗表で現行状態を表現する。

## 現在の64件分類

| 状態 | 件数 | 意味 |
|---|---:|---|
| PRODUCT_EVIDENCE_PRESENT | 6 | 商品stagingが既にある。URL/公式根拠をHuman Reviewする |
| PRIORITY20_STAGED | 15 | 重点20に基本プロフィールはあるが商品stagingはない |
| MASTER_ONLY_UNCHECKED | 38 | 64件原本にはあるが今回の重点20・商品78件に未接続 |
| EXCLUDED_MENS_ONLY | 2 | 五大陸 / TAKEO KIKUCHI。今回の「メンズ対象外」運用により調査対象外 |
| LEGACY_REBRANDED | 1 | any FAM。ANYへのリブランド履歴として保持 |
| CURRENT_BRAND_IDENTITY_RESOLVED | 1 | ANY。現行ブランドとして公式確認済み |
| SUBLINE_RESOLVED | 1 | MATINEE LINE。GLOBAL WORK内ラインとして確認済み |

合計64件。24件は `official_current_verified=YES`。

## 商品78件の内訳

- GLOBAL WORK: 23
- ROPÉ PICNIC: 22
- DoCLASSE: 20
- Te chichi: 6
- GU: 4
- MUJI: 3

商品レコードが存在することと、公式根拠確認済みは別扱いとする。既存78件には `REVIEW_REQUIRED` が多いため、件数だけで「ブランド調査完了」としない。

## 次の調査順

1. `PRODUCT_EVIDENCE_PRESENT` 6ブランドの既存78商品を公式商品URLへ照合
2. 公式確認済みだが商品stagingのない重点ブランドの女性向けニットを商品単位で補完
3. `MASTER_ONLY_UNCHECKED` 38件から、女性向けニット対象を企業グループ単位で公式確認
4. メンズ専業2件は母数には残し、今回の調査実働から除外

## 安全ルール

- メンズ対象外
- 公式サイト優先
- 商品単位の混率・機能をブランド全体へ一般化しない
- 公式確認できない項目は `NOT AVAILABLE` / `REVIEW REQUIRED`
- `ANY` / `any FAM` / `any SiS` は履歴・現行ブランドを区別し、自動統合しない
- `MATINEE LINE` はGLOBAL WORK内ラインとして扱う
- `MUJI` と `MUJI Labo` は別行を維持
