# knit-compass-photo-capture

アパレル編地の写真撮影・商品／素材情報管理システムです。

## 現在の接続状態

> **重要:** Knit Compass v0.4 / Daily / Android版は独立運用です。現時点で Production、Core、Company DBへ自動接続しません。v0.4の業務データは基本的にブラウザまたはAndroid WebView内に保存され、所有者が設定した場合のみ手動同期を使用します。

接続先、保存先、正本、未解決事項は次を確認してください。

- [システム接続台帳](docs/SYSTEM_REGISTRY.md)
- [機械可読の接続定義](config/system-registry.json)
- [共通ID・データ項目定義](docs/DATA_CONTRACT.md)
- [KIMI・Gemini調査／Human Review SOP](docs/RESEARCH_REVIEW_SOP.md)
- [KPI計測基準](docs/KPI_MEASUREMENT.md)
- [KPI入力テンプレート](data/kpi_log_template.csv)

## 構成

| システム | 入口 | 主な保存先 | 外部DB自動接続 |
|---|---|---|---|
| Photo Capture | リポジトリ直下 | 現行実装。画面内で保存先表示を追加予定 | 未確認接続は禁止 |
| Knit Compass v0.4 | `/brand-intelligence/app.html` | ブラウザ内 | なし |
| Daily Web | `/daily/` | ブラウザ内 | なし |
| Daily Android | APK | Android WebView内 | なし |

## ローカル起動

```bat
start.bat
```

ブラウザで `http://localhost:8080` を開きます。

## 変更ルール

接続先、保存先、共通ID、確定項目を変更するときは、コードだけでなく以下も同じPull Requestで更新します。

1. `docs/SYSTEM_REGISTRY.md`
2. `config/system-registry.json`
3. `docs/DATA_CONTRACT.md`（項目・IDを変更する場合）

保存先が不明な状態や、AI推定と確認済み情報を区別できない状態を正式運用に入れません。
