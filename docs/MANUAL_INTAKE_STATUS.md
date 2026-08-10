# Manual Intake Status

更新: 2026-08-10

| Batch | 状態 | 件数 | 次工程 |
|---|---|---:|---|
| WEIJIE + 东莞合升 Batch 1 | READY_FOR_HUMAN_REVIEW | 10 | V04 Human Review JSON取込 → 承認 |
| 威海雅信 + 威海诚韵 Batch 2 | READY_FOR_HUMAN_REVIEW | 2 | V04 Human Review JSON取込 → 会社承認（調査記録も同時作成） |
| MZ100 69586・69587・52482 Batch 3 | READY_FOR_HUMAN_REVIEW_WITH_LIMITS | 3 | V04 Human Review JSON取込 → 一次規格不足・variant・102%矛盾を確認。正式昇格は保留可能 |
| MZ100 / 月兔毛 Research | NEEDS_MORE_EVIDENCE | 5調査記録 | MZ100をRank Bで保持。月兔毛は非一意市場名としてSKU単位の一次資料を取得 |
| 东莞合升 30S/4 61元 | HOLD_INCOMPLETE_EVIDENCE | 1 | 反射で隠れた混率・商品名を再確認 |
| WEIJIE 雀羽绒 / Ologeal 2.0 | HOLD_INCOMPLETE_EVIDENCE | 1 | 番手・混率の現物根拠を確認 |

`READY_FOR_HUMAN_REVIEW` はマスター確定済みを意味しない。V04のブラウザ内正本へ入るのはHuman Review承認後のみ。

MZ100 Batch 3は全件 `PENDING`、全体確認状態は `candidate`。69586・69587の混率も `candidate`、52482の混率は合計102%を原文保持した `conflicting` であり、100%へ補正しない。`月兔毛` 自体は同名異仕様のため汎用糸候補へしない。

威海Batch 2は2社を別会社として保持し、雅信↔诚韵の関係は `operationally_related`、資本関係は `unconfirmed` とする。丁晓威は雅信所属として保持し、诚韵については関連連絡先に留める。
