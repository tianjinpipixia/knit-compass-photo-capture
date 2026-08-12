# Knit Compass システム接続台帳

更新日: 2026-08-12
版: 1.6.0
状態: **暫定正本**

## 1. 接続済みフロー

次の6工程を実データで接続しています。

1. Photo Captureが混率・機能性・サステナブル・共通ID・根拠・確認状態をAppend Only DRAFTとして保持
2. Photo CaptureのDRAFTをv0.4の受信箱へ候補送信
3. Human Review承認後だけ商品・糸・会社・素材・調査マスターへ確定反映
4. 月次掲載観測をMD提案へ紐付け、販売数量未取得時は推定せず公開保留
5. 顧客共有管理で、確認済み／PUBLISHEDかつ所有者が明示承認した安全項目だけを顧客ポータル用スナップショットへ発行
6. 顧客ポータルからの調査・商品追加・修正依頼を、マスターを直接変更せず専用リクエストとして戻す

加えて、v0.4には読取専用の中国語糸名辞書 `KC-CN-YARN-001` を接続し、中国市場名から日本語標準名・代表的な糸タイプへ変換しながら、同一ブラウザのV04糸マスター一致候補を表示します。辞書はマスターを自動更新しません。

糸マスターと2,000件カタログには、読取専用の「糸 → 編み地イメージ」`KC-YARN-KNIT-IMAGE` を接続しています。番手・混率・糸構造・対応ゲージを引き継ぎ、ゲージ・編組織・本取りを別項目として指定し、端末内Canvasで検討用PNGを生成します。マスター、受信箱、顧客共有データ、外部AI/APIへの書き込みはありません。

業務入口として、生地検査 `KC-FABRIC-INSPECTION` と原料相場 `KC-MARKET-INTELLIGENCE` を追加します。どちらも端末内の追記型記録で、`PENDING_HUMAN_REVIEW`・公開保留のまま保存し、V04マスター、Photo Capture受信箱、顧客共有を自動変更しません。

V04の共通入口には `V04本体 → Photo Capture → 中国糸名辞書 → 糸検索2,000件 → 編み地イメージ → 生地検査 → 原料相場 → Daily → 管理` の導線を常設し、管理メニューから未反映17件取込、共有管理、顧客ポータル、システム状態へ移動できます。Photo Capture、糸検索、Daily、共有管理、システム状態にも主要画面への共通導線を置きます。外部画面へ移動する導線はトップ階層で開き、V04内のiframeを入れ子にしません。顧客ポータルは所有者向け管理導線を表示せず、既存の顧客境界を維持します。

PENDING候補とREJECTED候補はマスターへ反映しません。DRAFT／REVIEW、未確認商品、社内研究メモ、開発仮説、糸の価格・MOQ・納期・注意事項は顧客ポータルへ発行しません。外部Production / Core / Company DBへの自動接続も追加していません。

## 2. 現在の接続状況

