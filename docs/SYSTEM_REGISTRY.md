# Knit Compass システム接続台帳

更新日: 2026-08-04  
版: 1.2.3  
状態: **暫定正本**

## 1. 接続済みフロー

次の3工程を実データで接続しています。

1. Photo Captureが混率・機能性・サステナブル・共通ID・根拠・確認状態をAppend Only DRAFTとして保持
2. Photo CaptureのDRAFTをv0.4の受信箱へ候補送信
3. Human Review承認後だけ商品・糸・会社・素材・調査マスターへ確定反映

PENDING候補とREJECTED候補はマスターへ反映しません。外部Production / Core / Company DBへの自動接続も追加していません。

## 2. 現在の接続状況

| system_id | 画面・アプリ | 環境 | 表示版 | コード正本・Revision | データ保存先 | 同期・受渡し | 外部DB | 状態 |
|---|---|---|---|---|---|---|---|---|
| `KC-PHOTO-CAPTURE` | Photo Capture | 独立Sandbox | `v1.2.3` | `app.js@main` / `git-blob:5c2efd18e8b6…`。補助: `app-state-guard.js` / `8f42d047…`、`app.css` / `3fa9acda…`、`index.html` / `a679071e…`、`backup.js` / `5f7dee4a…` | IndexedDB `kc_independent_photo_capture_v1_0`、sessionStorage `kc_session_v1`・`kc_photo_capture_editor_draft_v1`、受信箱localStorage `kc_v04_handoff_queue_v1` | 同一ブラウザ受信箱＋手動JSON / PENDINGを全件保持し確認済み履歴から整理 | なし | 稼働中 |
| `KC-V04-WEB` | Knit Compass 独立実用版 v0.4 | 独立運用 | `v0.4.5` | 本体 `brand-intelligence/app.html` / `52f174f3…`。Human Review入口 `brand-intelligence/index.html` / `81927bcd…`。SW `7c5dc989…` | localStorage `kc_independent_practical_v0_4`、受信箱 `kc_v04_handoff_queue_v1` | 候補受信、JSON取込、既存値保護・失敗時復元付きHuman Review反映 | Production / Core / Company DBへの自動接続なし | 稼働中 |
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

## 5. Revision形式

- 単一ファイル: `git-blob:<40桁SHA>`
- ディレクトリ: `content-sha256:<64桁SHA>`

Pull Requestとmainへのpushで、接続台帳、実ファイルRevision、CI対象パス、保存キー、接続表示、KPI列を自動検証します。加えて `scripts/validate_handoff_safety.py` でJavaScript構文、混率判定、DRAFT維持、空欄上書き防止、会社ID固定、承認ロールバック、PENDING保持を、`scripts/validate_ui_state_guard.py` で保存連打防止・版単位の送信固定・入力途中復元を検証します。

## 6. 正本

| 対象 | 正本 |
|---|---|
| ソースコード | GitHub `main` |
| 接続定義 | `docs/SYSTEM_REGISTRY.md` と `config/system-registry.json` |
| 共通ID・項目 | `docs/DATA_CONTRACT.md` |
| Photo Capture受渡し | `docs/PHOTO_CAPTURE_HANDOFF.md` |
| 調査承認ルール | `docs/RESEARCH_REVIEW_SOP.md` |
| 現在の業務データ | 各ブラウザ／WebView内。全社一元正本は未決定 |

## 7. 残る次段階

1. 正式な全社一元DB、権限、監査ログ、バックアップ方針を決定する
2. Daily Web／Androidへ同じ受信箱・Human Review導線を展開する
3. 本番公開版へrelease tagを付与する
4. 定期エクスポートと復元テストを運用記録する

## 8. 変更時チェック

- [ ] 本番・独立Sandbox・ローカルを混同していない
- [ ] 読み取り元、書き込み先、受信箱を別々に記載した
- [ ] 候補と承認済みを区別した
- [ ] 変更した全ソースのRevisionを台帳へ登録した
- [ ] 入力途中データの保存キーと写真非保存境界を記載した
- [ ] 空欄で既存マスターを消さない
- [ ] 一時会社IDが同じ正式会社IDへ固定される
- [ ] PENDING候補を件数上限で削除しない
- [ ] 接続先を暗黙に外部DBへ変更していない
- [ ] `python scripts/validate_system_registry.py` が成功した
- [ ] `python scripts/validate_handoff_safety.py` が成功した
- [ ] `python scripts/validate_ui_state_guard.py` が成功した
