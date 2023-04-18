# LunoAutoTrader

LunoAutoTraderは、Luno取引所で暗号通貨ポートフォリオをリバランスするためのPythonスクリプトです。

## 環境とインストール

1. Python 3.7以降がインストールされていることを確認してください。
2. 依存関係をインストールするために、プロジェクトのディレクトリで次のコマンドを実行します。
    pip install -r requirements.txt
3. Luno APIキーを取得し、`keys.json`ファイルに記入してください。
    {
    "api_key_id": "your_api_key_id",
    "api_key_secret": "your_api_key_secret"
    }

## 使い方

1. `main.py`を実行します。
2. スクリプトが自動的にポートフォリオをリバランスし、必要な取引を実行します。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細については、[LICENSE](LICENSE)ファイルを参照してください。
