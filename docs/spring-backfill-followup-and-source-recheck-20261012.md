# 完了判定の追加修正と優先3ブランドの再確認

## PR #267 後続レビュー

承認名簿とcoverageの両方を変更すると承認外ブランドが通る問題、追記済み証拠を後から削除できる問題を修正した。

- 名簿の出典blobと全40レコード（公式URLを含む）の内容ハッシュをコードの固定値に照合する。元の名簿とcoverageを同時に変更しても拒否する。
- 最初の277証拠の保全台帳は固定ハッシュで保護する。現在の全証拠と台帳を重複回数まで完全一致で照合し、追加証拠の未登録を拒否する。
- pull_requestではGitHubのbase SHA、mainへのpushではbefore SHAを取得し、直前のcoverageに含まれる全証拠の保持を検証する。後から証拠と台帳を同時に削除しても拒否する。
- ローカルCLIは `--previous-ref <40桁コミットSHA>` で同じ履歴検証を行う。指定なし・定期実行はスナップショット照合で、出力に `SNAPSHOT_ONLY` と明示する。履歴を比較した実行は `PREVIOUS_COMMIT_CHECKED`。

レビュー：PR #267の `discussion_r4245190914`、`discussion_r4245190915`。

## 一次情報の再確認

実確認記録：2026-10-12T06:26:57Z。研究完了の追加は0。

| ブランド・月 | 個別商品確認 | 月への帰属と問題 | 判定 |
| --- | --- | --- | --- |
| AMERICAN HOLIC・5月 | 現行公式個別ページ2件を取得。メーカー品番0H002191600、0H002214600、婦人ニットを確認 | 現行特集・商品ページは10月の販売情報を含む。5月に同じ品番が掲載された証拠は未確認 | PARTIAL、確認済み商品0 |
| B.C STOCK・3月 | 記事のリンク先26080700614010は2回の取得で404 | 現在の3月3日記事は配色ニットカーディガンを掲載。元記録の襟付きスキッパーニットと一致しない。検索索引の公式ページキャッシュでライブ確認を代替しない | PARTIAL、確認済み商品0 |
| SENSE OF PLACE・4月 | 既存SENSE OF PLACEスナップの本文を再取得できず | KBFの証拠除外を維持。取得失敗から商品なし・サイト全体オフラインとは判定しない | PARTIAL、確認済み商品0 |

AMERICAN HOLICの個別URL：

- https://stripe-club.com/brand/american-holic/item/100HS26G0003
- https://stripe-club.com/brand/american-holic/item/100HA26G0083

B.C STOCKの記事・個別URL：

- https://baycrews.jp/blog/detail/100006047
- https://baycrews.jp/item/detail/bcstock/cutsew/26080700614010

対象データに元の277証拠を残し、再確認の4観測を追記して281行とした。元観測原文と旧監査理由を保存し、新しい確認結果で監査判定・未解決理由・実確認日時を更新した。B.C STOCKについて現在の記事にニットがないとは記載せず、元商品名の不一致と個別ページ未取得を明示する。

## 進捗・検証

月別完了数は1月5、2月7、3月7、4月7、5月7、6月7。240ブランド月中40完了、200未完了（PARTIAL158、PENDING42）。全6月完了4ブランド、確認済み商品月観測43、正規台帳2件。

ローカル65チェックPASS：coverage 30（実git履歴を使うCLI試験を含む）、方針11、商品なし13、遡及台帳8、完了方針3。GitHub Actionsで変更前コミットとの比較と関連テストを実行する。

`PUBLISH_HOLD`、`human_review_required=true`、販売数量推定禁止を維持する。詳細な再確認記録は `data/brand-md-monitoring/2026-10-12-spring-priority-source-recheck.json`。
