# Photo Capture → Human Review 接続仕様

更新日: 2026-08-05  
版: 1.0.4

## 接続済みの3工程

1. Photo Captureは混率、機能性、サステナブル、共通ID、根拠、確認状態を同じAppend Only DRAFTに保存します。
2. DRAFTは `KC_V04_INBOX_ITEM` としてHuman Review受信箱へ渡します。形式名は既存データ互換のため維持します。
3. Human Reviewで承認した場合だけ、商品・糸・会社・素材・調査マスターへ確定反映します。却下時はマスターを変更しません。

## 保存先と受渡し

- Photo Capture本体: IndexedDB `kc_independent_photo_capture_v1_0`
- 受信箱: localStorage `kc_v04_handoff_queue_v1`
- 正式マスター: localStorage `kc_independent_practical_v0_4`（内部互換キー）
- 同一オリジン・同一ブラウザ: 受信箱を直接共有
- 別サイト・別端末: `KC_V04_INBOX_EXPORT` JSONを書き出し、Human Review側で取り込み
- 外部Production / Core / Company DBへの自動接続: なし

写真Blobは受信箱へ複製しません。受信箱には写真IDとメタデータだけを渡し、容量増加と意図しない画像複製を防ぎます。

## 受信箱項目

- `handoff_id`
- `dedupe_key`（`recordId:eventVersion`）
- `capture_id`
- `event_id`
- `event_version`
- `source_system`
- `sent_at`
- `review_status`（`PENDING` / `APPROVED` / `REJECTED`）
- `payload`

同じDRAFT版を再送しても `dedupe_key` が同じ場合は重複登録しません。UPDATE版は別候補として履歴を保持します。

## 編地仕様の受渡し

Photo Captureの編地入力では、ゲージと本取りを別項目で保持します。

- `payload.gauge`: 例 `12G`
- `payload.knittingEnds`: 例 `2`（1以上の整数または `null`）

資料の `12G×2`、`12G*2`、`12G＊2` は保存時に `gauge: "12G"`、`knittingEnds: 2`へ分離します。本取りは糸の合糸数・撚り本数を示す `plyCount` と混同しません。

同じ端末で編集値を早く復元するため、localStorage `kc_photo_capture_knitting_ends_v1` に補助索引を持ちます。この補助索引は一覧表示と入力復元だけに使用し、正本はIndexedDBのAppend Onlyイベントです。受信箱JSONを書き出した場合も `knittingEnds` はpayload内に保持されます。

## 混率合計の解釈

混率合計は、数値の直後に半角`%`または全角`％`が付いた値だけを対象にします。中国語資料の`粘胶80％ 尼龙20％`、半角表記の`RY80% NY20%`、半角・全角が混在する入力のいずれも同じように計算します。

`TENCEL A100`、`G100`、`70D`、`2/48NM`など、品名・グレード・番手に含まれる数字は混率へ加算しません。

## 受信箱の件数保護

通常の目安は500件ですが、PENDING候補の件数が500件を超えた場合もPENDINGは全件保持します。件数を整理するときは、古いAPPROVED／REJECTED履歴だけを先に削減します。

localStorageの容量不足で保存できない場合は、既存の未承認候補を削除せずエラーを表示します。利用者は受信箱JSONを書き出したうえで容量を整理します。

## 共通ID

正式IDが未作成の場合、Photo Captureは `TMP-` で始まる一時IDを発行します。Human Review承認時に次の正式IDへ自動採番または手入力で確定し、`photoCaptureIdMap` に一時IDと正式IDの対応を保存します。

- 商品: `PR-` + 8桁
- 糸: `YN-` + 8桁
- 会社: `OR-` + 7桁
- 素材: `MT-` + 7桁
- 調査: `RS-` + 10桁

会社対象の `TMP-OR-…` は、最初の承認で確定した正式 `OR-…` IDへ固定します。同じcaptureのUPDATEを後から承認しても、新しい会社IDを発行せず同じ会社マスターを更新します。

## Human Reviewの処理

### 承認

- 確認者名と確認日時を保存
- 一時IDを正式IDへ変換
- 商品、糸、会社をIDでupsert
- 商品と糸が同じ候補に含まれる場合は `linkedYarnIds` で紐付け
- 機能性・サステナブル・混率・根拠をマスターへ反映
- `photoCaptureImports` と `auditLog` に承認記録を追加

### 部分更新時の既存値保護

既存マスターに値があり、今回の受信値が空文字、空配列、nullまたは未確認状態の場合、その項目は変更しません。番手、混率、機能性、サステナブル、URL、メモ、会社IDなどは、今回の候補に明示的な値がある場合だけ更新します。

現時点では空欄を使った「明示的な削除」は行いません。値を削除する必要がある場合は、マスター編集画面で個別に実施します。

### 却下

- 却下理由、確認者、確認日時を受信箱へ保存
- 商品・糸・会社マスターは変更しない

## 自動検証

`scripts/validate_handoff_safety.py` と `Validate Human Review safety` workflowで次を確認します。

- Photo CaptureとHuman Review受信箱のJavaScript構文
- 500件での単純切捨てが残っていないこと
- PENDING保持ロジック
- 空欄上書き防止ロジック
- 会社一時IDと正式IDの固定
- 半角`%`、全角`％`、混在入力での混率合計
- `TENCEL A100`や`G100`の数字を混率へ誤加算しないこと
- 本取り入力がapp.jsの後に読み込まれ、`knittingEnds`をDRAFTと受信箱payloadへ保持すること

## 会社スプレッドとの運用境界

- 業務データの主系統はKnit Compassとし、会社スプレッドを正本にしない
- 会社スプレッドへ出すCSVは必要最小項目の `BACKUP_SHARE_ONLY` とする
- CSVには `source_of_truth: KNIT_COMPASS` と `automatic_import_to_master: FORBIDDEN` を含める
- 会社シートからKnit Compassマスターへの自動取込、既存行上書き、自動公開を行わない
- 端末内監査JSONは全payloadを含み得るため、会社共有前に内容をHuman Reviewする

## 安全条件

- PENDING候補を確定値として表示・利用しない
- AI推定、Supplier主張、資料確認、試験確認を同じ確認状態にしない
- 空欄で既存の確認済みマスター値を消さない
- 同じ会社一時IDから会社マスターを重複作成しない
- 件数制限でPENDING候補を削除しない
- 同一IDに異なる対象を上書きしない
- 接続先を暗黙に外部DBへ変更しない
- 正式な一元DBを導入するまでは、ブラウザ内マスターを全社正本と誤認しない

## 承認保存の一体性

Human Review承認では、マスター更新と受信箱のAPPROVED更新を一組として保存します。どちらかのlocalStorage書込みが失敗した場合は、保存前の両方の値へ復元し、PENDINGのまま再確認できる状態を維持します。

同じPhoto Captureイベント版は一度だけ受信箱へ送信でき、送信後のボタンは無効化します。保存・承認ボタンも処理中は無効化して二重実行を防止します。
