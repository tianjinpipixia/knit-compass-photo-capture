# Knit Compass 共通ID・データ項目定義

更新日: 2026-08-09
版: 1.2.0

## 1. 基本原則

- 同じ情報を複数画面で別々に確定しない
- Photo Captureは写真と撮影時情報をDRAFTとして保持する
- 商品・糸・会社の確定情報はHuman Review承認後に各マスターへ反映する
- AI推定、Supplier主張、資料確認、試験確認を同じ状態として扱わない
- 名称やURLが変わっても共通IDは変更しない
- 不明情報は空欄だけで放置せず確認状態を持たせる

## 2. 共通ID

| 対象 | キー | 形式 | 例 |
|---|---|---|---|
| ブランド | `brand_id` | `BR-` + 5桁 | `BR-00058` |
| 商品 | `product_id` | `PR-` + 8桁 | `PR-00001234` |
| 糸 | `yarn_id` | `YN-` + 8桁 | `YN-00000482` |
| 会社・組織 | `organization_id` | `OR-` + 7桁 | `OR-0000123` |
| 素材・原料 | `material_id` | `MT-` + 7桁 | `MT-0000315` |
| 写真 | `photo_id` | `PH-` + 10桁 | `PH-0000001024` |
| 調査記録 | `research_id` | `RS-` + 10桁 | `RS-0000000482` |
| 根拠資料 | `evidence_id` | `EV-` + 10桁 | `EV-0000000159` |

マスター未作成の場合、Photo Captureは `TMP-<種別>-<UUID>` の一時IDを発行します。Human Review承認時に正式IDへ変換し、`photoCaptureIdMap` に対応関係を保存します。

## 3. Photo Capture DRAFT

主キー: `captureId`

必須または主要項目:

- `dataContractVersion`
- `captureId`
- `targetType`
- `targetId`
- `commonIds.productId`
- `commonIds.yarnId`
- `commonIds.materialId`
- `commonIds.researchId`
- `sourceOrganizationName` / `sourceOrganizationId`
- `manufacturerName` / `manufacturerId`
- `sellerName` / `sellerId`
- `brandName`
- `productName` / `productCode` / `productUrl`
- `yarnName` / `yarnCode`
- `countSystem` / `countValue` / `countDisplay`
- `gauge` / `knittingEnds`
- `basicYarnForm` / `yarnStructure`
- `spinningMethod` / `processingMethod`
- `compositionRaw` / `compositionTotal` / `compositionStatus`
- `functionalProperties`
- `sustainableAttributes`
- `verificationStatus`
- `evidenceId`
- `sourceType` / `sourceUrl`
- `photoRefs`
- `notes`

Photo CaptureのイベントはAppend Onlyとし、`CREATE` と `UPDATE` の全版を残します。

### 編地のゲージと本取り

ゲージと本取りは別項目として保持します。

| 項目 | 型 | 例 | 意味 |
|---|---|---|---|
| `gauge` | string | `12G` | 使用した、または推奨される編機ゲージ |
| `knittingEnds` | positive integer / null | `2` | 編成時に同時給糸する糸の本数 |

資料に `12G×2`、`12G*2`、`12G＊2` と記載されている場合は、`gauge: "12G"` と `knittingEnds: 2` に分離します。`knittingEnds` は糸そのものの撚り本数・合糸数を示す `plyCount` とは別概念です。

Photo Captureは `knittingEnds` をIndexedDBのDRAFTイベントとv0.4受信箱payloadへ保持します。画面の補助用localStorageは復元と一覧表示のためだけに使用し、正本はIndexedDBイベントとします。

## 4. 正本マスター

### 商品マスター

主キー: `product_id`

- `brand_id`
- `manufacturer_product_code`
- `product_name`
- `product_url`
- `product_composition_label`
- `functional_properties`
- `sustainable_attributes`
- `country_of_origin`
- `release_status`
- `confirmed_at`

### 糸マスター

主キー: `yarn_id`

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

番手は値・体系・表示を分けます。表示順を変更しても元の値を破壊しません。

### 会社・組織マスター

主キー: `organization_id`

- `organization_name_official`
- `organization_name_local`
- `organization_role`
- `official_url`
- `organization_type`
- `country`
- `website`
- `founded_year`
- `organizationProfile`
- `verification_status`

`organization_role` は複数可とし、原料メーカー、糸メーカー、加工会社、販売会社、商社、ブランド運営会社、入手先、未確認を区別します。販売会社が原料メーカーを把握していない場合、メーカーとして確定しません。

`organizationProfile` はHuman Reviewで根拠を確認した会社情報を保持する拡張領域です。連絡先、所在地、事業情報、根拠、関連素材・資料、他組織との関係を含められます。関係先が `relatedOrganizationTempId` で渡された場合、関係する組織が承認された時点で対応する正式IDを `relatedOrganizationId` に追記します。一時IDや資本関係未確認という状態も削除せず保持します。

### 写真マスター

主キー: `photo_id`

- `file_reference`
- `captured_at`
- `captured_by`
- `photo_category`
- `target_type`
- `target_id`
- `source_organization_id`
- `document_type`
- `season`

### 調査記録

主キー: `research_id`

- `target_type`
- `target_id`
- `research_question`
- `candidate_answer`
- `verified_facts`
- `inferences`
- `open_questions`
- `review_status`
- `reviewed_by`
- `reviewed_at`

## 5. 商品と糸の関係

商品と糸は直接上書きせず、関係情報で結びます。

