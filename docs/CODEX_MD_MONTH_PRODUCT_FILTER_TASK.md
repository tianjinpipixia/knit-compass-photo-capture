# Codex task — proposal-workspace 月別商品フィルターと選択状態リセット

Repository: `tianjinpipixia/knit-compass-photo-capture`  
Issue: `#87`  
Reference branch: `fix/md-month-product-filter-20260820`

## Goal

正規公開先 `knit-compass-v04.s-zhujing.chatgpt.site/proposal-workspace#product` の **02 個別MD情報 → 月選択 → 3. 商品情報を選ぶ** を、ブランド・年度・月の厳密なスコープで動かす。

月を変えた時に前月の商品や内部の選択状態が残り、03 素材候補、04 ゲージ・編み地候補、05 デザイン提案へ古い商品条件が流れる状態を禁止する。

## Source boundary — 最重要

- **ChatGPT Sitesで現在公開中の最新ソースを起点に差分修正すること。**
- 古いDrive/GitHubスナップショットでSites全体を上書きしない。
- このGitHubブランチはMD契約・回帰fixture・validatorの参照元であり、公開SitesソースそのものがGitHubに存在するとは仮定しない。
- Sites-onlyの新しいUI、ヘッダー、辞典、糸検索、Human Review導線を消さない。

## Reference contract

実装仕様の正本:

- `config/proposal-workspace-month-scope-contract.json`
- `data/brand-md-monitoring/2026-08-20-global-work-month-scope-fixture.json`
- `scripts/validate_proposal_workspace_month_scope.py`

## Required implementation

### 1. 商品一覧を選択月で再計算

`brand_id + fiscal_year + selected_month` を商品一覧の必須スコープにする。

- 月変更後、前月の商品を通常一覧へ残さない。
- ブランド変更・年度変更でも同じ。
- 対象0件なら過去商品で埋めず空状態を出す。
- `MONTH_UNRESOLVED` は選択月へ推測挿入しない。

### 2. 月・年度・ブランド変更時に依存選択を完全リセット

少なくとも以下をクリアする。

- `selectedProductId` / `selectedProduct`
- selected material candidate
- selected knit/gauge candidate
- selected design proposal
- 選択商品から生成された候補collection
- URL/query/hash/session/local UI stateに残る、現在スコープ外の商品ID

商品レコード自体は削除しない。

**新月の先頭商品を自動選択しない。** ユーザーが明示選択するまで下流は未選択。

### 3. 月所属判定

- 予約が最初の商業投入イベントなら `preorder_start_date` の月を `md_primary_month` とし、PREORDER表示。
- 先行予約がない場合は confirmed `sales_start_date` の月。
- `first_seen_date` は観測日であり、確認済み発売・予約月の代用にしない。
- `delivery_expected_month` は補助情報のみ。納品月にNEWとして二重カウントしない。
- 月が確定できない場合は `MONTH_UNRESOLVED`。

### 4. CARRYOVER / SPECIAL / COMPETITORを本体新規と分離

- CARRYOVERは明示根拠がある場合のみ別枠。
- STAFF LAB等は `SPECIAL_TEST` 別枠。通常本体MDの型数・主要素材集計から除外。
- GU等の競合は `COMPETITOR_REFERENCE`。GLOBAL WORKの商品件数へ混ぜない。

## GLOBAL WORK regression fixture

2026年8月のMAINLINE対象:

- `826491` — 8/7予約開始、8/25正午終了、9月上旬納品。9月NEWへ二重計上しない。
- `1051672` — 8/12、PET71/AC29、約280g。
- `1051195` — 8/13、C72/PET28、約400g。
- `670330` — 8/18予約開始、8/24正午終了、9月上旬納品、AC48/C37/PET15。WJQD系は現時点推定で確定扱い禁止。

SPECIAL:

- `1044391` STAFF LAB — 保持するが本体MD集計から除外。

COMPETITOR:

- GU `360801` — WJQD確認済み。GLOBAL WORKの商品一覧には混ぜない。

## Required QA

1. GLOBAL WORK / 2026年度 / 8月 → 上記8月MAINLINEだけが通常商品一覧に出る。
2. 8月商品を選択後に9月へ変更 → 8月商品が消え、`selectedProduct`も解除。
3. そのまま03素材候補へ進んでも8月商品の条件が残らない。
4. 9月→8月へ戻す → 商品一覧は戻るが以前の商品を自動再選択しない。
5. GLOBAL WORK→GU → GLOBAL WORKの商品と下流選択が残らない。
6. 0件月 → 過去商品を代替表示しない。
7. 826491/670330を8月NEWと9月NEWの両方へ計上しない。
8. 1044391はSPECIALで、本体型数・主要素材集計へ入らない。
9. GU 360801は競合参照のみ。
10. Human Review / PENDING / NOT_PROMOTED / PUBLISH_HOLD / customer-sharingを変更しない。

## Repository validation

実装作業の前後で最低限:

```bash
python3 scripts/validate_proposal_workspace_month_scope.py
python3 scripts/validate_brand_md_analysis_framework.py
python3 scripts/validate_v04_reflection_guard.py
```

## Completion report

完了時は以下を報告する。

- Sites側の変更箇所
- GitHub側の対応ファイル
- 月所属判定関数
- resetしたstate一覧
- GLOBAL WORK 8月→9月→8月のQA結果
- 他ブランドへの回帰結果
- 公開URLでのPC確認結果

**公開Sitesで月変更後に古い商品と下流選択が残らないことを確認するまで完了扱いにしない。**
