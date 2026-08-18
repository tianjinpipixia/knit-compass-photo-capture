# 64ブランド 日次観測 → ブランド別MDプラン

更新日: 2026-08-19

## 目的
64ブランドを一度確認して終わりにせず、日次で変化を拾い、週次で意味づけし、月次でブランド別MDプランに変換する。アクティブ監視対象の単一ソースは `config/brand64-active-brands.json` とする。

## Brand64構成更新

### 2026-08-18 PAL10追加
Issue #53 のオーナー決定に従い、旧10ブランドをアクティブ監視から外し、PAL系10ブランドを追加した。旧ブランドの過去観測・商品URL・根拠は削除せず `INACTIVE_LEGACY_REFERENCE` として保持し、BR-IDは再利用しない。

新規PAL系10ブランド:
- BR-00065 GALLARDAGALANTE
- BR-00066 Whim Gazette
- BR-00067 LOUNGEDRESS
- BR-00068 RIVE DROITE
- BR-00069 DOUDOU
- BR-00070 SHENERY
- BR-00071 un dix cors
- BR-00072 La boutique BonBon
- BR-00073 natural couture
- BR-00074 DISCOAT

PAL共通ニット入口:
`https://www.palcloset.jp/display/display/?mode=zSearch&SearchItem.SORT_KEY=POPULARITY_DESC&b=&sex=&c=1104,1105&type=01`

PAL系は毎日、新着・予約・SALE・ランキング入口を軽量確認し、週次では人気順/ランキング変化もMDシグナルとして見る。

### 2026-08-19 ZARA追加
Issue #73 のオーナー決定に従い、TAKEO KIKUCHI（BR-00048）をアクティブ監視から外し、ZARAをBR-00075として追加する。BR-00048は再利用せず、TAKEO KIKUCHIの過去観測は `INACTIVE_LEGACY_REFERENCE` として保持する。

ZARAは国内ブランドと同列の「売れ筋推定」ではなく、グローバルファストファッションの先行MD指標として扱う。日次はTHE NEW / レディースニット / Special Pricesを軽量確認し、週次では新シルエット、表面感、カラー、価格帯、値下げ深度、商品回転を比較する。

- レディースニット: `https://www.zara.com/jp/ja/woman-knitwear-l1152.html`
- Special Prices: `https://www.zara.com/jp/ja/woman-knitwear-special-prices-l1163.html`
- 初回基準: `data/brand-md-monitoring/2026-08-19-zara-initial-baseline.jsonl`

## 運用サイクル

### 毎日 — Light Scan
各ブランドの公式サイト・公式ECを優先して確認する。

確認項目:
- 新着ニット
- 予約ニット
- 値下げ・価格変更
- 新しい素材混率
- 新しい機能訴求
- 新しいシルエット・編地・柄
- カラー変化
- 新規掲載数 / 掲載終了の変化

保存ルール:
- 公式URLを必須とする
- 観測事実とAI解釈を分離する
- 販売数量は根拠がなければ `NOT_AVAILABLE`
- 販売数量を推定しない
- 同一URL・同一品番は重複登録しない
- 初回発見時の商品基準を保持し、後日404/掲載終了/URL変更でも削除しない
- 掲載終了は `SOURCE_OFFLINE` 等で扱い、最終確認情報を残す
- 取引先非公開情報は混ぜない

### 毎週 — Weekly Brand Signal
日次差分をブランド単位で集約する。

出力:
- 今週増えた素材
- 今週増えた機能
- 価格帯の変化
- 予約比率の変化
- シルエット / 編地の変化
- PAL系のランキング/人気順変化
- ZARAの新シルエット / 表面感 / 値下げ深度 / 商品回転
- 注目商品3件まで
- 素材開発への示唆
- 次週確認事項

### 毎月 — Brand MD Plan
各ブランドについて月次観測と日次・週次差分を統合し、MD DRAFTを作る。

出力:
- ブランド名
- 対象月
- 市場ポジション
- 今月の主力ニットテーマ
- 素材構成の変化
- 機能性の変化
- 価格帯
- カラー / シルエット / 編地
- 予約 / 新着 / 値下げの動き
- Knit Compassで提案すべき糸タイプ
- 既存糸候補
- 新規開発候補
- 営業提案テーマ
- 次月の仮説
- 根拠URL一覧

## Gemini向け日次指示

以下を毎日実行する前提の固定指示とする。

> Knit Compassのアクティブ64ブランドについて、`config/brand64-active-brands.json` を正本として公式サイト・公式ECの公開情報だけを確認し、前回観測との差分をブランド別に記録してください。対象はレディースニット中心です。新着、予約、値下げ、商品終了、価格、混率、機能、カラー、シルエット、編地、商品名、品番、公式URLを確認してください。PAL系10ブランドはPAL CLOSET共通ニット入口と各ブランド公式ページの新着・予約・SALE・ランキングを毎日確認し、週次では人気順変化も記録してください。ZARAはTHE NEW / レディースニット / Special Pricesを毎日軽量確認し、週次では新シルエット・表面感・カラー・価格帯・値下げ深度・商品回転を先行MDシグナルとして整理してください。販売数量は一次根拠がある場合だけ保存し、推定しないでください。事実と解釈を分離し、事実には公式URLを付けてください。同一URL・同一品番は重複登録しないでください。初回発見時の基準情報は保持し、後日404や掲載終了になっても削除しないでください。変更がないブランドも観測済みを残してください。旧INACTIVEブランドは日次アクティブ集計に混ぜず、履歴参照としてのみ保持してください。

## 重要
この指示ファイルだけではGeminiを自動実行しない。Gemini API / Gemini側の定期実行環境が接続された場合に、この内容を固定プロンプトとして使う。Knit Compass側のMDデータはHuman Review後にのみ確定する。

GitHub Actionsの `monitor-brand64-daily-freshness.yml` は毎朝6:40（日本時間）に、最新のアクティブ64ブランドが揃っていること、BR-ID/ブランド名の重複がないこと、INACTIVEブランドがアクティブ一覧に戻っていないこと、PAL10ブランドとZARAの公式URLが保持されること、販売数量非推定・公開保留が維持されることを確認する。これは外部サイトを自動調査する処理ではなく、更新漏れや古い提案を「最新」と扱わないための監視である。
