# Brand64 Gemini稼働修復

- MIX.Tokyoの春先遡及2商品（0176170252、0176170124）のsource_kindを既存の許容値OFFICIAL_EC_PRODUCT_PAGEに統一。価格・素材・観測日・審査保留は変更しない。
- Gemini 2.5では検索・URL Contextと強制JSON Schemaを同時指定しない。JSON形式をプロンプトで指定し、戻り値の構造と取得根拠を検証する。
- Googleの仕様: https://ai.google.dev/gemini-api/docs/structured-output#structured_outputs_with_tools
- 不明な状態、ブランドの重複・取り違え、取得根拠のないOK、途中終了は完了にしない。
- 再試行を別ファイルへ保存し、失敗した試行で前回成功の比較基準を上書きしない。
- 現在のページを過去の日付へ付け替える実行を禁止。9月1日以降の未観測日は根拠が揃うまで保留する。
- スキャナー修正をmainへ反映した際も試運転する。通常の日次時刻は05:30 JSTを維持。
- 実行先はこのGitHubリポジトリのActions。V04のSitesに登録したキーは、このリポジトリのGEMINI_API_KEY Secretには自動共有されない。
- APIキーはチャット・ソース・ログへ書かず、GitHubのActions Secretへ登録する。
- Phase Aの成功だけでは正式マスター・V04 latest・顧客公開へ昇格しない。ChatGPTによる公式個別商品ページ確認と既存のHuman Reviewを維持する。
