# Knit Compass システム接続台帳

更新日: 2026-08-04  
版: 1.3.0  
状態: **暫定正本**

## 1. 接続済みフロー

次の5工程を実データで接続しています。

1. Photo Captureが混率・機能性・サステナブル・共通ID・根拠・確認状態をAppend Only DRAFTとして保持
2. Photo CaptureのDRAFTをv0.4の受信箱へ候補送信
3. Human Review承認後だけ商品・糸・会社・素材・調査マスターへ確定反映
4. 顧客共有管理で、確認済み／PUBLISHEDかつ所有者が明示承認した安全項目だけをSTYLEMスナップショットへ発行
5. STYLEM領域からの調査・商品追加・修正依頼を、マスターを直接変更せず専用リクエストとして戻す

PENDING候補とREJECTED候補はマスターへ反映しません。DRAFT／REVIEW、未確認商品、社内研究メモ、開発仮説、糸の価格・MOQ・納期・注意事項はSTYLEM領域へ発行しません。外部Production / Core / Company DBへの自動接続も追加していません。

## 2. 現在の接続状況

| system_id | 画面・アプリ | 環境 | 表示版 | コード正本・Revision | データ保存先 | 同期・受渡し | 外部DB | 状態 |
|---|---|---|---|---|---|---|---|---|
| `KC-PHOTO-CAPTURE` | Photo Capture | 独立Sandbox | `v1.2.2` | `app.js@main` / `git-blob:eb4be9528af1…`。補助: `app.css` / `3fa9acda…`、`app-state-guard.js` / `8f42d047…`、`index.html` / `d42039b9…`、`backup.js` / `5f7dee4a…` | IndexedDB `kc_independent_photo_capture_v1_0`、sessionStorage `kc_session_v1`・`kc_photo_capture_editor_draft_v1`、受信箱localStorage `kc_v04_handoff_queue_v1` | 同一ブラウザ受信箱＋手動JSON / PENDINGを全件保持し確認済み履歴から整理 / 送信失敗時もDRAFT維持 | なし | 稼働中 |
| `KC-V04-WEB` | Knit Compass 独立実用版 v0.4 | 独立運用 | `v0.4.5` | 本体 `brand-intelligence/app.html` / `52f174f3…`。Human Review入口 `brand-intelligence/index.html` / `81927bcd…`。SW `7c5dc989…` | localStorage `kc_independent_practical_v0_4`、受信箱 `kc_v04_handoff_queue_v1` | 候補受信、JSON取込、既存値保護付きHuman Review反映、承認結果の一体保存 | Production / Core / Company DBへの自動接続なし | 稼働中 |
| `KC-CUSTOMER-SHARING-ADMIN` | 顧客共有管理 | 同一オリジン・所有者ローカルPilot | `v1.0.0` | `customer-sharing/index.html` / `2bc2bffc…`、共有ポリシー `customer-sharing/policy.js` / `9202562e…` | マスター `kc_independent_practical_v0_4`、共有承認 `kc_customer_sharing_v1`、STYLEM安全スナップショット `kc_customer_portal_STYLEM_v1`、顧客依頼 `kc_customer_requests_v1` | 所有者明示承認 → 安全項目スナップショット発行／共有取消／顧客依頼回答 | 自動接続なし | Pilot |
| `KC-STYLEM-PORTAL` | STYLEM Customer Area | 同一オリジン・顧客ローカルPilot | `v1.0.0` | `stylem/index.html` / `fddeb899…`、共有ポリシー `customer-sharing/policy.js` / `9202562e…` | STYLEM安全スナップショット `kc_customer_portal_STYLEM_v1`、顧客依頼 `kc_customer_requests_v1` | 承認済みスナップショット閲覧／顧客リクエスト送信。マスター直接更新なし | 自動接続なし | Pilot |
| `KC-DAILY-WEB` | Dailyショートカット版 | 独立運用 | `v0.4` | `daily/index.html@main` / `a7d85f1b…` | v0.4と同じlocalStorage | 所有者設定時のみ手動 | 自動接続なし | 稼働中 |
| `KC-DAILY-ANDROID` | Androidアプリ | 独立APK | `v0.4.0` | `android-daily@main` / `content-sha256:21ff2fd0…` | Android WebViewアプリデータ | 所有者設定時のみ手動 | 自動接続なし | 稼働中 |

## 3. Photo Captureからv0.4への受渡し

### 同一ブラウザ・同一オリジン

Photo CaptureはlocalStorage `kc_v04_handoff_queue_v1` に `KC_V04_INBOX_ITEM` を追加し、v0.4のHuman Review受信箱が同じキーを読み取ります。

### 別サイト・別端末

Photo Captureで `KC_V04_INBOX_EXPORT` JSONを書き出し、v0.4の「受信箱JSONを取込」で読み込みます。

写真Blobは受信箱へ複製しません。写真ID、分類、ファイル名、撮影日時だけを候補へ含めます。

### 入力途中の復元

Photo Captureの入力途中フォームはsessionStorage `kc_photo_capture_editor_draft_v1` に保持します。写真Blobは保存せず、画面を開き直したときは文字・選択項目だけを復元し、写真は再選択を案内します。

### 受信箱の件数管理

- PENDING候補は500件を超えても全件保持します。
- 上限調整が必要な場合は、古いAPPROVED／REJECTED履歴から先に整理します。
- localStorageの容量不足時は、未承認候補を削除せず保存失敗として表示します。
- 受信箱送信に失敗しても、IndexedDBへ保存済みのDRAFTは維持し、一覧から再送できます。

## 4. Human Review後の確定処理

