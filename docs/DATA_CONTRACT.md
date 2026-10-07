# Knit Compass 共通ID・データ項目定義

更新日: 2026-10-07
版: 1.3.0

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

Photo Captureは `knittingEnds` をIndexedDBのDRAFTイベントとHuman Review受信箱payloadへ保持します。画面の補助用localStorageは復元と一覧表示のためだけに使用し、正本はIndexedDBイベントとします。

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

商品調査・Human Reviewでは承認済み候補を商品側の `linkedYarnIds` に保持します。

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

## 9. Human Review受信箱（内部互換形式V04）

Photo CaptureからHuman Reviewへ渡す候補は `KC_V04_INBOX_ITEM` とします。形式名は既存データ互換のため変更しません。

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

- 正式糸マスター: localStorage `kc_independent_practical_v0_4` の `yarns`（内部互換キー）
- 現行3,000件カタログ: `data/yarn-catalog/mz100-catalog-3000.json`。状態は `CATALOG_INDEXED / LISTING_PAGE_ONLY / NOT_PROMOTED`
- 安全な予備索引: `data/yarn-catalog/mz100-catalog-2000.json`。3,000件成果物を読み込めない場合だけ使用

選択糸から `id`、`source`、`name`、`supplier`、`code`、`count`、`composition`、`structure`、`gauge`、`status` を表示用に引き継ぎます。編み条件は `gauge`、`knitStructure`、`knittingEnds`、`color` を別々に扱い、`knittingEnds` を糸の合糸数・撚り本数から推定しません。

出力は `GENERATED_REFERENCE` 相当の検討用Canvas／PNGです。実編み、色、風合い、物性、Supplier仕様の根拠には昇格させません。生成処理はマスター、受信箱、IndexedDB、顧客共有スナップショットへ書き込まず、外部AI/APIへ糸情報を送信しません。

## Brand64直接収集 v2：速報・確認範囲・詳細キュー

- `known-products.json` のキー `brand_id|product_url` と `first_seen_date` を維持する。未取得日に既存商品を削除せず、初回発見を発売日へ転記しない。
- `flash-history.json` は初回発見・観測項目変更・対象判定待ちを保持し、`flash-latest.json` は当日のイベントを速報として出力する。候補は公開保留。対象未判定リンクを確認済み商品件数へ含めない。
- `coverage-state.json` はブランドIDごとに `observed_date`、`last_attempt_at_utc`、`successful_page_urls`、`attempted_page_urls`、`pending_page_urls`、`errors`、観測商品、取得元を保持。前日の残URLは成功するまで持ち越す。前日取得した商品を当日取得数に加算しない。
- `deep-dive-queue.json` と `detail-results.json` は速報とは別。詳細未確認でも速報は保存する。既知商品への新たな自動確定・顧客公開は行わない。
- `latest.json` schema 2.0 の `complete_brand_count` は当日・入口・新着/予約/ニット/カーディガンの範囲監査・残件なしを満たすブランド数。`product_observed_brand_count` は商品を取得したブランド数。両者を混同しない。39ブランドによる成功閾値は廃止。
- 全64ブランドの `brands[].coverage.reasons` を保持する。未確認／未取得／未解析／範囲検証待ちは変更なしではない。範囲監査は実際の公式根拠がある場合のみ設定する。
- 複数ファイルにまたがる完全なトランザクションではないため、速報履歴を商品台帳より先に原子的に保存し、再実行は既知キーで重複を防ぐ。破損JSONは空に置換せず処理を失敗させる。

- `feed.json` (`KC_BRAND64_OWNER_FLASH` 1.0) は `summary`（上記2.0）、当日 `candidates`、`deep_dive_pending_count` を1ファイルで提供する。V04は形式・ブランドID重複・観測日を検証し、取得失敗時に0件へ置き換えない。`brand64/flash-feed` には既知台帳と回復用状態もまとめて1コミットで保存し、次回日次処理の復元元とする。公開済みの公式情報に限定し、顧客・会社・個人の非公開データを追加しない。


