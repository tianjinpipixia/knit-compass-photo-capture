# Brand64の商品正本と入力・表示の契約

商品正本は、このリポジトリの `brand64/flash-feed` ブランチにある `data/brand-md-monitoring/direct-scans/cumulative-products/manifest.json` と、manifestが列挙するチェックサム付き `BR-xxxxx.json` だけです。mainは収集・統合プログラム、設定、履歴入力の正本です。商品件数はmanifestとブランド別の実商品行から算出します。全商品を重複保持する `catalogue.json` は廃止し、V04を含む表示側はmanifestのブランド別シャードから派生させます。

公式サイト巡回 → 検証済み累積から再構成した作業state → 公式の過去資料/importsとの統合 → cumulative-products → V04の読み取り専用adapter、という順序です。`observed-products`、feed、flash、latestは日次表示・処理進捗です。deltaは変更イベントであり独立商品台帳ではありません。

known-productsは再開用チェックポイントです。古いチェックポイントで正本の商品・過去月根拠を消さず、正本の不完全・破損を検出したら公開を中止します。正本の親コミットを読取前に固定し、非force pushで同時更新の上書きを防ぎます。ブランド別の古いファイルや未知の保存ファイルは削除しません。

retrospective/importsは一回限りの移行入力です。元リポジトリ・パス・コミットまたはblob hashを保持し、再実行しても同じ商品を増やしません。未確認・対象外・不正形式の行はreview-queueへ残して件数には含めません。初回観測日は発売日ではなく、全観測行はHOLD/人の確認を要します。

Gemini MDは補助分析入力であり、商品正本へ直接書き込む経路ではありません。旧Gemini primary pointer、baseline、過去ブランチはdeprecatedの監査入力です。凍結対象コミットはconfig/brand64-data-lineage.jsonに記録しています。過去ブランチの内容を書き換えません。

V04は商品factsをこの正本から取得し、表示上のID・非公開の糸との関連はV04側メタデータとして保持します。既存のオーナー商品DB・ブランド調査DBは別の書込経路が見つかっており、認証付き実データ監査と業務フロー調整が未完了です。全システムの一本化完了とは扱いません。

Sandbox、ローカル作業コピー、Sitesのビルド成果物は正本ではありません。SitesはGitHub V04のソースをビルドした表示アプリです。実運用の認証付き応答は別途検証が必要です。
