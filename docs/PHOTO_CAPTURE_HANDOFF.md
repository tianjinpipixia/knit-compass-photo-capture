# Photo Capture → v0.4 → Human Review 接続仕様

更新日: 2026-08-04  
版: 1.0.0

## 接続済みの3工程

1. Photo Captureは混率、機能性、サステナブル、共通ID、根拠、確認状態を同じAppend Only DRAFTに保存します。
2. DRAFTは `KC_V04_INBOX_ITEM` としてv0.4の受信箱へ渡します。
3. Human Reviewで承認した場合だけ、商品・糸・会社・素材・調査マスターへ確定反映します。却下時はマスターを変更しません。

## 保存先と受渡し

- Photo Capture本体: IndexedDB `kc_independent_photo_capture_v1_0`
- 受信箱: localStorage `kc_v04_handoff_queue_v1`
- v0.4マスター: localStorage `kc_independent_practical_v0_4`
- 同一オリジン・同一ブラウザ: 受信箱を直接共有
- 別サイト・別端末: `KC_V04_INBOX_EXPORT` JSONを書き出し、v0.4側で取り込み
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

## 共通ID

正式IDが未作成の場合、Photo Captureは `TMP-` で始まる一時IDを発行します。Human Review承認時に次の正式IDへ自動採番または手入力で確定し、`photoCaptureIdMap` に一時IDと正式IDの対応を保存します。

- 商品: `PR-` + 8桁
- 糸: `YN-` + 8桁
- 会社: `OR-` + 7桁
- 素材: `MT-` + 7桁
- 調査: `RS-` + 10桁

## Human Reviewの処理

### 承認

- 確認者名と確認日時を保存
- 一時IDを正式IDへ変換
- 商品、糸、会社をIDでupsert
- 商品と糸が同じ候補に含まれる場合は `linkedYarnIds` で紐付け
- 機能性・サステナブル・混率・根拠をマスターへ反映
- `photoCaptureImports` と `auditLog` に承認記録を追加

### 却下

- 却下理由、確認者、確認日時を受信箱へ保存
- 商品・糸・会社マスターは変更しない

## 安全条件

- PENDING候補を確定値として表示・利用しない
- AI推定、Supplier主張、資料確認、試験確認を同じ確認状態にしない
- 同一IDに異なる対象を上書きしない
- 接続先を暗黙に外部DBへ変更しない
- 正式な一元DBを導入するまでは、ブラウザ内マスターを全社正本と誤認しない