| system_id | 画面・アプリ | 環境 | 表示版 | コード正本・Revision | データ保存先 | 同期・受渡し | 外部DB | 状態 |
|---|---|---|---|---|---|---|---|---|
| `KC-PHOTO-CAPTURE` | Photo Capture | 独立Sandbox | `v1.3.1` | `app.js@main` と登録済み補助ソース。カメラアイコン、PWA manifest、iOS用アイコン、root Service Workerを含む | IndexedDB `kc_independent_photo_capture_v1_0`、sessionStorage `kc_session_v1`・`kc_photo_capture_editor_draft_v1`、本取りUI補助localStorage `kc_photo_capture_knitting_ends_v1`、受信箱localStorage `kc_v04_handoff_queue_v1` | 同一ブラウザ受信箱＋手動JSON / PENDINGを全件保持 / 送信失敗時もDRAFT維持 / ゲージと本取りを分離 / PWA再起動 | なし | 稼働中 |
| `KC-V04-WEB` | Knit Compass 独立実用版 v0.4 | 独立運用 | `v0.4.7` | 本体 `brand-intelligence/app.html` と登録済み補助ソース | localStorage `kc_independent_practical_v0_4`、受信箱 `kc_v04_handoff_queue_v1` | 根拠確認済み項目だけHuman Review反映。会社プロフィールと正式関係IDを保持。月次掲載観測→公開保留MD提案。販売数量は非推定 | Production / Core / Company DBへの自動接続なし | 稼働中 |
| `KC-OWNER-YARN-MASTER` | 糸検索2,000件・未反映17件取込 | 独立運用 | `v1.0.0` | `owner-yarns/index.html@main` | 静的2,000件カタログ、V04端末内マスター、受信箱 | CATALOG_INDEXEDを正式糸と分離し、取込はPENDINGのみ。選択糸を編み地イメージへ読取専用で引渡し | 会社受信箱CSVのみ／直接書込なし | 稼働中 |
| `KC-YARN-KNIT-IMAGE` | 糸 → 編み地イメージ | 独立Sandbox | `v1.0.0` | `knit-image/app.js@main` とHTML/CSS | 読取専用カタログ＋端末内V04マスター。生成結果はCanvas／明示PNG保存 | 外部送信なし・マスター書込なし・検討用画像のみ | なし | 稼働中 |
| `KC-FABRIC-INSPECTION` | 生地検査 | 独立端末内 | `v1.0.0` | `fabric-inspection/app.js@main` と `fabric-inspection/index.html@main` | localStorage `kc_fabric_inspection_records_v1` | 追記専用／PENDING_HUMAN_REVIEW／監査JSON | 自動接続なし | 稼働中 |
| `KC-MARKET-INTELLIGENCE` | 原料相場 / Market Intelligence | 独立端末内 | `v1.0.0` | `market-intelligence/app.js@main` と `market-intelligence/index.html@main` | localStorage `kc_market_intelligence_observations_v1` | 手動観測追記／自動換算なし／PENDING_HUMAN_REVIEW／監査JSON | ライブ価格・外部DB接続なし | 稼働中 |
| `KC-CUSTOMER-SHARING-ADMIN` | 顧客共有管理 | 同一オリジン・所有者ローカルPilot | `v1.0.2` | `customer-sharing/index.html` と共有ポリシー `customer-sharing/policy.js` | マスター、共有承認、顧客ポータル用安全スナップショット、顧客依頼 | 所有者明示承認 → 安全項目スナップショット発行／共有取消／顧客依頼回答 | 自動接続なし | Pilot |
| `KC-STYLEM-PORTAL` | 顧客ポータル | 同一オリジン・顧客ローカルPilot | `v1.0.2` | `stylem/index.html` と共有ポリシー `customer-sharing/policy.js`。system_idと保存キーの`STYLEM`は後方互換用の内部識別子 | 顧客ポータル用安全スナップショット `kc_customer_portal_STYLEM_v1`、顧客依頼 `kc_customer_requests_v1` | 承認済みスナップショット閲覧／顧客リクエスト送信。マスター直接更新なし | 自動接続なし | Pilot |
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

### 編地のゲージと本取り

Photo Captureは `gauge` と `knittingEnds` を別項目としてIndexedDBのAppend Onlyイベントへ保存し、そのままv0.4受信箱payloadへ渡します。資料の `12G×2`、`12G*2`、`12G＊2` は `gauge: "12G"` と `knittingEnds: 2` に分離します。本取りは糸の合糸数・撚り本数とは別概念です。

localStorage `kc_photo_capture_knitting_ends_v1` は一覧表示と編集値復元のための補助索引であり、正本はIndexedDBイベントです。

### 生地検査と原料相場の分離

- 生地検査は `kc_fabric_inspection_records_v1` へ追記し、検査判定と根拠状態を別項目で保持します。訂正時は元行を上書きせず、`supersedes_id` を持つ新しい検査記録を作ります。
- 原料相場は `kc_market_intelligence_observations_v1` へ追記し、観測日、原料、市場、指標、値、通貨、単位、方向感、情報源を保持します。異なる通貨・単位の自動換算と将来予測は行いません。
- 両画面は `PENDING_HUMAN_REVIEW`、`publication_status: HOLD` のまま保存します。V04マスター・Photo Capture受信箱・顧客共有キーを読み書きしません。

### 混率合計

混率は数値直後の半角`%`または全角`％`だけを合計します。`TENCEL A100`、`G100`、`70D`、`2/48NM`など品名・グレード・番手中の数字は加算しません。

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

会社対象の `organizationProfile` は正式会社マスターへ保持します。プロフィール内の `relatedOrganizationTempId` は、相手組織も正式承認された時点で対応する `relatedOrganizationId` を追記します。未確認の資本関係は未確認のまま残し、親子関係を推定しません。

### 糸仕様の根拠境界

番手、混率、ゲージ、構造、紡績・加工方法、機能性、サステナブルは、資料確認済み等の根拠状態がある項目だけをマスターへ反映します。`ai_candidate`、`inferred`、`candidate`、`unconfirmed` は確定値へ昇格させません。現物糸10件はPENDINGのままHuman Review対象とし、自動承認しません。

却下時は理由、確認者、確認日時だけを受信箱へ記録し、マスターを変更しません。

## 5. 中国語糸名辞書 `KC-CN-YARN-001`

### 目的

中国の展示会、糸BOOK、WeChatで使われる市場名を、日本のニット実務で想像しやすい名称と糸タイプへ橋渡しします。画面はV04入口の「中国糸名辞書」から開きます。

### 初期登録

初期実装は次の8分類です。

