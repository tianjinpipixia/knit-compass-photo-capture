# Knit Compass KPI計測基準

更新日: 2026-08-03  
版: 1.1.0

## 目的

売上発生前でも、Knit Compassが生み出す業務価値を時間・品質・再利用で説明できるようにします。月次集計は `data/kpi_log_template.csv` の構造化項目だけで再計算できる状態を保ちます。

## 当面の必須KPI

| KPI | 計算方法 | 初期目標 |
|---|---|---|
| 1件あたり削減時間 | `baseline_minutes - actual_minutes` | 10件で基準値を作る |
| 月間登録件数 | 月内に `event_type=CONFIRM` かつ `registration_status=CONFIRMED` となった一意の `item_id` 数 | 前月比較 |
| Human Review修正率 | `ai_correction_count > 0` のレビュー件数 ÷ Human Review完了件数 | 継続低下 |
| 再利用回数 | `event_type=REUSE` の `reuse_count` 合計 | 継続増加 |
| 利用人数 | 月内の一意の `operator` 数。補助値として `active_user_count` も記録 | 実人数を記録 |
| 根拠なし確定件数 | `registration_status=CONFIRMED` かつ `evidence_status=MISSING` の件数 | 0件 |

## テンプレート必須項目

- `measurement_date`: 計測日
- `operator`: 操作者
- `workflow`: 調査、登録、レビュー、再利用など
- `event_type`: `CREATE` / `UPDATE` / `REVIEW` / `CONFIRM` / `REUSE`
- `item_type`: product、yarn、organization、photo、research等
- `item_id`: 共通ID
- `registration_status`: `DRAFT` / `REVIEW` / `CONFIRMED` / `REJECTED`
- `confirmed_at`: 確定日時。未確定は空欄
- `evidence_id`: 根拠ID。複数は `|` 区切り
- `evidence_status`: `PRESENT` / `MISSING` / `NOT_REQUIRED`
- `human_review_status`: `NOT_STARTED` / `IN_REVIEW` / `APPROVED` / `REJECTED`

自由記述の `notes` だけで確定・根拠の有無を判定してはいけません。

## 計測方法

1. 同じ種類の代表業務を最低10件選ぶ
2. 従来方法の所要時間を `baseline_minutes` に記録
3. Knit Compass利用時の時間を `actual_minutes` に記録
4. `minutes_saved = baseline_minutes - actual_minutes` で算出
5. AI回答を人が修正した項目数を `ai_correction_count` に記録
6. 確定時は `event_type=CONFIRM`、`registration_status=CONFIRMED`、`confirmed_at` を必ず記録
7. 根拠が必要な確定では `evidence_id` と `evidence_status=PRESENT` を記録
8. 月末に合計時間、中央値、修正率、再利用回数、根拠なし確定件数を集計

入力テンプレート: `data/kpi_log_template.csv`

## 資産評価で使用できる計算例

- 月間削減時間 = `minutes_saved` 合計 ÷ 60
- 年間削減時間 = 月間削減時間 × 12
- 年間工数価値 = 年間削減時間 × 社内時間単価

時間単価や売上換算は、社内承認済みの値だけを使用します。推定値を確定実績として表示しません。

## 月次レビュー

月末に次を記録します。

- 今月の削減時間
- 新規登録／確定件数
- 利用人数
- 調査修正率
- 根拠なし確定件数
- 最も再利用された素材・糸・調査
- 翌月に改善する一項目
