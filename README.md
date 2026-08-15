# knit-compass-photo-capture

アパレル編地・糸・商品の写真撮影から、Human Review後のマスター確定までをつなぐKnit Compass独立運用リポジトリです。

## 現在の接続状態

Photo Capture、商品調査・Human Review、Daily、Androidは引き続き独立運用です。Production、Core、Company DBへの自動接続はありません。設計・実装・検証・公開作業はApple Silicon搭載Macを主環境とし、Windowsは会社内でのブラウザ利用と補助起動に限定します。

次の4工程を接続しています。

1. Photo Captureが混率・機能性・サステナブル・共通ID・根拠をAppend Only DRAFTとして保存
2. DRAFTを「Human Review受信箱」へ候補送信
3. Human Review承認後だけ商品・糸・会社マスターへ確定反映
4. 月次掲載観測を根拠付きMD提案へ接続し、販売数量未取得時は推定せず公開保留

同一ブラウザではlocalStorage受信箱を共有します。別サイト・別端末では受信箱JSONを書き出し、Human Review側で取り込みます。PENDINGまたはREJECTEDの候補はマスターへ反映しません。

Photo Capture v1.3.3では、Independent Account IDを画面から除外した簡単な利用開始、Macの端末内データ自動保護、7日バックアップ警告、バックアップ整合性検証を追加しました。Service WorkerによるPWA起動とオフライン再起動も維持します。営業向けメニューでは「商品調査・糸検索・原料相場・編み地イメージ・生地検査」を先頭に置き、技術情報と補助画面は管理メニューへ集約します。

糸マスター／3,000件カタログからは、番手・混率・糸構造・対応ゲージを引き継ぐ「糸 → 編み地イメージ」を開けます。ゲージ・編組織・本取りを指定し、外部AIへ送信せず端末内で検討用PNGを生成します。既存マスターと公開範囲は変更しません。

商品調査・Human Reviewでは、営業向け入口とカタログ導線を整理し、**中国糸名辞書**と**月次掲載・MD**を接続しています。中国市場名は日本語標準名・代表的な糸タイプ（例）として読取専用で照合し、月次観測は販売数量を推定せずMD提案へ引き継ぎます。内部互換性のため、保存キーと受信箱形式には従来の `v0_4` / `V04` 識別子を維持します。

生地検査と原料相場 / Market Intelligenceは独立した端末内の追記型記録です。どちらも `PENDING_HUMAN_REVIEW`・公開保留で保存し、正式マスター、Human Review受信箱、顧客共有を自動更新しません。原料相場は中国ベースの綿・ウール・麻・ナイロン・ポリエステル・再生ポリエステルを一画面比較し、出典URL付き確認済み観測だけを表示します。ライブ価格取得、通貨・単位の自動換算、将来予測は行いません。

### データ保護

- 既存マスターに値があり、Photo Capture側が空欄の場合は既存値を維持します。
- `TMP-OR-…` の会社一時IDは、最初に承認した正式 `OR-…` IDへ固定して以後のUPDATEでも再利用します。
- 受信箱が500件を超えてもPENDING候補は削除しません。古いAPPROVED／REJECTED履歴から先に整理します。
- 保存容量不足時は未承認候補を黙って削除せず、保存失敗として表示します。
- 同じイベント版の送信ボタンは送信後に無効化し、保存・承認処理の連打を防止します。
- Human Review承認時はマスターと受信箱を一組として保存し、片側だけ失敗した場合は元に戻します。
- Human Reviewで番手・混率・ゲージ等を反映するのは根拠確認済みの項目だけです。推定・AI候補・未確認項目は確定値にしません。
- 会社の `organizationProfile` を正式OR-IDに保持し、承認済み会社間の一時関係IDを正式IDへ解決します。
- 混率合計は半角`%`・全角`％`の両方を認識し、`TENCEL A100`や`G100`など品名中の数字は加算しません。
- 編地仕様はゲージと本取りを分離し、`12G×2`を`gauge: 12G`、`knittingEnds: 2`としてDRAFTと受信箱payloadに保存します。
- 中国糸名辞書の`仿〇〇`、`冰麻`、`丝麻`などは市場名として扱い、天然繊維の含有を名称だけで確定しません。混率・規格書・Supplier確認を優先します。
- 中国糸名辞書はlocalStorage `kc_independent_practical_v0_4` の糸マスターを読取専用で参照し、自動更新やHuman Review状態変更を行いません。
- 月次掲載観測に販売数量の根拠がない場合は `NOT_AVAILABLE` / `null` のまま保持し、MD提案を必ず公開保留にします。
- 編み地イメージは糸データを読取専用で参照し、Canvas／PNG以外の保存、外部送信、自動マスター反映、自動公開を行いません。