## 15. Owner Yarn候補の項目別確認と証拠保持

Human Reviewの `APPROVED` はレビュー・登録の完了であり、全項目の `confirmed` を意味しません。未確認の新規糸は `status: CANDIDATE` / `verificationStatus: candidate` で登録し、既存の確認済みレコードを候補入力で降格・消去しません。保留は受信箱をPENDINGのまま保持し、マスターも受信箱も書き換えません。

番手・撚り本数・構造・加工等は `fieldEvidence.<payload項目名>` の `status: confirmed` と非空の `evidenceId` によって個別に反映できます。明示された未確認・矛盾状態は全体の確認状態より優先します。個別証拠がない従来入力は既存の全体確認条件を使います。`ai_candidate` は個別状態に関わらず確定仕様へ反映しません。

機能・サステナブルは名称、許可された `verification_status`、`evidence_id` を持つオブジェクトを反映します。機能の `supplier_claim` は主張の記録であり試験確認ではありません。状態のない文字列・証拠参照のないオブジェクトは確定タグにせず、元入力として保持します。

糸と素材レコードの `intakeEvidence` は承認した元payload全体をイベント版ごとに追記します。元notes、fieldEvidence、未確認仕様、主張、名称矛盾も保持します。同じhandoff・同じ版は証拠を重複追加せず、新しい版は既存版を消しません。

QYSMART-COMFYは、40s/1基糸の `yarnComposition`（VIS80/PET10/functional10、原料名矛盾あり）と、完成生地の `fabricComposition`（基糸95%＋20D PU5%）を別レベルとして保持します。これらは `intakeEvidence` に残し、名前の矛盾が解消するまで糸の確定 `composition` や素材組成にコピーしません。アクリレートと改質アクリルの同一性、法定原料名、紡績方式、正確な染色方法は未確認です。

素材の独立登録には `materialName`、`materialEvidenceId`、`materialVerificationStatus: confirmed` がすべて必要です。`commonIds.materialId` と糸名だけでは登録・ID解決しません。素材組成・機能は素材専用の `materialCompositionRaw` / `materialCompositionStatus`、`materialFunctionalProperties`、`materialSustainableAttributes` を使い、糸・生地の値を流用しません。独立確認のない素材を主対象にした承認は保存前に止まり、PENDINGを保持します。

### 既承認データの調査方針（読取のみ）

既存ブラウザのデータ・承認履歴はこの変更で自動走査、移行、削除、再承認しません。調査が必要な場合は、ユーザーが明示的に書き出した受信箱とマスターのコピーを読取り、captureId / sourceCaptureId / handoffId / eventVersion とID mapで突合します。候補payloadから確認済み糸・素材になった記録、文字列機能と欠落タグ、混率レベル混在を疑いとして列挙します。欠損履歴では影響を断定せず、修復や再承認は別途レビューを要します。

機能・サステナブルの追加入力は既存項目とマージし、同じ名称またはコードの弱い根拠で既存の試験・資料確認を置き換えません。無関係な既存タグも消去しません。


項目別のfieldEvidenceは、当該payload項目の値を実際に採用した場合だけ更新します。AI由来、空欄、未確認・矛盾する項目の根拠は既存確定値の根拠と置き換えず、intakeEvidenceに元入力として残します。旧形式でyarnStructureが空欄または未確認語だけの場合は、根拠条件を満たすbasicYarnFormをstructureの表示に使います。意味のある未確認yarnStructureから勝手にfallbackして確定させません。

糸のnoteEntriesは元メモ全文を各一要素として保持し、notesはそれらを空行で結んだ表示値とします。同じ元メモの再送は一度だけ保持し、元メモ内の段落は分割・削除しません。旧レコードのnotesはそのまま一要素として保全します。元入力履歴から全文を完全一致で再構成できる場合だけ、その元メモ単位を利用します。
