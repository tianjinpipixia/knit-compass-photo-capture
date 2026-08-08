# knit-compass-photo-capture

アパレル編地・糸・商品の写真撮影から、Human Review後のマスター確定までをつなぐKnit Compass独立運用リポジトリです。

## 現在の接続状態

Photo Capture、v0.4、Daily、Androidは引き続き独立運用です。Production、Core、Company DBへの自動接続はありません。

次の3工程を接続しています。

1. Photo Captureが混率・機能性・サステナブル・共通ID・根拠をAppend Only DRAFTとして保存
2. DRAFTをv0.4の「Photo Capture受信箱」へ候補送信
3. Human Review承認後だけ商品・糸・会社マスターへ確定反映

同一ブラウザではlocalStorage受信箱を共有します。別サイト・別端末では受信箱JSONを書き出し、v0.4側で取り込みます。PENDINGまたはREJECTEDの候補はマスターへ反映しません。

v0.4.6では、V04入口に**中国糸名辞書**を追加しています。中国の展示会・BOOK・WeChatで使われる市場名を日本語標準名と**代表的な糸タイプ（例）**へ変換し、現在のV04糸マスターと読取専用で照合します。

### データ保護

- 既存マスターに値があり、Photo Capture側が空欄の場合は既存値を維持します。
- `TMP-OR-…` の会社一時IDは、最初に承認した正式 `OR-…` IDへ固定して以後のUPDATEでも再利用します。
- 受信箱が500件を超えてもPENDING候補は削除しません。古いAPPROVED／REJECTED履歴から先に整理します。
- 保存容量不足時は未承認候補を黙って削除せず、保存失敗として表示します。
- 同じイベント版の送信ボタンは送信後に無効化し、保存・承認処理の連打を防止します。
- Human Review承認時はマスターと受信箱を一組として保存し、片側だけ失敗した場合は元に戻します。
- 混率合計は半角`%`・全角`％`の両方を認識し、`TENCEL A100`や`G100`など品名中の数字は加算しません。
- 編地仕様はゲージと本取りを分離し、`12G×2`を`gauge: 12G`、`knittingEnds: 2`としてDRAFTと受信箱payloadに保存します。
- 中国糸名辞書の`仿〇〇`、`冰麻`、`丝麻`などは市場名として扱い、天然繊維の含有を名称だけで確定しません。混率・規格書・Supplier確認を優先します。
- 中国糸名辞書はlocalStorage `kc_independent_practical_v0_4` の糸マスターを読取専用で参照し、自動更新やHuman Review状態変更を行いません。

**画面で確認:** [`/status/`](status/index.html)

## 構成

| システム | 入口 | 主な保存先 | 接続 |
|---|---|---|---|
| Photo Capture v1.2.4 | `/` | IndexedDB `kc_independent_photo_capture_v1_0` | v0.4受信箱へ候補送信 |
| Knit Compass v0.4.6 | `/brand-intelligence/` | localStorage `kc_independent_practical_v0_4` | Human Review後にマスター反映／中国糸名辞書は読取専用照合 |
| Daily Web | `/daily/` | localStorage | 独立運用 |
| Daily Android | APK / `android-daily/` | Android WebView内 | 独立運用 |

受信箱は localStorage `kc_v04_handoff_queue_v1` を使用し、写真Blobは複製しません。

## 基準文書

- [システム接続台帳](docs/SYSTEM_REGISTRY.md)
- [共通ID・データ項目定義](docs/DATA_CONTRACT.md)
- [Photo Capture受渡し仕様](docs/PHOTO_CAPTURE_HANDOFF.md)
- [中国語糸名辞書](docs/CN_YARN_GLOSSARY.md)
- [KIMI・Gemini調査／Human Review SOP](docs/RESEARCH_REVIEW_SOP.md)
- [KPI計測基準](docs/KPI_MEASUREMENT.md)

## ローカル起動

Windows:

```bat
start.bat
```

macOS / Linux:

```sh
sh start.sh
```

ブラウザで `http://127.0.0.1:8080/` を開きます。v0.4のHuman Review受信箱と中国糸名辞書は `http://127.0.0.1:8080/brand-intelligence/` から切り替えます。

## 検証

```sh
python3 -m pip install -r requirements-validation.txt
python3 scripts/validate_system_registry.py
python3 scripts/validate_yarn_glossary.py
python3 scripts/validate_handoff_safety.py
python3 scripts/validate_ui_state_guard.py
```

検証対象は、接続台帳、全登録ソースのGit blob／content SHA、保存キー、CIトリガー、接続表示、KPI列、JavaScript構文、空欄上書き防止、会社ID固定、PENDING保持、本取りフィールドの読込順と保存契約、中国糸名辞書の初期8分類・標準ラベル・天然繊維確認ルールです。

## 変更ルール

接続先、保存先、共通ID、確定項目を変更するときは、コードだけでなく次を同じPull Requestで更新します。

1. `docs/SYSTEM_REGISTRY.md`
2. `config/system-registry.json`
3. `docs/DATA_CONTRACT.md` または `docs/PHOTO_CAPTURE_HANDOFF.md`
4. 必要に応じて `docs/CN_YARN_GLOSSARY.md`、KPI文書、テンプレート

AI推定、候補、Human Review承認済みの値を同じ状態として扱いません。
