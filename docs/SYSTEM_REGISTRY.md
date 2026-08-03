# Knit Compass システム接続台帳

更新日: 2026-08-03  
版: 1.1.1  
状態: **暫定正本（接続先の不明確さを解消するための基準）**

## 1. この台帳の目的

Photo Capture、Knit Compass v0.4、Daily、Androidアプリについて、次を一か所で確認できるようにします。

1. どの画面・アプリか
2. どのコードと版から動いているか
3. データをどこへ保存するか
4. 外部同期・外部DB接続があるか
5. 最終同期日時をどこで確認するか

記載のない接続を暗黙に追加してはいけません。接続先を変更する場合は、この台帳と `config/system-registry.json` を同じPull Requestで更新します。

## 2. 現在の接続状況

| system_id | 画面・アプリ | 環境 | 表示版 | コード正本・Revision | データ保存先 | 同期・最終同期 | 外部DB | 状態 |
|---|---|---|---|---|---|---|---|---|
| `KC-PHOTO-CAPTURE` | Photo Capture | 独立Sandbox | `v1.1.0` | `app.js@main` / `git-blob:c1604c677b2f…`。補助: `backup.js@main` / `git-blob:5f7dee4ac1de…` | IndexedDB `kc_independent_photo_capture_v1_0`。ログイン中の識別情報はsessionStorage `kc_session_v1`。最終バックアップ日時だけをlocalStorage `kc_photo_capture_last_backup_v1`へ保存 | 同期OFF / `not-applicable` | なし | 稼働中 |
| `KC-V04-WEB` | Knit Compass 独立実用版 v0.4 | 独立運用 | `v0.4` | `brand-intelligence/app.html@main` / `git-blob:52f174f307d4…` | ブラウザlocalStorage `kc_independent_practical_v0_4` | 所有者設定時のみ手動 / `runtime-per-device-or-none` | Production / Core / Company DBへの自動接続なし | 稼働中 |
| `KC-DAILY-WEB` | Dailyショートカット版 | 独立運用 | `v0.4` | `daily/index.html@main` / `git-blob:a7d85f1bd884…` | v0.4と同じlocalStorage | 所有者設定時のみ手動 / `runtime-per-device-or-none` | Production / Core / Company DBへの自動接続なし | 稼働中 |
| `KC-DAILY-ANDROID` | Androidアプリ | 独立APK | `v0.4.0` | `android-daily@main` / `git-commit:5b8cf9256dd6…` | Android WebViewアプリデータ。バックアップ・端末移行の抽出対象外 | 所有者設定時のみ手動 / `runtime-per-device-or-none` | Production / Core / Company DBへの自動接続なし | 稼働中 |

`runtime-per-device-or-none` は、最終同期日時が静的台帳ではなく各端末内の実行時データとして保持されることを示します。同期未実施の端末では「なし」です。

## 3. 正本の定義

| 対象 | 正本 |
|---|---|
| ソースコード | GitHub `main` ブランチ |
| 接続定義 | `docs/SYSTEM_REGISTRY.md` と `config/system-registry.json` |
| 共通ID・項目定義 | `docs/DATA_CONTRACT.md` |
| 調査結果の承認ルール | `docs/RESEARCH_REVIEW_SOP.md` |
| KPI記録 | `data/kpi_log_template.csv` を基にした月次台帳 |
| 業務データ | 現時点では一元正本未確定。ブラウザ／WebView内データを正式な一元DBと誤認しない |

## 4. 全画面に表示する接続情報

各画面の「接続先情報」またはフッターに次を表示します。

- 環境
- システムID
- 表示バージョン
- コードRevision（commit SHA、release tag、またはgit blob SHA）
- データ保存先
- 外部同期方式
- 最終同期日時
- 外部DB接続状態

表示例:

> 独立Sandbox｜KC-PHOTO-CAPTURE｜v1.1.0｜Revision: c1604c677b2f｜データ: IndexedDB｜同期: OFF｜最終同期: 対象外

端末ごとに値が異なる項目は、静的台帳で架空の日時を記入せず `runtime-per-device-or-none` と表示します。

## 5. 接続変更時の必須確認

- [ ] 本番・テスト・独立Sandbox・ローカルを混同していない
- [ ] 読み取り元と書き込み先を別々に記載した
- [ ] 表示バージョンとコードRevisionを記載した
- [ ] 主コードと補助コードのRevisionを実ファイルと照合した
- [ ] 認証情報をHTML、Git履歴、エクスポートファイルへ直接保存していない
- [ ] 接続失敗時に別保存先へ黙って切り替わらない
- [ ] 同期日時と同期結果を画面で確認できる
- [ ] エクスポートと復元手順を確認した
- [ ] この台帳とJSONを更新した
- [ ] `python scripts/validate_system_registry.py` が成功した

## 6. 未解決事項

1. Photo Capture、商品、糸、ブランド、会社、写真、調査記録を共通IDで結ぶ
2. 正式な業務データの一元正本を決定する
3. 本番公開版にrelease tagを付け、画面のRevisionをrelease tag中心へ切り替える
4. v0.4 / Daily / Androidの実行画面にも同等の接続表示を追加する
5. 定期エクスポートと復元テストを運用化する