- `product_id`
- `yarn_id`
- `usage_position`
- `adoption_status`
- `evidence_id`
- `confidence_level`
- `confirmed_at`

v0.4では承認済み候補を商品側の `linkedYarnIds` に保持します。

## 6. 機能性

`functionalProperties` は複数選択とし、各項目に次を持たせます。

- `code`
- `name`
- `verification_status` または `claim_status`
- `detail`
- `test`
- `evidence_id`

確認状態:

- `not_confirmed`
- `supplier_claim`
- `document_confirmed`
- `test_confirmed`

## 7. サステナブル

`sustainableAttributes` も複数選択とし、曖昧な「サステナブル」の一語だけで確定しません。

- `code`
- `name`
- `detail` または `basis`
- `certification`
- `evidence_id`
- `verification_status`

対象例は再生原料、バイオベース、認証セルロース、トレーサビリティ、環境負荷低減です。

## 8. 共通の確認状態

| 値 | 意味 |
|---|---|
| `confirmed` | 一次情報または十分な根拠で確認済み |
| `candidate` | 有力候補だが未承認 |
| `inferred` | 構造・混率等からの推定 |
| `unconfirmed` | 未確認 |
| `conflicting` | 情報源同士が矛盾 |
| `not_applicable` | 対象外 |

候補・推定を確定値と同じ色や表示にしません。

## 9. v0.4受信箱

Photo Captureからv0.4へ渡す候補は `KC_V04_INBOX_ITEM` とします。

- `handoff_id`
- `dedupe_key`
- `capture_id`
- `event_id`
- `event_version`
- `source_system`
- `sent_at`
- `review_status`
- `payload`

`review_status` は `PENDING`、`APPROVED`、`REJECTED` のいずれかです。同一版は `dedupe_key` で重複防止します。別端末用の書き出し形式は `KC_V04_INBOX_EXPORT` です。

## 10. Human Review

### APPROVED

- 確認者と確認日時を保存
- 一時IDを正式IDへ変換
- 商品・糸・会社・素材・調査マスターをIDでupsert
- 商品と糸を紐付け
- `photoCaptureImports` と `auditLog` を追加
- 番手・混率・ゲージ・構造・機能性・サステナブルは、資料確認済み等の根拠状態がある項目だけを確定値として反映
- `ai_candidate`、`inferred`、`candidate`、`unconfirmed` の項目は既存マスターへ確定値として反映しない
- 会社対象は `organizationProfile` を保持し、承認済み会社間の一時関係IDを正式組織IDへ解決

### REJECTED

- 却下理由、確認者、確認日時を保存
- マスターは変更しない

## 11. 最低限の入力チェック

- 混率の数値合計が100%でない場合は警告
- メーカーと販売会社を別項目で保持
- 糸構造未確認の場合は `unconfirmed` を明示
- 編地の本取りは1以上の整数または未入力とし、ゲージ欄の末尾にある `×本数` 表記は分離する
- 写真は `targetType` と `targetId` を持つ
- 共通ID未作成の場合は一時IDを発行
- Human Review前の候補をマスターへ確定反映しない

## 12. 未連携一覧の共通判定

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

これらは削除対象ではなく改善対象として追跡します。

## 13. 月次掲載観測とMD提案

### 月次掲載観測

主キー: `observation_id`

- `month`
- `brand`
- `totalListings`
- `newListings`
- `saleListings`
- `observedAt`
- `sourceUrl`
- `salesQuantityStatus`
- `salesQuantity`
- `salesQuantityEvidence`
- `method`
- `estimationPolicy`

掲載数は公式掲載面を人が数えた観測値として保存し、販売数量とは区別します。販売数量を取得できない場合は `salesQuantityStatus: NOT_AVAILABLE`、`salesQuantity: null` とし、推定値を補いません。販売数量を保存できるのは `EVIDENCE_PROVIDED` かつ数量と根拠参照を同時に入力した場合だけです。

### MD提案

主キー: `proposal_id`

- `sourceObservationId`
- `observationSnapshot`
- `status`: `DRAFT` / `REVIEW` / `PUBLISH_HOLD`
- `publicationStatus`: `HOLD`
- `mdDecision`
- `theme`
- `rationale`
- `nextAction`
- `estimationPolicy`: `NO_SALES_ESTIMATION`

MD提案は月次掲載観測へ必ず紐付けます。観測に根拠付き販売数量がない場合、提案側にも数量を生成しません。作成時は必ず公開保留とし、自動公開・自動マスター反映を行いません。

## 14. 糸から編み地イメージ

`KC-YARN-KNIT-IMAGE` は次の2データ源を読取専用で参照します。

- V04糸マスター: localStorage `kc_independent_practical_v0_4` の `yarns`
- 2,000件カタログ: `data/yarn-catalog/mz100-catalog-2000.json`。状態は `CATALOG_INDEXED / LISTING_PAGE_ONLY / NOT_PROMOTED`

選択糸から `id`、`source`、`name`、`supplier`、`code`、`count`、`composition`、`structure`、`gauge`、`status` を表示用に引き継ぎます。編み条件は `gauge`、`knitStructure`、`knittingEnds`、`color` を別々に扱い、`knittingEnds` を糸の合糸数・撚り本数から推定しません。

出力は `GENERATED_REFERENCE` 相当の検討用Canvas／PNGです。実編み、色、風合い、物性、Supplier仕様の根拠には昇格させません。生成処理はマスター、受信箱、IndexedDB、顧客共有スナップショットへ書き込まず、外部AI/APIへ糸情報を送信しません。
