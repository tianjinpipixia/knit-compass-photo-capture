# knit-compass-photo-capture

アパレル編地の写真撮影・商品／素材情報管理システムです。

## 現在の接続状態

> **重要:** Photo Captureは独立Sandboxで、写真とDRAFTをブラウザIndexedDBへ保存します。Knit Compass v0.4 / Daily / Android版も独立運用で、Production、Core、Company DBへ自動接続しません。所有者が明示設定した場合だけ手動同期を使用します。

**画面で確認:** [`/status/`](status/index.html)

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
| Photo Capture | リポジトリ直下 | ブラウザIndexedDB `kc_independent_photo_capture_v1_0` | なし |
| Knit Compass v0.4 | `/brand-intelligence/app.html` | ブラウザlocalStorage | なし |
| Daily Web | `/daily/` | ブラウザlocalStorage | なし |
| Daily Android | APK / `android-daily/` | Android WebView内 | なし |

## ローカル起動

### Windows

Python 3をインストールしたうえで、リポジトリ直下から実行します。

```bat
start.bat
```

### macOS / Linux

```sh
sh start.sh
```

ブラウザで `http://127.0.0.1:8080/` を開きます。ポートを変更する場合、macOS / Linuxでは `PORT=8081 sh start.sh` を使用できます。

Pythonを直接使用する場合は、全OS共通で次を実行できます。

```sh
python3 -m http.server 8080 --bind 127.0.0.1
```

## 検証

接続台帳、実ソースのRevision、イベント別のCI対象、ブラウザ保存キー、KPI列、起動スクリプトを検証します。

```sh
python3 -m pip install -r requirements-validation.txt
python3 scripts/validate_system_registry.py
```

Pull Requestと`main`へのpushでは、GitHub Actionsの `Validate system registry` も実行されます。

## 変更ルール

接続先、保存先、共通ID、確定項目を変更するときは、コードだけでなく以下も同じPull Requestで更新します。

1. `docs/SYSTEM_REGISTRY.md`
2. `config/system-registry.json`
3. `docs/DATA_CONTRACT.md`（項目・IDを変更する場合）
4. `data/kpi_log_template.csv` と `docs/KPI_MEASUREMENT.md`（KPIを変更する場合）

保存先が不明な状態や、AI推定と確認済み情報を区別できない状態を正式運用に入れません。
