# Knit Compass システム接続台帳

更新日: 2026-08-03  
状態: **暫定正本（接続先の不明確さを解消するための基準）**

## 1. この台帳の目的

Photo Capture、Knit Compass v0.4、Daily、Android アプリについて、次の4点を一か所で確認できるようにします。

1. どの画面・アプリか
2. どのコードから動いているか
3. データをどこへ保存するか
4. 外部DBへ接続しているか

記載のない接続を暗黙に追加してはいけません。接続先を変更する場合は、この台帳と `config/system-registry.json` を同じPull Requestで更新します。

## 2. 現在の接続状況

| system_id | 画面・アプリ | 入口 | コード正本 | 現在のデータ保存先 | 外部DB接続 | 状態 |
|---|---|---|---|---|---|---|
| `KC-PHOTO-CAPTURE` | Photo Capture | リポジトリ直下 | `main` のルートファイル | 現行実装に従う。保存先は画面内で明示すること | 未確認の接続は使用禁止 | 稼働中・接続表示改善対象 |
| `KC-V04-WEB` | Knit Compass 独立実用版 v0.4 | `/brand-intelligence/app.html` | `brand-intelligence/app.html` | ブラウザ内ローカルデータ。所有者が設定した場合のみ手動サーバー同期 | Production / Core / Company DBへの自動接続なし | 稼働中 |
| `KC-DAILY-WEB` | Daily ショートカット版 | `/daily/` | v0.4 HTMLを直接配信 | v0.4と同じ | Production / Core / Company DBへの自動接続なし | 稼働中 |
| `KC-DAILY-ANDROID` | Android アプリ | APK | `android/`。ビルド時にv0.4 HTMLを同梱 | Android WebView内のアプリデータ。Androidバックアップ対象外 | Production / Core / Company DBへの自動接続なし | 稼働中 |

## 3. 正本の定義

| 対象 | 正本 |
|---|---|
| ソースコード | GitHub `main` ブランチ |
| 接続定義 | `docs/SYSTEM_REGISTRY.md` と `config/system-registry.json` |
| 共通ID・項目定義 | `docs/DATA_CONTRACT.md` |
| 調査結果の承認ルール | `docs/RESEARCH_REVIEW_SOP.md` |
| KPI記録 | `data/kpi_log_template.csv` を基にした月次台帳 |
| 業務データ | 現時点では一元正本未確定。ブラウザ内データを正式DBと誤認しない |

## 4. 全画面に表示する接続情報

今後、各画面の「接続先情報」またはフッターに次を表示します。

- 環境: `本番` / `テスト` / `ローカル`
- システムID
- 表示バージョン
- コード版（commit SHAまたはrelease tag）
- データ保存先: `ブラウザ内` / `Android端末内` / `サーバー名`
- 外部同期: `未設定` / `手動` / `自動`
- 最終同期日時

表示例:

> 本番｜KC-V04-WEB｜v0.4｜データ: ブラウザ内｜外部同期: 未設定｜最終同期: なし

保存先が判定できない場合は、正常表示ではなく次の警告を出します。

> 保存先未確認。この状態では正式データとして確定できません。

## 5. 接続変更時の必須確認

- [ ] 本番・テスト・ローカルを混同していない
- [ ] 読み取り元と書き込み先を別々に記載した
- [ ] 認証情報をHTML、localStorage、Git履歴へ直接保存していない
- [ ] 接続失敗時にローカル保存へ黙って切り替わらない
- [ ] 同期日時と同期結果を画面で確認できる
- [ ] エクスポートと復元手順を確認した
- [ ] この台帳とJSONを更新した

## 6. 未解決事項

1. Photo Captureの実際の書き込み先を、画面とコードの両方で一意に表示する
2. Photo Capture、商品、糸、ブランド、調査記録を共通IDで結ぶ
3. 正式な業務データの一元正本を決定する
4. 本番公開版にrelease tagを付け、画面にcommit SHAを表示する
5. 定期エクスポートと復元テストを運用化する