- 仿貂毛／仿貂绒
- 仿兔毛／仿兔绒
- 仿羊绒
- 仿马海毛
- 仿狐狸毛
- 仿羊驼
- 仿亚麻
- 冰麻／丝麻

表示項目は「中国語市場名」「簡体字別名」「日本語標準名」「代表的な糸タイプ（例）」「よく使う実繊維」「分類」「天然対象繊維の確認注意」「検索キーワード」「展示会確認ポイント」を標準とします。`糸例`は標準ラベルとして使いません。

### 判定ルール

`仿〇〇`、`冰麻`、`丝麻`は混率そのものではなく、市場での見た目・風合い・毛足・清涼感などを示す名称として扱います。天然ミンク、Rabbit/Angora、Cashmere、Mohair、Fox、Alpaca、Linen、Silk等の含有は、混率表示またはSupplier確認で確定します。

### V04糸マスター照合

辞書画面はlocalStorage `kc_independent_practical_v0_4` の `yarns` を読取専用で参照し、糸名・品番・Supplier・構造・混率・Gauge・機能・メモと辞書の市場名・別名・日本語名・検索キーワードを照合します。一致は検索補助の候補表示であり、糸マスター、確認状態、Human Review結果を変更しません。

詳細ルールは `docs/CN_YARN_GLOSSARY.md` を正本補助文書とします。

## 6. 月次掲載観測からMD提案

V04の「月次掲載・MD」で、ブランド、対象月、公式掲載数、新規掲載数、セール掲載数、観測日、根拠URLを記録します。販売数量を取得できない場合は `NOT_AVAILABLE` と `null` を保持し、掲載数から販売数量を推定しません。

MD提案は元の観測IDと観測スナップショットを保持し、状態を `DRAFT` / `REVIEW` / `PUBLISH_HOLD` に限定します。`publicationStatus` は常に `HOLD` で、自動公開と自動マスター反映を行いません。

## 7. マスターから顧客ポータルへの共有

### 入口

- 所有者向け共有管理: `/customer-sharing/`
- 顧客ポータル: `/stylem/`（パス名と内部保存キーは後方互換のため維持）
- 詳細仕様: `docs/CUSTOMER_SHARING.md`

### 明示承認

商品は `sourceStatus === CONFIRMED`、糸は `status === PUBLISHED` の場合だけ共有候補になります。条件を満たしても自動共有せず、所有者が顧客共有を明示したレコードだけを `APPROVED` grantとして保存します。

### 安全スナップショット

共有管理はマスターから安全項目だけを抽出し、後方互換用キー `kc_customer_portal_STYLEM_v1` へ発行します。顧客ポータルのアプリケーションロジックは、マスターキー `kc_independent_practical_v0_4` とgrantキー `kc_customer_sharing_v1` を読みません。

共有承認と顧客スナップショットの片側保存に失敗した場合は、両方を保存前へ復元します。元データが共有条件から外れた場合は、再発行時に顧客ポータルから除外します。

### 顧客リクエスト

顧客ポータルからの調査・商品追加・糸調査・修正依頼は `kc_customer_requests_v1` に `OPEN` として保存します。共有管理で回答すると `ANSWERED`、完了すると `CLOSED` になります。顧客依頼からマスターを自動更新しません。

### Pilotの限界

現在は同一オリジン／同一ブラウザのローカルPilotです。正式な社外公開ではサーバー側の認証、顧客別認可、行レベル権限、監査ログ、署名付き画像URLが必要です。ローカルPilotを正式なセキュリティ境界とは扱いません。

## 8. Revision形式

- 単一ファイル: `git-blob:<40桁SHA>`
- ディレクトリ: `content-sha256:<64桁SHA>`

Pull Requestとmainへのpushで、接続台帳、実ファイルRevision、CI対象パス、保存キー、接続表示、KPI列を自動検証します。

- `scripts/validate_handoff_safety.py`: JavaScript構文、混率判定、DRAFT維持、空欄上書き防止、会社ID固定、承認ロールバック、PENDING保持
- `scripts/validate_photo_capture_install.py`: PWA名、カメラアイコン、インストール用PNG、新規キャプチャ／書き出し配置、安全モデル表示
- `scripts/validate_v04_monthly_md.py`: 月次観測、販売数量の非推定、MD提案の公開保留、JSON／CSV／サーバー出力
- `scripts/validate_ui_state_guard.py`: 保存連打防止、版単位の送信固定、入力途中復元、本取りフィールドの読込順・保存契約・ゲージ分離
- `scripts/validate_customer_sharing.py`: CONFIRMED／PUBLISHED条件、安全項目投影、顧客ポータルからのマスター直接参照禁止、明示grant、顧客リクエスト戻し
- `scripts/validate_yarn_glossary.py`: 初期8分類、辞書ラベル、天然繊維確認ルール、V04入口・保存済みHuman Review画面・オフラインキャッシュ、およびV04 TOPの主要9操作を検証
- `scripts/validate_navigation_links.py`: 全HTMLのローカル画面・素材リンク、主要画面の相互導線、V04 iframe対象を検証
- `scripts/validate_knit_image.py`: 糸マスター／カタログ参照、番手・混率引継ぎ、ゲージ・編組織・本取り分離、Canvas PNG生成、外部送信とマスター書込の禁止を検証
- `scripts/validate_operational_surfaces.py`: 生地検査・原料相場の追記型保存、PENDING／公開保留、V04マスター・受信箱非接続、外部価格フィード非接続を検証
- `scripts/validate_product_link_completion_20260809.py`: 未登録だった公式商品URL 9件の品番・公式ドメイン・女性ニット対象範囲を検証

