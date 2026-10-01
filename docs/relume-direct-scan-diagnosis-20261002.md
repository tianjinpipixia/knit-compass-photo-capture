# relume 公式巡回0件の調査（2026-10-02 JST）

## 結論
10月1日の0件は、アクセス制限や商品消失ではなく、Baycrewsアダプターが商品リンクを相対URLに限定していたため。保存HTMLの商品リンクは絶対URLで、対象カードをすべて除外していた。新規登録されたrelumeの検索入口は正しくWOMEN・店舗0498・ニット231／カーディガン223を指定していた。

53件の累積記録は9月30日の公式商品ページ調査から取り込まれた別経路の結果。過去53件が同じ日次アダプターで取得できたという履歴は確認されていないため、「10月1日に公式サイトの構造が変わった」とは断定しない。

## 根拠
- V04 main: `5adbbbe9e71c3c06d67a134defe9f654130506ad`
- 商品正本・収集コード: `tianjinpipixia/knit-compass-photo-capture`。V04の `config/product-data-governance.json` が同リポジトリの `brand64/flash-feed` を参照。
- 10月1日の実行: [36793888044](https://github.com/tianjinpipixia/knit-compass-photo-capture/actions/runs/36793888044)、実行ソース `9a1d999c54b8090dc9546757c8ca31063a8af233`
- 調査・修正のベース: Photo Capture main `9a5476f4594881bb53524584370b342e6193aeeb`
- 最終artifact `11132958041` の `coverage-state.json` では、relumeのerrorsは空、scan_statusはLINK_CANDIDATES_OBSERVED、未確認2件は商品ではなくカテゴリナビの「ニット／セーター」「カーディガン」。
- 09:00 JST巡回の保存HTMLをartifactから取得し、SHA256を実バイトと照合:
  - ニット: `5e649dc2136398c11ea3427a9218d81626952e32e18d53a438a19ebdb893b784`
  - カーディガン: `2ca61097346a80b3fdae14467c3dfab110ee69ae048c86e55dc1eecdcf321a42`
- 保存ページには対象詳細URLを持つアンカー90／61件が存在。旧アダプターは0件。リンク例は `https://baycrews.jp/item/detail/js-relume/cutsew/26080462867030?q_sclrcd=007` で、旧 `^/item/detail/...` 正規表現に一致しない。

## 切り分け
| 箇所 | 結果 |
|---|---|
| アクセス制限 | 当該巡回に403・認証challengeなし。現在も同じ監視UAでHTTP 200。回避処理なし。 |
| 検索経路 | 店舗0498・WOMEN・カテゴリ231／223の入口は有効。9月30日は `/item/list/js-relume/category/cutsew/ladys?q_mccate=231&qPage=0` 等の別経路。 |
| selector／URL判定 | 絶対hrefを相対hrefの正規表現で除外。これが0件化の直接原因。 |
| 商品名・価格 | 旧処理は親の全文からブランド名と円記号で商品名を切り出す方式。商品カード単位のbrand・itemName・price・statusへ限定。 |
| 正規化 | 色違いは `q_sclrcd` で分かれるが商品IDはパス。従来のBaycrewsパス単位の重複排除を維持。 |
| pagination | 次矢印は `class="next icon-chevron-right"` でテキストとrelが空。旧処理は未認識。qPageが1ずつ進み、他の検索条件が完全一致する場合だけ継続。 |
| coverage | 未確認ナビ2件でもsuccessful_page_urlsに記録される既存挙動があるため「取得成功＝商品抽出成功」ではない。completeには昇格させない。 |

## 検証
- 10月1日保存HTMLを同じ入口URLで再抽出: 旧0 → 修正後50商品（ニット24、カーディガン26、色違い重複除外後）。
- 10月2日04時台JSTの現在ページ: 1ページ目のみでは49商品、修正済み巡回ではニット2ページ＋カーディガン1ページから69商品、取得エラー0、認識した次ページの残り0。
- 69件は現在の対象カテゴリの観測候補。全商品・全販売月の収集完了や新発売件数ではない。NEW／PREORDERの全範囲監査は未実施。
- Photo Captureの収集・復旧・累積保持・snapshot binding・retrospective関連テスト54件成功。回帰テスト4件追加。
- 実際の累積53件に現在の観測結果を重ねるローカル検証でも既存53件を全保持し、予約開始／お届け予定／通常販売開始／sales_start_dateと関連ラベルの値が保持されることを確認。
- 保存済みの商品正本・予約記録・V04 coverage数値は書き換えていない。初販日推測・予約開始日推測・お届け予定の通常販売開始への昇格なし。PUBLISH_HOLD／human reviewを維持。

## 反映
収集処理の修正はPhoto Capture側のPR。V04にはこの診断を記録する。PR統合前の公式スケジュールは旧処理のままであり、ローカル再取得69件を公開済み件数として扱わない。統合後は通常の巡回・累積保存・coverage出力で反映を確認する。

