# WORLD 3ブランドの春物遡及・ローカル候補

正本はPhotoCaptureの `data/brand-md-monitoring/2026-spring-backfill-coverage.json`。比較元mainは `b5539e33e72a380fae836adeed7c853fd1cb6b5c`。対象範囲はV04 `config/brand-research-scope.json` の承認済み `KC40-20260930`・40ブランドであり、春物の固定ロスターとID・名称・tierが一致する。V04やSitesへは変更を加えていない。

先行SHOO候補 `20ae3f49e13feacaea350b381892d9ccda26834d` に、Chat側が22:09–22:14 UTCに確認したOPAQUE.CLIP・indexの固定本文と公式個別商品の対応を追記した。こちらでもindex3品番とOPAQUEの3月2品番を公式ページで補足確認し、セットの部位別混率を転記した。全ページを新規取得したとは記録せず、未提供のレスポンス本文・ハッシュも作成していない。

| ブランド | 今回の追加月 | 新しい適合セル | 追加商品月観測 | 対象品番数 |
| --- | --- | ---: | ---: | ---: |
| SHOO・LA・RUE（先行分） | 1〜6月 | 6 | 12 | 7 |
| OPAQUE.CLIP | 1・2・3・5・6月 | 5 | 6 | 5 |
| index | 2・3・5月 | 3 | 3 | 3 |
| 合計 | | 14 | 21 | 15 |

OPAQUEの3月は2品番、637-15165は5月と6月で各1観測。色違いは同じ月の別商品として加算しない。indexの既存6月1観測は元のまま保持し、今回の追加3観測には含めない。

| 月 | OPAQUE.CLIP | index | 採用した固定記事 |
| --- | --- | --- | --- |
| 1月 | N02-14001 | 保留 | 087888・1/9「あったかニット」 |
| 2月 | 637-15069 | C58-15026 | 088953・2/9「季節のニット」、088966・公開2/13（ランキング2/12） |
| 3月 | 637-15136・637-15003 | C58-15041 | 089849・3/20固定本文 |
| 4月 | 保留 | 保留 | 新たな適合根拠なし |
| 5月 | 637-15165 | C58-15042 | 092005・5/25固定本文（indexは袖デザイン欄） |
| 6月 | 637-15165 | 既存観測を保持 | 092355・6/5固定本文 |

OPAQUEの旧088559・089169は動的更新された記事として今回の月根拠に使わない。indexの090330セットアップと、5/20の動的な「その他おすすめ」も不採用。旧証拠・旧監査理由は削除しない。089849の旧3/19は残し、対応する新しい3/20固定本文を別行で追記した。

637-15136は[公式ツインセット商品ページ](https://store.world.co.jp/brand/opaque-clip/item/BR63726S0200)に基づく1品番。混率はプルオーバーがポリエステル38・レーヨン25・アクリル19・綿18、インナーのジャージ部分が綿100、布帛部分がポリエステル65・綿35。部位の重量比は不明で、セット全体の合計混率を計算せず、ニットとタンクを別2品番にしない。

既存validatorによる実再集計は **54→68/240適合セル、63→84商品月観測、PARTIAL144→130、PENDING42のまま**。残る非適合172セルはPARTIAL130＋PENDING42。正規台帳2件、`INCOMPLETE`、`PUBLISH_HOLD`、Human Review Requiredは維持する。掲載月観測を発売日・売上・網羅性の証明に置き換えない。

先行根拠314行と監査314行の順序付きprefixを保持し、17行（固定記事8＋個別商品9）を追加した。保留月と既存index6月はセル全体を保持し、SHOOを含む他38ブランドもそのまま。正規台帳・ロスター・監視ポリシー・既存validator・最新mainの週次MD3ファイルは変更しない。

詳細は `data/brand-md-monitoring/2026-10-14-opaque-index-spring-month-evidence.json`。以下を実行してから候補を保存する。

```sh
python scripts/validate_spring_backfill_coverage.py --previous-ref b5539e33e72a380fae836adeed7c853fd1cb6b5c
python scripts/validate_spring_backfill_coverage.py --previous-ref 20ae3f49e13feacaea350b381892d9ccda26834d
python -m unittest discover -s tests -p 'test_spring*.py' -v
python -m unittest discover -s tests -p 'test_onward_spring*.py' -v
python -m unittest discover -s tests -p 'test_shoo_spring*.py' -v
python -m unittest discover -s tests -p 'test_world_fixed_article_spring*.py' -v
```

すべてローカル候補であり、push・PR・merge・Sites公開は行っていない。
