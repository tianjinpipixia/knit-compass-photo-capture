# Manual Intake Data Policy

Manual Intakeは、会話や写真から直接コード内マスターへ確定登録するための仕組みではありません。

1. 写真で確認できる事実を `PENDING` 候補へ変換する。
2. 根拠写真ファイル名とLibrary file_idをnotes/photoRefsへ保持する。
3. 不完全・反射・矛盾がある項目はHOLDにする。
4. Human Reviewで承認された候補だけを正式マスターへupsertする。
5. 市場名（例: 仿亚麻）から天然繊維含有を推定しない。
6. Supplier表示・資料確認・試験確認を同一の根拠レベルとして扱わない。