承認時は一時IDを正式IDへ変換し、次をIDでupsertします。

- 商品マスター
- 糸マスター
- 会社・組織マスター
- 素材マスター
- 調査記録
- 商品と糸の紐付け

### 既存マスター保護

部分的なPhoto Captureを既存IDへ承認する場合、受信値が空文字、空配列、null、未確認状態であれば、既存の番手、混率、機能性、サステナブル、URL、メモなどを消しません。明示的な値がある項目だけを更新します。

### 承認保存の一体性

Human Review承認ではマスターと受信箱を一組として保存し、片側保存に失敗した場合は両方を保存前へ復元します。Photo Capture側はイベント版単位で送信済みを判定し、同じ版の再送信と保存連打を防止します。

### 会社IDの固定

会社対象の `TMP-OR-…` は、最初の承認で作成または指定した正式 `OR-…` IDへ `photoCaptureIdMap` で固定します。同じcaptureのUPDATEを再承認しても、別会社を新規採番せず同じ会社マスターへupsertします。

却下時は理由、確認者、確認日時だけを受信箱へ記録し、マスターを変更しません。

## 5. マスターからSTYLEMへの共有

### 入口

- 所有者向け共有管理: `/customer-sharing/`
- STYLEM顧客領域: `/stylem/`
- 詳細仕様: `docs/CUSTOMER_SHARING.md`

### 明示承認

商品は `sourceStatus === CONFIRMED`、糸は `status === PUBLISHED` の場合だけ共有候補になります。条件を満たしても自動共有せず、所有者が「STYLEMへ共有」を押したレコードだけを `APPROVED` grantとして保存します。

### 安全スナップショット

共有管理はマスターから安全項目だけを抽出し、`kc_customer_portal_STYLEM_v1` へ発行します。STYLEM領域のアプリケーションロジックは、マスターキー `kc_independent_practical_v0_4` とgrantキー `kc_customer_sharing_v1` を読みません。

共有承認と顧客スナップショットの片側保存に失敗した場合は、両方を保存前へ復元します。元データが共有条件から外れた場合は、再発行時にSTYLEM領域から除外します。

### 顧客リクエスト

STYLEM領域からの調査・商品追加・糸調査・修正依頼は `kc_customer_requests_v1` に `OPEN` として保存します。共有管理で回答すると `ANSWERED`、完了すると `CLOSED` になります。顧客依頼からマスターを自動更新しません。

### Pilotの限界

現在は同一オリジン／同一ブラウザのローカルPilotです。正式な社外公開ではサーバー側の認証、顧客別認可、行レベル権限、監査ログ、署名付き画像URLが必要です。ローカルPilotを正式なセキュリティ境界とは扱いません。

## 6. Revision形式

- 単一ファイル: `git-blob:<40桁SHA>`
- ディレクトリ: `content-sha256:<64桁SHA>`

Pull Requestとmainへのpushで、接続台帳、実ファイルRevision、CI対象パス、保存キー、接続表示、KPI列を自動検証します。

- `scripts/validate_handoff_safety.py`: JavaScript構文、混率判定、DRAFT維持、空欄上書き防止、会社ID固定、承認ロールバック、PENDING保持
- `scripts/validate_ui_state_guard.py`: 保存連打防止、版単位の送信固定、入力途中復元
- `scripts/validate_customer_sharing.py`: CONFIRMED／PUBLISHED条件、安全項目投影、STYLEMからのマスター直接参照禁止、明示grant、顧客リクエスト戻し

## 7. 正本

| 対象 | 正本 |
|---|---|
| ソースコード | GitHub `main` |
| 接続定義 | `docs/SYSTEM_REGISTRY.md` と `config/system-registry.json` |
| 共通ID・項目 | `docs/DATA_CONTRACT.md` |
| Photo Capture受渡し | `docs/PHOTO_CAPTURE_HANDOFF.md` |
| 顧客共有 | `docs/CUSTOMER_SHARING.md` |
| 調査承認ルール | `docs/RESEARCH_REVIEW_SOP.md` |
| 現在の業務データ | 各ブラウザ／WebView内。全社一元正本は未決定 |

## 8. 残る次段階

1. 正式な全社一元DB、認証、顧客別権限、監査ログ、バックアップ方針を決定する
2. STYLEM Pilotをサーバー側の顧客領域へ移行する
3. Daily Web／Androidへ同じ受信箱・Human Review導線を展開する
4. 本番公開版へrelease tagを付与する
5. 定期エクスポートと復元テストを運用記録する

## 9. 変更時チェック

- [ ] 本番・独立Sandbox・ローカルPilotを混同していない
- [ ] 読み取り元、書き込み先、受信箱、顧客スナップショットを別々に記載した
- [ ] 候補と承認済みを区別した
- [ ] 変更した全ソースのRevisionを台帳へ登録した
- [ ] 入力途中データの保存キーと写真非保存境界を記載した
- [ ] 空欄で既存マスターを消さない
- [ ] 一時会社IDが同じ正式会社IDへ固定される
- [ ] PENDING候補を件数上限で削除しない
- [ ] STYLEM領域がマスター保存キーを直接読まない
- [ ] 商品はCONFIRMED、糸はPUBLISHEDかつ明示承認だけを共有する
- [ ] 顧客リクエストからマスターを自動更新しない
- [ ] 接続先を暗黙に外部DBへ変更していない
- [ ] `python scripts/validate_system_registry.py` が成功した
- [ ] `python scripts/validate_handoff_safety.py` が成功した
- [ ] `python scripts/validate_ui_state_guard.py` が成功した
- [ ] `python scripts/validate_customer_sharing.py` が成功した