## 9. 正本

| 対象 | 正本 |
|---|---|
| ソースコード | GitHub `main` |
| 接続定義 | `docs/SYSTEM_REGISTRY.md` と `config/system-registry.json` |
| 共通ID・項目 | `docs/DATA_CONTRACT.md` |
| Photo Capture受渡し | `docs/PHOTO_CAPTURE_HANDOFF.md` |
| 中国語糸名辞書 | `brand-intelligence/data/cn-yarn-glossary.json` と `docs/CN_YARN_GLOSSARY.md` |
| 顧客共有 | `docs/CUSTOMER_SHARING.md` |
| 調査承認ルール | `docs/RESEARCH_REVIEW_SOP.md` |
| 現在の業務データ | 各ブラウザ／WebView内。全社一元正本は未決定 |

## 10. 残る次段階

1. 正式な全社一元DB、認証、顧客別権限、監査ログ、バックアップ方針を決定する
2. 顧客ポータルPilotをサーバー側の顧客領域へ移行する
3. Daily Web／Androidへ同じ受信箱・Human Review導線を展開する
4. 本番公開版へrelease tagを付与する
5. 定期エクスポートと復元テストを運用記録する
6. 中国糸名辞書へ展示会・現物BOOKで確認した市場名をHuman Review後に追加する

## 11. 変更時チェック

- [ ] 本番・独立Sandbox・ローカルPilotを混同していない
- [ ] 読み取り元、書き込み先、受信箱、顧客スナップショットを別々に記載した
- [ ] 候補と承認済みを区別した
- [ ] 変更した全ソースのRevisionを台帳へ登録した
- [ ] V04 TOPからPhoto Capture、中国糸名辞書、糸検索、生地検査、原料相場、Daily、管理へ移動できる
- [ ] 外部画面への遷移でV04 iframeを入れ子にしていない
- [ ] 入力途中データの保存キーと写真非保存境界を記載した
- [ ] ゲージと本取りを別項目で保存し、糸のply数と混同していない
- [ ] 編み地イメージがマスター・受信箱・顧客共有データへ書き込まず、検討用であることを表示している
- [ ] 空欄で既存マスターを消さない
- [ ] 一時会社IDが同じ正式会社IDへ固定される
- [ ] PENDING候補を件数上限で削除しない
- [ ] 中国市場名を原料混率の確定値として扱っていない
- [ ] 中国糸名辞書の表示ラベルを「代表的な糸タイプ（例）」としている
- [ ] 中国糸名辞書からマスターを自動更新していない
- [ ] 顧客ポータルがマスター保存キーを直接読まない
- [ ] 根拠のない糸仕様をHuman Review承認で確定値へ昇格しない
- [ ] `organizationProfile` を正式会社IDへ保持し、会社間一時IDを正式IDへ解決する
- [ ] 販売数量未取得時は推定せず、MD提案を公開保留にする
- [ ] 商品はCONFIRMED、糸はPUBLISHEDかつ明示承認だけを共有する
- [ ] 顧客リクエストからマスターを自動更新しない
- [ ] 生地検査・原料相場が追記型かつPENDING_HUMAN_REVIEW・公開保留である
- [ ] 原料相場を自動換算・推定せず、ライブ価格フィードへ接続していない
- [ ] 接続先を暗黙に外部DBへ変更していない
- [ ] `python scripts/validate_system_registry.py` が成功した
- [ ] `python scripts/validate_yarn_glossary.py` が成功した
- [ ] `python scripts/validate_handoff_safety.py` が成功した
- [ ] `python scripts/validate_ui_state_guard.py` が成功した
- [ ] `python scripts/validate_customer_sharing.py` が成功した
- [ ] `python scripts/validate_photo_capture_install.py` が成功した
- [ ] `python scripts/validate_v04_monthly_md.py` が成功した
- [ ] `python scripts/validate_navigation_links.py` が成功した
- [ ] `python scripts/validate_knit_image.py` が成功した
- [ ] `python scripts/validate_operational_surfaces.py` が成功した
- [ ] `python scripts/validate_product_link_completion_20260809.py` が成功した