**画面で確認:** [`/status/`](status/index.html)

## 構成

| システム | 入口 | 主な保存先 | 接続 |
|---|---|---|---|
| Photo Capture v1.3.3 | `/` | IndexedDB `kc_independent_photo_capture_v1_0`＋端末内永続化要求＋検証付きバックアップ | Human Review受信箱へ候補送信 |
| 商品調査・Human Review | `/brand-intelligence/` | localStorage `kc_independent_practical_v0_4` | Human Review後にマスター反映／月次掲載観測から公開保留MD提案 |
| 糸検索（3,000件） | `/owner-yarns/` | 静的カタログ＋localStorage受信箱 | CATALOG_INDEXEDと正式糸を分離／全件NOT_PROMOTED／19件はPENDING取込／12承認可能・4条件付き・3HOLDは判定補助のみ／選択糸を編み地イメージへ読取専用で引渡し |
| 糸 → 編み地イメージ v1.0.0 | `/knit-image/` | なし（Canvas、明示PNG保存のみ） | 外部送信・マスター書込なし |
| 生地検査 | `/fabric-inspection/` | localStorage `kc_fabric_inspection_records_v1` | 追記専用／Human Review待ち／監査JSON |
| 原料相場 / Market Intelligence | `/market-intelligence/` | localStorage `kc_market_intelligence_observations_v1` | 中国6原料比較／確認済み出典URL必須／64ブランドMD→糸候補→素材提案／自動換算・推定なし／Human Review待ち |
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
- [公式商品リンク未登録9件の完了記録](docs/PRODUCT_LINK_COMPLETION_20260809.md)

## ローカル起動

主開発環境はApple Silicon搭載Macです。初回はApple Silicon版Node.js LTSを導入し、次を実行します。

```sh
scripts/setup_macos.sh
```

Finderから `start.command` を開くか、ターミナルから起動します。

```sh
./start.sh
```

ブラウザで `http://127.0.0.1:8080/` を開きます。Human Review受信箱と中国糸名辞書は `http://127.0.0.1:8080/brand-intelligence/` から切り替えます。

Windowsは会社PCでの補助起動だけを維持します。設計・実装・検証環境としては使用しません。

```bat
start.bat
```

詳細は [Mac開発環境方針](docs/MAC_DEVELOPMENT.md) を参照してください。

## 検証

```sh
scripts/validate_macos.sh
```

検証対象は、Apple Silicon/arm64の実行環境、接続台帳、全登録ソースのGit blob／content SHA、保存キー、CIトリガー、営業向け表記、全ローカル画面・素材リンク、JavaScript構文、Photo Captureのインストール名・カメラアイコン・PWA起動・操作配置、空欄上書き防止、根拠付き項目だけの反映、会社IDとプロフィール、PENDING保持、本取り保存契約、中国糸名辞書、生地検査・原料相場の追記／公開保留境界、月次観測から公開保留MD提案への接続、販売数量の非推定、および公式商品URL未登録9件の解消です。Node.jsがない場合にJavaScript検証を省略して成功扱いにはしません。

## 変更ルール

接続先、保存先、共通ID、確定項目を変更するときは、コードだけでなく次を同じPull Requestで更新します。

1. `docs/SYSTEM_REGISTRY.md`
2. `config/system-registry.json`
3. `docs/DATA_CONTRACT.md` または `docs/PHOTO_CAPTURE_HANDOFF.md`
4. 必要に応じて `docs/CN_YARN_GLOSSARY.md`、KPI文書、テンプレート

AI推定、候補、Human Review承認済みの値を同じ状態として扱いません。
