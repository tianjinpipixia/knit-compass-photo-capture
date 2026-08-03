# Knit Compass システム接続台帳

更新日: 2026-08-04  
版: 1.2.0  
状態: **暫定正本**

## 1. 接続済みフロー

次の3工程を実データで接続しました。

1. Photo Captureが混率・機能性・サステナブル・共通ID・根拠・確認状態をAppend Only DRAFTとして保持
2. Photo CaptureのDRAFTをv0.4の受信箱へ候補送信
3. Human Review承認後だけ商品・糸・会社・素材・調査マスターへ確定反映

PENDING候補とREJECTED候補はマスターへ反映しません。外部Production / Core / Company DBへの自動接続も追加していません。

## 2. 現在の接続状況

| system_id | 画面・アプリ | 環境 | 表示版 | コード正本・Revision | データ保存先 | 同期・受渡し | 外部DB | 状態 |
|---|---|---|---|---|---|---|---|---|
| `KC-PHOTO-CAPTURE` | Photo Capture | 独立Sandbox | `v1.2.0` | `app.js@main` / `git-blob:4bca5b3bf439…`。補助: `app.css` / `3fa9acda…`、`index.html` / `a64a5e17…`、`backup.js` / `5f7dee4a…` | IndexedDB `kc_independent_photo_capture_v1_0`、sessionStorage `kc_session_v1`、受信箱localStorage `kc_v04_handoff_queue_v1` | 同一ブラウザ受信箱＋手動JSON / 最終受渡しは端末内実行時値 | なし | 稼働中 |
| `KC-V04-WEB` | Knit Compass 独立実用版 v0.4 | 独立運用 | `v0.4.3` | 本体 `brand-intelligence/app.html` / `52f174f3…`。Human Review入口 `brand-intelligence/index.html` / `36c48940…`。SW `90332232…` | localStorage `kc_independent_practical_v0_4`、受信箱 `kc_v04_handoff_queue_v1` | 候補受信、JSON取込、Human Review後のローカルマスター反映 | Production / Core / Company DBへの自動接続なし | 稼働中 |
| `KC-DAILY-WEB` | Dailyショートカット版 | 独立運用 | `v0.4` | `daily/index.html@main` / `a7d85f1b…` | v0.4と同じlocalStorage | 所有者設定時のみ手動 | 自動接続なし | 稼働中 |
| `KC-DAILY-ANDROID` | Androidアプリ | 独立APK | `v0.4.0` | `android-daily@main` / `content-sha256:21ff2fd0…` | Android WebViewアプリデータ | 所有者設定時のみ手動 | 自動接続なし | 稼働中 |

## 3. Photo Captureからv0.4への受渡し

### 同一ブラウザ・同一オリジン

Photo CaptureはlocalStorage `kc_v04_handoff_queue_v1` に `KC_V04_INBOX_ITEM` を追加し、v0.4のHuman Review受信箱が同じキーを読み取ります。

### 別サイト・別端末

Photo Captureで `KC_V04_INBOX_EXPORT` JSONを書き出し、v0.4の「受信箱JSONを取込」で読み込みます。

写真Blobは受信箱へ複製しません。写真ID、分類、ファイル名、撮影日時だけを候補へ含めます。

## 4. Human Review後の確定処理

承認時は一時IDを正式IDへ変換し、次をIDでupsertします。

- 商品マスター
- 糸マスター
- 会社・組織マスター
- 素材マスター
- 調査記録
- 商品と糸の紐付け

一時IDと正式IDの対応は `photoCaptureIdMap` へ保存します。承認記録は `photoCaptureImports` と `auditLog` へ保存します。

却下時は理由、確認者、確認日時だけを受信箱へ記録し、マスターを変更しません。

## 5. Revision形式

- 単一ファイル: `git-blob:<40桁SHA>`
- ディレクトリ: `content-sha256:<64桁SHA>`

Pull Requestとmainへのpushで、接続台帳、実ファイルRevision、CI対象パス、保存キー、接続表示、KPI列を自動検証します。

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
- [ ] 接続先を暗黙に外部DBへ変更していない
- [ ] `python scripts/validate_system_registry.py` が成功した
