# Knit Compass 共通ID・データ項目定義

更新日: 2026-08-03  
版: 1.0.0

## 1. 基本原則

- 同じ情報を複数画面で別々に確定しない
- 各情報には「正本となるマスター」を一つだけ決める
- Photo Captureは写真と撮影時情報を保持し、商品・糸・会社の確定情報は各マスターから参照する
- 不明情報を空欄のまま放置せず、確認状態を必ず保持する
- AIの推定値と確認済み事実を同じ値として扱わない

## 2. 共通ID

| 対象 | キー | 推奨形式 | 例 |
|---|---|---|---|
| ブランド | `brand_id` | `BR-` + 5桁 | `BR-00058` |
| 商品 | `product_id` | `PR-` + 8桁 | `PR-00001234` |
| 糸 | `yarn_id` | `YN-` + 8桁 | `YN-00000482` |
| 会社・組織 | `organization_id` | `OR-` + 7桁 | `OR-0000123` |
| 素材・原料 | `material_id` | `MT-` + 7桁 | `MT-0000315` |
| 写真 | `photo_id` | `PH-` + 10桁 | `PH-0000001024` |
| 調査記録 | `research_id` | `RS-` + 10桁 | `RS-0000000482` |
| 根拠資料 | `evidence_id` | `EV-` + 10桁 | `EV-0000000159` |

IDは名称変更、URL変更、会社名の表記揺れがあっても変更しません。

## 3. 正本となるマスター

### 3.1 ブランドマスター

主キー: `brand_id`

主な項目:

- `brand_name_official`
- `brand_name_display`
- `official_site_url`
- `operating_company_id`
- `country_code`
- `active_status`

### 3.2 商品マスター

主キー: `product_id`

正本項目:

- `brand_id`
- `manufacturer_product_code`
- `product_name`
- `product_url`
- `regular_price`
- `sale_price`
- `currency`
- `color`
- `size`
- `product_composition_label`
- `country_of_origin`
- `release_status`
- `confirmed_at`

`product_url`は原則として商品詳細の公式URLを保存し、ブランド一覧URLや検索結果URLで代用しません。

### 3.3 糸マスター

主キー: `yarn_id`

正本項目:

- `yarn_name`
- `supplier_product_code`
- `yarn_count_value`
- `yarn_count_system`
- `yarn_count_display`
- `yarn_composition`
- `basic_yarn_form`
- `yarn_structure`
- `spinning_system`
- `spinning_method`
- `twisting_method`
- `processing_method`
- `recommended_gauge`
- `functional_properties`
- `sustainable_attributes`
- `manufacturer_organization_id`
- `seller_organization_id`

番手は、値・体系・表示を分けます。例:

```json
{
  "yarn_count_value": "30/2",
  "yarn_count_system": "Nm",
  "yarn_count_display": "2/30 Nm"
}
```

表示順の変更が必要でも、元の値を破壊しません。

### 3.4 会社・組織マスター

主キー: `organization_id`

正本項目:

- `organization_name_official`
- `organization_name_local`
- `organization_role`
- `country_code`
- `province_or_state`
- `official_url`
- `verification_status`

`organization_role`は複数可とし、最低限次を区別します。

- `raw_material_manufacturer`
- `yarn_manufacturer`
- `processor`
- `seller`
- `trading_company`
- `brand_operator`
- `unknown`

販売会社が原料メーカーを把握していない場合、メーカーとして確定せず `seller` として登録します。

### 3.5 写真マスター

主キー: `photo_id`

正本項目:

- `file_reference`
- `captured_at`
- `captured_by`
- `photo_category`
- `orientation_corrected`
- `target_type`
- `target_id`
- `source_organization_id`
- `document_type`
- `season`

`target_type`は `product`、`yarn`、`material`、`organization`、`research` のいずれかとし、`target_id`に対応する共通IDを入れます。

### 3.6 調査記録

主キー: `research_id`

正本項目:

- `target_type`
- `target_id`
- `research_question`
- `ai_tool`
- `candidate_answer`
- `verified_facts`
- `inferences`
- `open_questions`
- `review_status`
- `reviewed_by`
- `reviewed_at`

## 4. 商品と糸の関係

商品と糸は直接上書きせず、関係テーブル `product_yarn_link` で結びます。

必須項目:

- `product_id`
- `yarn_id`
- `usage_position`（身頃、衿、プレーティング、芯糸など）
- `adoption_status`（候補、確認済み、否定）
- `evidence_id`
- `confidence_level`
- `confirmed_at`

これにより、一商品に複数糸、一糸に複数商品を安全に紐付けできます。

## 5. 機能性・サステナブル項目

### 機能性

`functional_properties`は複数選択とし、各機能に以下を持たせます。

- `function_code`
- `function_name`
- `claim_status`
- `test_method`
- `test_value`
- `evidence_id`

`claim_status`:

- `supplier_claim`
- `document_confirmed`
- `test_confirmed`
- `not_confirmed`

### サステナブル

`sustainable_attributes`も複数選択とし、曖昧な「サステナブル」の一語だけで確定しません。

- `attribute_code`
- `attribute_name`
- `basis`（再生原料、認証、バイオベース、トレーサビリティ等）
- `certification_or_standard`
- `evidence_id`
- `verification_status`

## 6. 確認状態

全ての重要項目に `verification_status` を持たせます。

| 値 | 意味 |
|---|---|
| `confirmed` | 一次情報または十分な根拠で確認済み |
| `candidate` | 有力候補だが未承認 |
| `inferred` | 構造・混率等からの推定 |
| `unconfirmed` | 未確認 |
| `conflicting` | 情報源同士が矛盾 |
| `not_applicable` | 対象外 |

画面では `candidate` と `inferred` を確定値と同じ色・表示にしてはいけません。

## 7. 根拠情報

重要項目を確定する際は、最低限次を保存します。

- `source_url` またはファイル参照
- `source_type`
- `source_title`
- `checked_at`
- `checked_by`
- `quoted_or_observed_fact`
- `evidence_id`

## 8. 最低限の入力チェック

### 商品

- `brand_id`必須
- `product_name`必須
- `product_url`またはURL未取得理由を必須
- 公式URLかどうかを記録

### 糸

- `yarn_name`または仮称必須
- 番手体系と番手値を分離
- 混率合計が100%でない場合は警告
- メーカーと販売会社を別項目で保持
- 糸構造が未確認の場合は `unconfirmed` を明示

### 写真

- `photo_category`必須
- `target_type`と`target_id`を両方必須
- 紐付け先が未作成の場合は一時IDを発行し、未連携一覧へ表示

## 9. 未連携一覧の共通判定

次の条件をダッシュボードで件数表示します。

- 商品URLなし
- 商品混率未確認
- 糸ID未連携
- 糸構造未確認
- メーカー未確認
- 販売会社未確認
- 機能性根拠なし
- サステナブル根拠なし
- 写真の紐付け先なし
- Human Review未完了

これらはエラーで削除せず、改善対象として追跡します。
