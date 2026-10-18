# Knit Compass｜Brand MD Monitor 週次MD DRAFT
**対象：2026年10月12日〜18日｜集計実行：2026年10月19日**
**状態：DRAFT / PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED**
**方針：ANALYSIS_ONLY / NO_OFFICIAL_SITE_REVISIT / NO_NEW_COLLECTION**

## 判定とデータ品質
- 2026年10月3日付の[現行アクティブブランド正本](https://github.com/tianjinpipixia/knit-compass-v04-current/blob/main/public/brand-md-monitor-active-master-latest.json)を使用。**CORE20 / MONITORING20 / BACKGROUND24＝64ブランド**。**BR-00032 mysty woman** はINACTIVE/LEGACY_REFERENCEとして集計除外。**BR-00077 JOURNAL STANDARD relume** はアクティブに含める。
- 保存済みGemini日次MD分析7本は **64ブランド照合**と記録されるが、旧スコープの **BR-00032を含みBR-00077を含まない**。週次では正本へ再マッピングして mysty woman の信号を除外、relumeは `ROSTER_SCOPE_GAP`。この不足は推定補完しない。
- 収集元スナップショットの集計値は各日 **65ブランドを試行した未調整の原収集値**であり、これをアクティブ64の正確な商品件数と称さない。観測商品の日別増減を需要・販売数・新着投入量の増減に換算しない。
- 2026年10月18日現在のV04保存済み[監査結果](https://github.com/tianjinpipixia/knit-compass-v04-current/blob/main/public/brand-md-monitor-daily-observation-audit-latest.json)は公式40ブランドの完了 **0**・`PUBLISH_HOLD`。保存済みGeminiの`scan_status: OK`も「その解析で公式ソース信号を抽出できた」の意であり、完全巡回・全商品照合・発売確証ではない。
- 商品と価格は保存済みシグナルの記載のみ使用。`NEW / PREORDER / RESTOCK / SALE`は保存時の分類で、**初発売日、予約→発売確定、数量、元値との差額を自動推定しない**。同一SKUで分類ラベルが変わっても一次根拠がない限り`STATE_TRANSITION_UNVERIFIED`とする。
- 同一URLにSKUの代わりにブランドトップ/カテゴリURLしか残らない信号は「商品個別根拠」として計上しない。根拠日時は保存済みMD分析の生成UTCで、各商品の単独確認日時と同一とは限らない。
- 保存済み日次記録に`SOURCE_OFFLINE`や`SOURCE_STATE_CONFLICT`の確証がない対象について、その状態を新たに断定しない。`SOURCE_ACCESS_LIMITED`と日付欠損・状態ラベル揺れは別に表示。

## 直近7日の保存済み照合
- 2026-10-12: 原収集試行 65ブランド（当時の65ブランド範囲）／商品確認 24ブランド・628件／保存済みMD分析 46ブランド・220シグナル／分析生成 2026-10-11T23:55:49Z ／ [根拠ファイル](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-12-38185741342-1/data/brand-md-monitoring/gemini-md/2026-10-12/gemini-md-20261011T235549654401Z.json)（SHA 93c35617670e）
- 2026-10-13: 原収集試行 65ブランド（当時の65ブランド範囲）／商品確認 24ブランド・783件／保存済みMD分析 46ブランド・228シグナル／分析生成 2026-10-13T02:18:40Z ／ [根拠ファイル](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-13-38335813511-1/data/brand-md-monitoring/gemini-md/2026-10-13/gemini-md-20261013T021840702951Z.json)（SHA 5cca3d9f9e88）
- 2026-10-14: 原収集試行 65ブランド（当時の65ブランド範囲）／商品確認 24ブランド・777件／保存済みMD分析 45ブランド・223シグナル／分析生成 2026-10-13T23:58:21Z ／ [根拠ファイル](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-14-38486664188-1/data/brand-md-monitoring/gemini-md/2026-10-14/gemini-md-20261013T235821549064Z.json)（SHA 18b58de2ae28）
- 2026-10-15: 原収集試行 65ブランド（当時の65ブランド範囲）／商品確認 24ブランド・778件／保存済みMD分析 46ブランド・228シグナル／分析生成 2026-10-15T00:37:19Z ／ [根拠ファイル](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-15-38660507828-1/data/brand-md-monitoring/gemini-md/2026-10-15/gemini-md-20261015T003719675431Z.json)（SHA fcbabc0ba93a）
- 2026-10-16: 原収集試行 65ブランド（当時の65ブランド範囲）／商品確認 24ブランド・650件／保存済みMD分析 46ブランド・228シグナル／分析生成 2026-10-15T23:18:15Z ／ [根拠ファイル](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-16-38822136246-1/data/brand-md-monitoring/gemini-md/2026-10-16/gemini-md-20261015T231815350416Z.json)（SHA 965c84cbc9f8）
- 2026-10-17: 原収集試行 65ブランド（当時の65ブランド範囲）／商品確認 24ブランド・1050件／保存済みMD分析 46ブランド・228シグナル／分析生成 2026-10-17T09:26:20Z ／ [根拠ファイル](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-17-39020733955-1/data/brand-md-monitoring/gemini-md/2026-10-17/gemini-md-20261017T092620700811Z.json)（SHA af18ad410c11）
- 2026-10-18: 原収集試行 65ブランド（当時の65ブランド範囲）／商品確認 14ブランド・769件／保存済みMD分析 45ブランド・209シグナル／分析生成 2026-10-17T22:39:38Z ／ [根拠ファイル](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-18-39075564811-1/data/brand-md-monitoring/gemini-md/2026-10-18/gemini-md-20261017T223938452665Z.json)（SHA 964acba04544）

上記の日次件数は**重複観測を含む日別記録**で、7日間のユニークSKU数・販売数ではない。保存済み分析からアクティブ64の`analysis-OK`の日数とSKU根拠有無を、以下の台帳に整理した。

## 週次の観察（FACT と INTERPRETATIONを区別）
**FACT（保存済み商品記録）**
- [ROPÉ PICNIC レースレイヤードVネックニット](https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM56320) 5,995円：レース複合型の保存済みシグナルに NEW / PREORDER ラベルが混在。いずれも*最終発売日を立証しない*。
- [VIS オフショルダーシャギーニット](https://www.junonline.jp/vis/product/tops/knit-sweater/BVM46220) 5,929円、[静電気防止リブニット](https://www.junonline.jp/vis/product/tops/knit-sweater/BVM66060) 4,389円：毛羽意匠と機能表示を同じブランドで観測。
- [Te chichi 帯電防止ダブルジップ衿付きニットブルゾン](https://www.canshop.jp/ap/item/i/A1CAN000A5G9) 8,800円：機能表示を持つ外衣型の候補。
- [RIVE DROITE ウール100 NEWボトルネックニット](https://www.palcloset.jp/display/item/RDZ1062405A0002/) 15,950円、[Whim Gazette モヘヤラメニット](https://www.palcloset.jp/display/item/WGZ1062505A0001/) 23,100円：ウール・モヘヤなど原料名と表面訴求が保存済み。
- [natural couture ラメペプラム](https://www.palcloset.jp/display/item/0362050380/) 5,940円、[GALLARDAGALANTE ペプラムレース](https://www.palcloset.jp/display/item/GGZ1062305A0008/) 28,600円：同じ形態テーマに価格階層の違う掲載例。
- [MUJI Labo カシミヤ（婦人カテゴリ）](https://www.muji.com/jp/ja/store/cmdty/section/T10013) では自然色カシミヤ／リャマ混／再生ウール混のカテゴリ掲載を保存。ただしこのURLはカテゴリ単位で、商品個別の証拠URLではない。

**INTERPRETATION（素材開発仮説・正式な市場増加判定ではない）**
1. 12〜16Gの**意匠と形状保持**：レースレイヤード、ペプラム、ZIP衿、金釦などにPBT芯・プレーティング・ミラノ/総針の比較試編を検討。強度・伸長回復・端部安定性は試験前。
2. 8〜12Gの**軽量毛羽二系列**：合繊シャギー（洗える、帯電、毛羽付着、ピリング）と上質ウール/FOX/モヘヤ系（軽さ・風合い・抜け毛）を別評価。KC既存のFezario FOXやBOOK毛羽糸との接続は仕様照合待ち。
3. 14G前後の**実用機能×装飾**：帯電防止やイージーケアを意匠面と両立。KC既存のAC100 Compact・ClimaVeilは仕様適合を再判定してから候補化。
4. **天然素材名と価格階層**：メリノ/カシミヤ/モヘヤ/ウール100%を価格差として説明する方向は観測可能。ただし同一構成比較・需要増加までは立証できない。

## アクティブ64ブランド週次台帳
各行の「MD照合x/7」は保存済み分析の取得状態であり、**完全収集率ではない**。「主題」は商品名・保存テキストからの素材開発仮説。掲載商品は最大3件で、個別URLを保存できた商品だけを記す。

| ブランド | 保存済み観測状態 | 注目商品（最大3件、公式個別URL） | 主題・素材開発への示唆 | 次の日次収集への確認事項 |
|---|---|---|---|---|
| BR-00001 UNIQLO | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00002 GU | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 毛羽・起毛／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00003 MUJI | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00004 ROPÉ PICNIC | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [レースレイヤードVネックニット](https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM56320) 5,995円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[ハイネックショートニットプルオーバー](https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM56110) 5,489円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[片畔ショート丈ニットプルオーバー](https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM56120) 5,489円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00005 VIS | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [スカーフ付きポロ襟ニット](https://www.junonline.jp/vis/product/tops/knit-sweater/BVM66110) 6,589円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[オフショルダーシャギーニット](https://www.junonline.jp/vis/product/tops/knit-sweater/BVM46220) 5,929円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[フラワーチュールドッキングニット](https://www.junonline.jp/vis/product/tops/knit-sweater/BVM46260) 7,689円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00006 GLOBAL WORK | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00007 LOWRYS FARM | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00008 studio CLIP | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00009 niko and ... | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00010 earth music&ecology | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [earth music&ecology Vネックオーバーサイズロングカーディガン](https://stripe-club.com/brand/earth1999/item/1001M26H0060)（保存時ラベル：DESIGN、最終記録 2026-10-17）<br>[earth music&ecology アニマルパターンニットカーディガン](https://stripe-club.com/brand/earth1999/item/1001M26H0063)（保存時ラベル：DESIGN、最終記録 2026-10-17）<br>[earth music&ecology ハンドニットカーディガン](https://stripe-club.com/brand/earth1999/item/1001M26G0010)（保存時ラベル：MATERIAL、最終記録 2026-10-17） | 構築・装飾／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00011 Green Parks | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [Green Parks daily chic スウェットニット](https://stripe-club.com/brand/greenparks/item/1006H26G0011)（保存時ラベル：NEW、最終記録 2026-10-18）<br>[Green Parks effortless casual ここち配色リングドットカーディガン](https://stripe-club.com/brand/greenparks/item/1006G26H0022)（保存時ラベル：NEW、最終記録 2026-10-18）<br>[Green Parks effortless casual 【WEB限定カラーあり】ここちクルーネックニットプルオーバー](https://stripe-club.com/brand/greenparks/item/1006G26H0021)（保存時ラベル：NEW、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00012 OPAQUE.CLIP | PARTIAL_RETRIEVAL / MD照合 6/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00013 index | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00014 SHOO・LA・RUE | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00015 grove | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00016 ikka | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 毛羽・起毛／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00017 coen | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 天然素材／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00018 DoCLASSE | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [ネックビジュー・クルーカーディガン](https://www.doclasse.com/item/detail/1_1_33287/480) 5,990円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[ダブルフェイスニット・オーバーカーディガン](https://www.doclasse.com/item/detail/1_1_33319/090) 10,700円（保存時ラベル：SALE、最終記録 2026-10-18）<br>[模様編み・シアーニットカーディガン](https://www.doclasse.com/item/detail/1_1_33171/490) 4,290円（保存時ラベル：SALE、最終記録 2026-10-18） | 構築・装飾／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00019 any SiS | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00021 LEPSIM | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00022 LAKOLE | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00023 JEANASIS | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00024 BAYFLOW | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00025 HARE | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00027 Heather | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00028 PAGEBOY | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00030 A part by | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00031 Elura | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00033 Andemiu | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00035 AMERICAN HOLIC | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [AMERICAN HOLIC 【予約】【バイパチ】スキッパー襟付きルーズニット](https://stripe-club.com/brand/american-holic/item/100HA26H0128) 3,990円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[AMERICAN HOLIC 【バイパチ】Vネック配色ニットコーディガン](https://stripe-club.com/brand/american-holic/item/100HA26H0044) 4,990円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[AMERICAN HOLIC 【顔映え】Vネックコクーンニット](https://stripe-club.com/brand/american-holic/item/100HA26H0094) 3,990円（保存時ラベル：SALE、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00036 YECCA VECCA | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [YECCA VECCA 金釦ラッフル5分袖カーディガン](https://stripe-club.com/brand/yeccavecca/item/1007A26F0010)（保存時ラベル：NEW、最終記録 2026-10-18）<br>[YECCA VECCA 【2点SET】ラッフルキャミセットニット](https://stripe-club.com/brand/yeccavecca/item/1007A26F0009)（保存時ラベル：NEW、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／機能・ケア（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00039 23区 | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [【先行予約】フォックスカシミヤファー ゴールドボタン カーディガン](https://crosset.onward.co.jp/items/KRWOLW0561) 34,980円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[ボイルドウールコンビ ジップデザイン ニット](https://crosset.onward.co.jp/items/KRWOLW0557) 22,990円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[スーパーラムズムリネ オフタートル ニット](https://crosset.onward.co.jp/items/KRWOLW0565) 26,950円（保存時ラベル：NEW、最終記録 2026-10-18） | 毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00040 ICB | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00041 自由区 | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00042 組曲 | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [【先行予約・WEB限定】ファー襟付 ニットブルゾン](https://crosset.onward.co.jp/items/KRWXLW0562) 17,930円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【先行予約・前後着用可】ウールカシミヤミックス ハイネックニット](https://crosset.onward.co.jp/items/KRWXLW0551) 13,970円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【WEB限定】ブラッシングニット プルオーバー](https://crosset.onward.co.jp/items/KRWXLW0558) 14,960円（保存時ラベル：NEW、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00047 UNFILO | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00049 INDIVI | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／毛羽・起毛／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00050 UNTITLED | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00051 NATURAL BEAUTY BASIC | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [＜第4回 CLASSY.お仕事名品大賞2026AW＞「トップス賞」ストライプフリルネックニット](https://mix.tokyo/products/0176270952) 8,998円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[＜Oggi11月号掲載＞＜WEB限定カラー：ネイビー系＞＜ちょうど、いい服＞“それどこの？”褒められ配色カーディガン](https://mix.tokyo/products/0176275910) 7,491円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[シアーフレアカフスリブニット](https://mix.tokyo/products/0176270900) 7,491円（保存時ラベル：NEW、最終記録 2026-10-18） | 構築・装飾／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00052 SENSE OF PLACE | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00053 B.C STOCK | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00054 SLOBE IENA | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／毛羽・起毛／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00055 green label relaxing | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側の取得障害を修復し公式SKU根拠URL・確認日時を保存。 |
| BR-00056 Spick & Span | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00057 IÉNA | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00058 Te chichi | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [【帯電防止】ダブルジップ衿付きニットブルゾン](https://www.canshop.jp/ap/item/i/A1CAN000A5G9) 8,800円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[フェザーカーディガン](https://www.canshop.jp/ap/item/i/A1CAN000A5JU) 6,930円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[ケーブルパッチワーク調ニットプルオーバー](https://www.canshop.jp/ap/item/i/A1CAN000A5KJ) 6,600円（保存時ラベル：NEW、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00059 ANY | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00060 MUJI Labo | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 天然素材／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00062 Mila Owen | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 構築・装飾／毛羽・起毛／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 日次側で公式個別SKUのURL・商品仕様・確認日時を保存。 |
| BR-00063 ROPÉ | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [【J'aDoRe・店舗限定サイズ】カシミヤ100% ボートネックドルマンスリーブニット](https://www.junonline.jp/rope/product/tops/knit-sweater/GGM36090) 29,700円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【J'aDoRe・店舗限定サイズ】カシミヤブレンドトグル釦クルーネックニット](https://www.junonline.jp/rope/product/tops/knit-sweater/GGM36130) 24,200円（保存時ラベル：NEW、最終記録 2026-10-18）<br>[【J'aDoRe・店舗限定サイズ】ビジュー2WAYニットプルオーバー(襟とカフス取り外し可能)](https://www.junonline.jp/rope/product/tops/knit-sweater/GGM36160) 28,600円（保存時ラベル：NEW、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00064 ADAM ET ROPÉ | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 7/7日 | [YAK Vネックスリットニット](https://www.junonline.jp/adam-et-rope-femme/product/tops/knit-sweater/GAM26220) 19,800円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【WEB限定】・【定番】WOOL混リブタートルニット](https://www.junonline.jp/adam-et-rope-femme/product/tops/knit-sweater/GAM56510) 8,580円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[バイカラー2WAYダンボールニットプルオーバー](https://www.junonline.jp/adam-et-rope-femme/product/tops/knit-sweater/GAM26360) 18,700円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一品番の予約/新着/SALE、混率・色・サイズ・元値/売価を日次側で再記録。 |
| BR-00065 GALLARDAGALANTE | PARTIAL_RETRIEVAL / MD照合 6/7日・直接商品記録 6/7日 | [【10/15(木)10:00～予約開始】【CHIKAコラボカラー】オーバータートルニット](https://www.palcloset.jp/display/item/GGZ1062405A0003/) 17,820円（保存時ラベル：PREORDER、最終記録 2026-10-17）<br>[【10/23(金)12:00～予約開始】【AYUMIコラボ】モヘアシルクボートニットプルオーバー](https://www.palcloset.jp/display/item/GGZ1062405A0004/) 28,600円（保存時ラベル：PREORDER、最終記録 2026-10-17）<br>[ハンドニットタンク](https://www.palcloset.jp/display/item/GGZ1062305A0010/) 33,000円（保存時ラベル：NEW、最終記録 2026-10-17） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00066 Whim Gazette | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [【Drawing numbers】接結ルーズタートルニット](https://www.palcloset.jp/display/item/DNZ1062405A0001/?cl=0510&b=whimgazette&ss=) 30,800円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[花柄ニット](https://www.palcloset.jp/display/item/WGZ1062405A0005/?cl=0130&b=whimgazette&ss=) 44,000円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[モヘヤラメニットプルオーバー](https://www.palcloset.jp/display/item/WGZ1062505A0001/?cl=0220&b=whimgazette&ss=) 23,100円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00067 LOUNGEDRESS | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [《洗える》オフショルニット](https://www.palcloset.jp/display/item/LDZ1062305A0009/?cl=0999&b=loungedress&ss=) 18,700円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[《1枚着でもレイヤードでも》シアータートル](https://www.palcloset.jp/display/item/LDZ1062105A0001/?cl=0110&b=loungedress&ss=)（保存時ラベル：NEW、最終記録 2026-10-18）<br>[《セットアップ可》フロッキーロゴプリントニット](https://www.palcloset.jp/display/item/LDZ1062405A0001/?cl=0900&b=loungedress&ss=) 17,600円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00068 RIVE DROITE | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [ウール100NEWボトルネックニット](https://www.palcloset.jp/display/item/RDZ1062405A0002/?cl=0610&b=rivedroite&ss=) 15,950円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【WEB限定】MIXヤーンペプラムニット](https://www.palcloset.jp/display/item/RDZ1062305A0004/?cl=0800&b=rivedroite&ss=) 13,200円（保存時ラベル：SALE、最終記録 2026-10-18）<br>[ウォッシャブルタートルニット](https://www.palcloset.jp/display/item/RDZ1062305A0007/) 15,950円（保存時ラベル：FUNCTION、最終記録 2026-10-17） | 構築・装飾／毛羽・起毛／天然素材／機能・ケア／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00069 DOUDOU | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [ヘンリーネックリブニット](https://www.palcloset.jp/display/item/DDZ1061105A0001/?cl=0999&b=doudou&ss=) 8,800円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[スクエアニットロングスリーブプルオーバー](https://www.palcloset.jp/display/item/DDZ1061105A0015/?cl=0920&b=doudou&ss=) 8,690円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【WEB限定】 ボトルネックアシメデザインニット](https://www.palcloset.jp/display/item/DDZ1062205A0001/?cl=0101&b=doudou&ss=) 7,590円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00070 SHENERY | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [【セットフェア対象】【Silhouette Hacker】ディープVネックブークレニット](https://www.palcloset.jp/display/item/SNZ1062305A0005/?cl=0110&b=shenery&ss=) 14,300円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【新色アイボリー&サーモンピンク】シアーギャザーニット](https://www.palcloset.jp/display/item/SNZ1062105A0002/?cl=0710&b=shenery&ss=) 14,850円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【リバイバル】ラクーンペプラムカーディガン](https://www.palcloset.jp/display/item/SNZ1062305A0001/?cl=0750&b=shenery&ss=) 17,820円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00071 un dix cors | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [【2点SET】ニットセットレイヤードプルオーバー](https://www.palcloset.jp/display/item/UOZ1062305A0008/?cl=0900&b=croisiere&ss=) 8,910円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[ショルダースタッズプルオーバー](https://www.palcloset.jp/display/item/UOZ1062205A0003/?cl=0110&b=croisiere&ss=) 6,930円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【一部WEB限定カラー】【２点SET】重ね着プルオーバー](https://www.palcloset.jp/display/item/UOZ1062305A0010/?cl=0450&b=croisiere&ss=) 7,700円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00072 La boutique BonBon | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [【新色登場！・チクチクしない】リブタートルニット](https://www.palcloset.jp/display/item/LBZ1062405A0008/?cl=0800&b=laboutiquebonbon&ss=) 13,893円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[ウール100強縮Vネックニット](https://www.palcloset.jp/display/item/LBZ1062405A0005/?cl=0700&b=laboutiquebonbon&ss=) 17,820円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【お気に入り総選挙2位】ケーブルニットカーディガン](https://www.palcloset.jp/display/item/LBZ1062305A0006/?cl=0570&b=laboutiquebonbon&ss=) 16,940円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00073 natural couture | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [〈canami〉袖口ハート釦ボートネックリブニット](https://www.palcloset.jp/display/item/NTU1062305A0008/?cl=0700&b=naturalcouture&ss=) 5,390円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[ラメペプラムニット](https://www.palcloset.jp/display/item/0362050380/?cl=0920&b=naturalcouture&ss=) 5,940円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[裾レースノースリニット](https://www.palcloset.jp/display/item/NTU1062305A1200/?cl=0110&b=naturalcouture&ss=) 3,960円（保存時ラベル：PREORDER、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／天然素材／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00074 DISCOAT | ANALYSIS_OBSERVED_NOT_FULL_COVERAGE / MD照合 7/7日・直接商品記録 6/7日 | [マルチボーダータートルプルオーバー](https://www.palcloset.jp/display/item/DCZ1062205A0012/?cl=0800&b=discoat&ss=) 4,950円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【Enlude/新色追加！/ロングシーズン着れる】スウェットライクヘンリーネックニット《ユニセックス》](https://www.palcloset.jp/display/item/DCE2062105A0001/?cl=0770&b=discoat&ss=) 6,600円（保存時ラベル：PREORDER、最終記録 2026-10-18）<br>[【Enlude】モールヘンリーネックニット《ユニセックス》](https://www.palcloset.jp/display/item/DCE2062305A0001/?cl=0800&b=discoat&ss=) 7,700円（保存時ラベル：NEW、最終記録 2026-10-18） | 構築・装飾／毛羽・起毛／形・編地（編地・糸候補との照合は仮説） | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| BR-00075 ZARA | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側でTHE NEW・ニット・Special Pricesの同一SKU/元値/売価/色/確認時刻を保存。 |
| BR-00076 SNIDEL | SOURCE_ACCESS_LIMITED / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | 日次側でNEW/予約/SALE/SOLD OUT、ニット/カーデの同一SKU状態・発売予定日を保存。 |
| BR-00077 JOURNAL STANDARD relume | ROSTER_SCOPE_GAP / MD照合 0/7日・直接商品記録 0/7日 | SKU単位の保存済み公式URLなし（商品差分判定不可） | 判断材料不足（編地・糸候補との照合は仮説） | BR-00077 relumeを日次MD分析の対象へ復帰し、公式商品URL・保存日時を記録。 |

## PAL系10ブランド：ランキングの品質
保存済み信号に`RANKING`ラベルがあっても、それが**同じランキング母集団の同一SKU数値順位**を示さない限り、上昇・下降は算定不可。価格数値を順位と誤認しない。

| PALブランド | 日次MDソース照合 | 収集済み信号の範囲 | 順位の保存状態 | 次の日次収集への対応 |
|---|---|---|---|---|
| GALLARDAGALANTE | 6/7日 | 保存済み信号 30件・SKU根拠 6種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| Whim Gazette | 7/7日 | 保存済み信号 35件・SKU根拠 11種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| LOUNGEDRESS | 7/7日 | 保存済み信号 34件・SKU根拠 10種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| RIVE DROITE | 7/7日 | 保存済み信号 32件・SKU根拠 9種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| DOUDOU | 7/7日 | 保存済み信号 33件・SKU根拠 10種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| SHENERY | 7/7日 | 保存済み信号 34件・SKU根拠 8種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| un dix cors | 7/7日 | 保存済み信号 34件・SKU根拠 10種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| La boutique BonBon | 7/7日 | 保存済み信号 34件・SKU根拠 9種 | 数値順位記録 3件／同一SKU順位比較 1組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| natural couture | 7/7日 | 保存済み信号 33件・SKU根拠 13種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |
| DISCOAT | 7/7日 | 保存済み信号 33件・SKU根拠 19種 | 数値順位記録 0件／同一SKU順位比較 0組 | 同一SKUの順位番号・ランキング種別/更新日時、予約→発売・SALE元値を日次側で保存。 |

## ZARA / SNIDEL 先行MD指標
- **ZARA**：対象7日分の保存済みGemini日次MDは `SOURCE_ACCESS_LIMITED`・商品別`md_signals=0`。THE NEW / レディースニット / Special Pricesの**週次入替・価格・値下げ深度・SKU回転は判定不能**。次回の日次収集で3入口別のSKU一覧、観測日時、色とサイズ、通常/SALE価格、前回差分、元値を保存すること。※過去週の商品例を今週の観測には転用しない。
- **SNIDEL**：同様に7日分 `SOURCE_ACCESS_LIMITED`・商品別`md_signals=0`。NEW / PREORDER / SALE / SOLD OUT / ニット / カーディガンの**予約→発売・フリル/ペプラム/アーガイルの増減は判定不能**。次の日次収集で品番・発売予定日・素材混率・機能/意匠・色・状態・確認日時を保存。

## Brand64外・週次補助ブランド（アクティブ集計には含めない）
| ブランド | 対象週の保存済み日次証拠 | 次の日次収集への確認事項 |
|---|---|---|
| PLST | `SOURCE_DAILY_EVIDENCE_NOT_FOUND`（今回照合した週次用日次MDの保存先では該当7日分を特定できず） | 公式個別SKU URL、確認日時、価格/混率/機能・ランキング/再入荷を**日次収集側**で記録。 |
| FRAY I.D | `SOURCE_DAILY_EVIDENCE_NOT_FOUND`（今回照合した週次用日次MDの保存先では該当7日分を特定できず） | 公式個別SKU URL、確認日時、価格/混率/機能・ランキング/再入荷を**日次収集側**で記録。 |
| H&M | `SOURCE_DAILY_EVIDENCE_NOT_FOUND`（今回照合した週次用日次MDの保存先では該当7日分を特定できず） | 公式個別SKU URL、確認日時、価格/混率/機能・ランキング/再入荷を**日次収集側**で記録。 |
| COS | `SOURCE_DAILY_EVIDENCE_NOT_FOUND`（今回照合した週次用日次MDの保存先では該当7日分を特定できず） | 公式個別SKU URL、確認日時、価格/混率/機能・ランキング/再入荷を**日次収集側**で記録。 |
| MANGO | `SOURCE_DAILY_EVIDENCE_NOT_FOUND`（今回照合した週次用日次MDの保存先では該当7日分を特定できず） | 公式個別SKU URL、確認日時、価格/混率/機能・ランキング/再入荷を**日次収集側**で記録。 |
| NOLLEY'S | `SOURCE_DAILY_EVIDENCE_NOT_FOUND`（今回照合した週次用日次MDの保存先では該当7日分を特定できず） | 公式個別SKU URL、確認日時、価格/混率/機能・ランキング/再入荷を**日次収集側**で記録。 |
| BEAUTY&YOUTH | `SOURCE_DAILY_EVIDENCE_NOT_FOUND`（今回照合した週次用日次MDの保存先では該当7日分を特定できず） | 公式個別SKU URL、確認日時、価格/混率/機能・ランキング/再入荷を**日次収集側**で記録。 |

## 次回の優先修正とHuman Review
1. **ROSTER_SCOPE_CONFLICT**：64ブランド正本のBR-00077 relumeをGemini日次MD分析に含め、INACTIVEのBR-00032を除く。収集側の65ブランド原件数は履歴として保持。集計時にアクティブ数へ読み替えない。
2. **SOURCE_ACCESS_LIMITED**：ZARA・SNIDEL、GLOBAL WORK、LOWRYS FARM、PALの一部等を日次収集側で復旧。週次は再収集しない。
3. **OFFICIAL_URL / VERIFIED_AT不足**：ブランド/カテゴリURLだけではSKU正式根拠にならない。日時・品番・混率・色・発注条件の欠損を別台帳へ。
4. **PALランキング**：順位の数値、ランキングの母集団・更新日時・クーポン情報を保存してから比較する。SALE元値未保存なら値下げ深度は算定不可。
5. **状態ラベルの差**：同一品番でNEW / PREORDER / RESTOCK等が混在する記録を`STATE_TRANSITION_UNVERIFIED`としてHuman Review。発売確定の自動判定をしない。
6. **月次実行**：2026年10月19日は月初最初の週次ではないため月次DRAFTは作成しない。月初初回週次で前月の日次・週次正本を再利用する。
7. **公開ゲート**：本報告はDRAFT、正式公開/営業配布/最新ポインター更新は行わず、原典・対象範囲・判断を人が承認する。

## 保存根拠
- `2026-10-12` [保存済みGemini日次MD分析](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-12-38185741342-1/data/brand-md-monitoring/gemini-md/2026-10-12/gemini-md-20261011T235549654401Z.json)、原収集run=未確定
- `2026-10-13` [保存済みGemini日次MD分析](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-13-38335813511-1/data/brand-md-monitoring/gemini-md/2026-10-13/gemini-md-20261013T021840702951Z.json)、原収集run=未確定
- `2026-10-14` [保存済みGemini日次MD分析](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-14-38486664188-1/data/brand-md-monitoring/gemini-md/2026-10-14/gemini-md-20261013T235821549064Z.json)、原収集run=未確定
- `2026-10-15` [保存済みGemini日次MD分析](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-15-38660507828-1/data/brand-md-monitoring/gemini-md/2026-10-15/gemini-md-20261015T003719675431Z.json)、原収集run=未確定
- `2026-10-16` [保存済みGemini日次MD分析](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-16-38822136246-1/data/brand-md-monitoring/gemini-md/2026-10-16/gemini-md-20261015T231815350416Z.json)、原収集run=未確定
- `2026-10-17` [保存済みGemini日次MD分析](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-17-39020733955-1/data/brand-md-monitoring/gemini-md/2026-10-17/gemini-md-20261017T092620700811Z.json)、原収集run=未確定
- `2026-10-18` [保存済みGemini日次MD分析](https://github.com/tianjinpipixia/knit-compass-photo-capture/blob/brand64%2Fgemini-md-2026-10-18-39075564811-1/data/brand-md-monitoring/gemini-md/2026-10-18/gemini-md-20261017T223938452665Z.json)、原収集run=未確定

*閲覧対象：Owner限定。保存済み日次の整理であり、現在の店頭情報や実売を証明しない。*