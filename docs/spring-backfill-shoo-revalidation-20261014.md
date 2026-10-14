# SHOO・LA・RUE 春物遡及の再検証候補

公開前のローカル候補。元候補 `4b7bd7bb7129c2d76d0346bbefb3a30683466d78` を、正本main `b5539e33e72a380fae836adeed7c853fd1cb6b5c` 上へ復元した。最新mainの週次MD変更3ファイルは保持している。push・merge・Sites公開は行わない。

Chat側から届いた2026-10-14 22:09–22:10 UTCの公式再検証結果を、保存済み7商品ページ・12商品月の根拠と照合した。今回の作業者が新たにページを取得したとは記録せず、未提供のレスポンス本文やハッシュも作らない。根拠は個別の婦人ニット商品ページと対象月の日付根拠の両方。発売日・売上・網羅性の証明とは区別する。

| 対象月 | 商品ID末尾 | 日付根拠 | 商品月観測 |
| --- | --- | --- | ---: |
| 2026-01 | 0016・0022 | 商品本文LIVE紹介1/8・1/29 | 2 |
| 2026-02 | 0022・0241 | 088966公開2/13、088953公開2/9 | 2 |
| 2026-03 | 0022・0184・0121・0241 | 089849公開3/20 | 4 |
| 2026-04 | 0102 | 商品本文LIVE紹介4/9 | 1 |
| 2026-05 | 0102 | 092005公開5/25、サマーニット欄の直接リンク | 1 |
| 2026-06 | 0356・0102 | 092355公開6/5 | 2 |

共通ID接頭辞は `BRC6226S`。色違いは同一商品ID・月で1件にする。色query付き取得に失敗した一部リンクは、同一IDのquery無し公式個別ページ本文で確認されている。

履歴保持付きの既存validatorで実際に再集計した結果は、適合セル54→60/240、商品月観測63→75、PARTIAL144→138、PENDING42のまま。7商品で12商品月観測、正規台帳は2件のままであり、同一の件数ではない。全体は `INCOMPLETE`、`PUBLISH_HOLD`、Human Review Requiredを維持する。

旧根拠298行と旧監査298行は、順番・本文・旧理由を保持した。088953の2/13→2/9、089849の3/19→3/20は訂正追記として再確認し、旧日付を書き換えない。未確認の0047・0052・0056と分類曖昧なC62-35301は加算しない。その他の未確認品は別途調査する。

再検証表は `data/brand-md-monitoring/2026-10-14-shoo-spring-month-revalidation.json`。元の10/12報告へ再検証表への参照のみを追記した。coverage/inventoryの元候補内容、既存validator、正規台帳、承認ブランド40件、その他の商談・UIは変更していない。

検査コマンド：

```sh
python scripts/validate_spring_backfill_coverage.py --previous-ref b5539e33e72a380fae836adeed7c853fd1cb6b5c
python -m unittest discover -s tests -p 'test_spring*.py' -v
python -m unittest discover -s tests -p 'test_onward_spring*.py' -v
python -m unittest discover -s tests -p 'test_shoo_spring*.py' -v
```
