# Brand64 日次観測サマリー — 2026-08-30

- 観測モード: DAILY_LIVE
- アクティブ64ブランド軽量確認: 64 / 64
- 深掘り: 3ブランド（Whim Gazette / ZARA / SNIDEL）
- 当日CURRENT_FIRST_SEEN: 1件
- RETROSPECTIVE_BACKFILL: 1件
- EXISTING_PRODUCT_STATE_UPDATE: 1件
- 正式商品候補: 2件
- 未解消観測ギャップ: 0日
- 販売数量: 推定しない
- 公開境界: PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED

## 本日の正式商品候補

1. **ZARA / クロスバック ニットトップス / 3433/006/800** — 公式ニットトップス一覧でNEW、個別ページで¥4,390・ブラック・品番を確認。発売日は明示されていないため推測せず、8/30監視上のCURRENT_FIRST_SEENとして保存。
2. **SNIDEL / ペプラムニットジャケット / SWNJ264260** — 公式カテゴリで予約・new、個別ページで¥19,800、9月上旬出荷予定、混率、IVR/BLK/BURを確認。当日以前からページが存在した可能性があるためRETROSPECTIVE_BACKFILLとして保存。

## 状態差分

- **Whim Gazette / WGZ1032306A0002**: 通常¥16,500に対し¥14,850表示、10%OFF案内、在庫なし表示を公式個別ページで確認。既存商品なので新商品件数へ加算せず、価格・販促・掲載状態差分として保持。

## MD差分

- ZARA: 背面開き・クロスコード・フィットシルエットのNEW。12G〜16Gで伸縮性と形態保持を確認する方向。
- SNIDEL: ヴィスコース混のペプラム構築＋チュールレース接続。高〜中ゲージでペプラム形状保持と異素材接続を継続確認。
- 販促: 値引き・クーポン・在庫状態は商品需要や販売数量の根拠から分離。

## データ境界

公式個別商品ページで確認できない項目は推測で補完していません。公式発売日が不明な商品はSOURCE_DATE_UNAVAILABLE、遡及時点が確定できない商品はRETROSPECTIVE_TIMING_UNCERTAINとして保持します。404・掲載終了が将来発生しても既存レコードを削除せず最終確認情報を保持します。

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
- 実データ再集計: `data/brand-md-monitoring/2026-08-30-retrospective-season-backfill-report.json`
<!-- KC_RETROSPECTIVE_SEASON_BACKFILL:END -->
