# Mac開発環境方針

Knit Compassの設計・実装・検証・公開作業は、Apple Silicon搭載Macを主環境とします。

## 運用境界

- Mac: 設計、実装、データ整備、ローカル確認、Git/GitHub、公開前検証の正規環境
- Windows: 会社内でのブラウザ利用と補助起動のみ
- GitHub Actions: Linux検証に加え、`macos-14`のM1/arm64検証を必須化
- Rosetta / Intel版Node.js: 開発環境として使用しない

Windows固有の開発手順やWindows用ビルド環境は追加しません。既存の `start.bat` は会社PCでの補助起動互換性のためだけに維持します。

## 初回セットアップ

Apple Silicon版のNode.js LTSをインストールしたうえで、リポジトリ直下から次を実行します。

```sh
scripts/setup_macos.sh
```

このスクリプトは `.venv` を作り、検証と糸カタログ生成に必要なPython依存を導入します。Node.jsがIntel版または未導入の場合は停止します。

## 起動

Finderから `start.command` を開くか、ターミナルで次を実行します。

```sh
./start.sh
```

## 検証

```sh
scripts/validate_macos.sh
```

全Python検証とJavaScript構文検証をApple Silicon環境で実行します。Node.jsが見つからない場合に検証を省略して成功扱いにはしません。
