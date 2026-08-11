# Manual Intake Status

更新: 2026-08-12

| Batch | 状態 | 件数 | 次工程 |
|---|---|---:|---|
| WEIJIE + 东莞合升 Batch 1 | READY_FOR_HUMAN_REVIEW | 10 | Owner Yarn MasterからV04受信箱へ取込 → Human Review承認 |
| 威海雅信 + 威海诚韵 Batch 2 | READY_FOR_HUMAN_REVIEW | 2 | Owner Yarn MasterからV04受信箱へ取込 → 会社承認（調査記録も同時作成） |
| MZ100 69586・69587・52482 Batch 3 | READY_FOR_HUMAN_REVIEW_WITH_LIMITS | 3 | 一次規格不足・variant・102%矛盾を確認。正式昇格は保留可能 |
| TWIN WIN TEXTILE Batch 4 | READY_FOR_HUMAN_REVIEW_WITH_LIMITS | 1 | 歴史資料値を保持し、現行法人登記・稼働状況・能力を再確認 |
| ROPÉ PICNIC GDM56050 Batch 5 | READY_FOR_HUMAN_REVIEW_WITH_LIMITS | 1 | 公式ページ再取得後、商品名・価格・混率・機能・糸紐付けを確認 |
| **一括取込対象** | **READY** | **17** | `/owner-yarns/` から重複なくV04受信箱へ取込 |
| MZ100 / 月兔毛 Research | NEEDS_MORE_EVIDENCE | 5調査記録 | MZ100をRank Bで保持。月兔毛は非一意市場名としてSKU単位の一次資料を取得 |
| 东莞合升 30S/4 61元 | HOLD_INCOMPLETE_EVIDENCE | 1 | 反射で隠れた混率・商品名を再確認 |
| WEIJIE 雀羽绒 / Ologeal 2.0 | HOLD_INCOMPLETE_EVIDENCE | 1 | 番手・混率の現物根拠を確認 |

`READY_FOR_HUMAN_REVIEW` はマスター確定済みを意味しない。V04のブラウザ内正本へ入るのはHuman Review承認後のみ。

MZ100 Batch 3は全件 `PENDING`、全体確認状態は `candidate`。69586・69587の混率も `candidate`、52482の混率は合計102%を原文保持した `conflicting` であり、100%へ補正しない。`月兔毛` 自体は同名異仕様のため汎用糸候補へしない。

威海Batch 2は2社を別会社として保持し、雅信↔诚韵の関係は `operationally_related`、資本関係は `unconfirmed` とする。丁晓威は雅信所属として保持し、诚韵については関連連絡先に留める。

TWIN WIN Batch 4の面積、月産、人員、設備等はユーザー提供PDFの歴史資料値であり、現在値として自動更新しない。GDM56050 Batch 5はURLと品番以外を空欄に保ち、公式ページの再取得前に商品仕様を補完しない。

会社スプレッドシートへの出力は受信箱用CSV／監査JSONで行い、処理状態を `PENDING_HUMAN_REVIEW` とする。正式マスターを直接上書きしない。
