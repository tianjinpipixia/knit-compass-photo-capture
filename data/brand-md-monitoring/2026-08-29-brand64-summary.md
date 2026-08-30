# Brand64 Daily Summary — 2026-08-29

- 観測モード: `DAILY_LIVE`
- アクティブ64ブランド軽量確認: **64 / 64**
- 深掘り: **3ブランド** — DOUDOU / La boutique BonBon / natural couture
- 当日first-seen正式候補: **2件**
- 既存商品の状態・識別情報更新: **1件**
- 遡及商品候補: **0件**
- 未処理日: **なし**（8/22・8/26は既に遡及補完済み）
- 販売数量: **推定しない**
- 公開境界: `PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED`

## 当日正式候補

### La boutique BonBon — 当日first-seen 2件
公式個別商品ページで `LBZ1062405A0003`、`LBZ1062405A0004` を本日発売・予約として確認。ウール／カシミヤのヘアリー表面を、ワンショルリボン、FUR加工衿へ展開。条件付き10%OFFクーポンは商品セール価格とは分離した。

### La boutique BonBon — 既存商品の状態更新1件
`LBZ1062405A0007` は8/20保存済みの「ラメヘアリー ウールカシミヤ混オフショルダーニット」¥28,930と同一商品。8/29は予約開始・品番・個別URL・混率・色を確定した状態更新として接続し、当日first-seen件数から除外する。商品コピーにFOX混表現がある一方、アイテム詳細の混率表は「毛80%・ポリエステル11%・カシミヤ9%」。不明なFOX混率は推測せず、詳細表を正式混率として保存し `SOURCE_MATERIAL_DESCRIPTION_CONFLICT` を保持する。

## 差分のみ深掘りしたその他ブランド

- **natural couture**: 公式キャンペーンで8/29 00:00〜8/31 23:59の15%OFF開始を確認。フラワースパンコールポケ付きカーディガン、ふわふわファーオフショル風ニット等の価格状態差分として記録し、新商品・販売数量とは分離。
- **DOUDOU**: 前日10:05 JST時点で12:00開始前だった予約群が現在は予約・クーポン対象へ移行。個別確認した `DDZ1061105A0015` は2026年3月・5月のレビュー履歴があり既存SKUと判断できるため、当日新規・遡及商品には登録しない。

## 重点ブランド軽量確認

ZARA、SNIDEL、GLOBAL WORK、NATURAL BEAUTY BASIC、VIS、ROPÉ PICNIC、PAL系を優先して公式導線を確認。ZARA Special Pricesの大幅値下げは継続確認したが、8/28からの新たな価格差分とは確定しないため当日差分へ昇格しない。その他、8/29付の婦人ニット差分を公式個別商品ページまで確定できないブランドは `SOURCE_FRESHNESS_LIMITED` を含む観測境界を維持する。

## MD差分

- 8G〜12G: ウール／カシミヤの上質毛羽をリボン・衿・オフショル等のフェミニン意匠へ接続。
- ラメ×ヘアリー: 意匠表現と正式混率を分離し、商品コピーと混率表の競合を監査対象として残す。
- 販促補正: 条件付き10%OFF、15%OFFキャンペーン、予約クーポンを商品需要の直接証拠にしない。
- 時刻・再露出補正: 前日開始前→当日予約表示への変化を新商品first-seenと混同しない。

## データ境界

不明項目は `NOT AVAILABLE` のまま保持。公式個別商品ページで確定できない商品は正式候補にしない。404・掲載終了が今後発生した場合も既存レコードは削除せず、最終確認情報を `SOURCE_OFFLINE` 等で保持する。product_id / product_code / official_url を優先し、過去レコードに強い識別子がない場合はブランド＋正規化商品名＋上代でも重複照合する。

<!-- KC_RETROSPECTIVE_SEASON_BACKFILL:START -->
## 2026年春先遡及（当日差分とは別集計）

- 対象期間: `2026-01-01/2026-04-30`
- 当日春先遡及: **0件**
- 春先遡及累積: **0件**
- 実行条件: 当日64ブランド確認完了、かつ未処理日なしの場合のみ
- 区分: `RETROSPECTIVE_BASELINE`（当日新規・通常の遡及候補には加算しない）
- 根拠: 公式個別商品ページのみ。不明項目は推測しない
- 公開境界: `PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED`
- 保存先: `data/brand-md-monitoring/2026-spring-retrospective-baselines.json`
- 実データ再集計: `data/brand-md-monitoring/2026-08-29-retrospective-season-backfill-report.json`
<!-- KC_RETROSPECTIVE_SEASON_BACKFILL:END -->
