# Owner Yarn Master 2,000件実装記録

更新: 2026-08-12

## 目的

糸を1件ずつ深掘りしてから検索対象へ加える方式ではなく、まず検索できる母数を2,000件まで増やし、実際に必要になった候補だけを元ページ・Supplier資料・現物で深掘りする。

## 実装範囲

### 1. MZ100軽量カタログ索引

- 生成物: `data/yarn-catalog/mz100-catalog-2000.json`
- 生成スクリプト: `scripts/build_mz100_catalog.py`
- 目標件数: 2,000件
- 取得対象: MZ100の糸一覧ページから確認できる掲載情報
- 保存項目:
  - MZ100掲載ID
  - 元ページURL
  - 掲載糸名
  - 掲載番手
  - 掲載混率
  - 掲載供給元

各行は次の状態を固定する。

- `catalog_status: CATALOG_INDEXED`
- `verification_status: LISTING_PAGE_ONLY`
- `master_status: NOT_PROMOTED`

したがって、2,000件は検索可能な索引であり、2,000件すべてが確認済み正式糸マスターという意味ではない。

### 2. Owner Yarn Master画面

入口: `/owner-yarns/`

- 2,000件を糸名・供給元・番手・混率・元IDから検索
- 情報充足状態で絞り込み
- 元MZ100ページを直接確認
- 端末内の正式糸マスター件数とカタログ件数を分離表示
- CATALOG INDEXと正式マスターを同じ状態として扱わない

### 3. 未反映17件の一括取込

以下5バッチを同じ画面からV04 Human Review受信箱へ重複なく取り込む。

| Batch | 件数 | 内容 |
|---|---:|---|
| WEIJIE + 东莞合升 | 10 | 現物BOOKで確認した糸候補 |
| 威海雅信 + 威海诚韵 | 2 | 会社候補 |
| MZ100 69586・69587・52482 | 3 | Evidence-backed調査候補 |
| TWIN WIN TEXTILE | 1 | 会社・工場候補 |
| ROPÉ PICNIC GDM56050 | 1 | 公式URL指定の商品候補 |
| **合計** | **17** | すべて `PENDING` |

取込先は `localStorage kc_v04_handoff_queue_v1`。`dedupe_key` を使って同じ候補の重複取込を防ぐ。

### 4. 会社スプレッドシート受信箱

Owner Yarn Masterから次を出力できる。

- 会社スプレッドシート受信箱用CSV
- 監査用JSON

CSVは既存の正式マスターを上書きせず、各行を `PENDING_HUMAN_REVIEW` として追記する。会社・商品・糸マスターへの正式昇格はHuman Review後に限定する。

会社所有Google Apps Scriptの正式WebアプリURLと認証方式が確定するまでは、任意URLへブラウザから自動送信しない。現在の確定接続はCSV／JSONによる受信箱追記である。

## 個別候補の安全境界

### TWIN WIN TEXTILE

ユーザー提供PDFに記載された会社名、所在地、面積、生産品、月産数量、予定人員、設備を歴史資料値として保存する。現在の法人登記、稼働状況、現行能力、認証は未確認のため、会社・工場マスターへ自動昇格しない。

### ROPÉ PICNIC GDM56050

ユーザー指定の公式URLと品番だけを確実な候補値として保存する。公式ページを再取得できるまで、商品名、価格、混率、機能、ゲージ、糸構造、供給元は空欄を維持する。

## 検証

```bash
python -m pip install -r requirements-catalog.txt
python scripts/build_mz100_catalog.py --target 2000
python scripts/validate_owner_yarn_implementation.py
python scripts/validate_navigation_links.py
```

検証条件:

- カタログが正確に2,000件
- ID・元URLが2,000件すべて一意
- 全件が `NOT_PROMOTED`
- 手動取込候補が5バッチ・17件
- 17件すべて `PENDING`
- TWIN WINとGDM56050が推測値で補完されていない
- Owner Yarn Master、Photo Capture、V04、System Statusの相互リンクが解決する
