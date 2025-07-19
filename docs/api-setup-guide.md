# OpenAI APIキー設定ガイド

このガイドでは、A4図面解析システムでOpenAI APIを使用するための設定方法を説明します。

## 必要な手順

### 1. OpenAI APIキーの取得

1. [OpenAI Platform](https://platform.openai.com/)にアクセス
2. アカウントを作成またはログイン
3. **API Keys**セクションに移動
4. **Create new secret key**をクリック
5. 生成されたAPIキーをコピー（一度しか表示されません）

### 2. 設定ファイルの作成

システムは `config.yaml` ファイルから設定を読み込みます：

```bash
# config.yamlにAPIキーを設定
cp config.yaml.example config.yaml
```

### 3. APIキーの設定

`config.yaml` を編集してAPIキーを設定：

```yaml
openai:
  api_key: "your-actual-api-key-here"  # 取得したAPIキーを入力
  model: "gpt-4-vision-preview"
  max_tokens: 2000
  temperature: 0.1
```

**⚠️ 重要**: 
- 実際のAPIキーに置き換えてください
- APIキーは秘密情報です。絶対に共有しないでください

### 4. 環境変数での設定（推奨）

より安全な方法として、環境変数での設定も可能です：

#### Windows（PowerShell）
```powershell
$env:OPENAI_API_KEY = "your-actual-api-key-here"
```

#### Windows（コマンドプロンプト）
```cmd
set OPENAI_API_KEY=your-actual-api-key-here
```

#### Linux/Mac
```bash
export OPENAI_API_KEY="your-actual-api-key-here"
```

環境変数を使用する場合、`config.yaml`の設定：
```yaml
openai:
  api_key: ${OPENAI_API_KEY}  # 環境変数から取得
  model: "gpt-4-vision-preview"
  max_tokens: 2000
  temperature: 0.1
```

### 5. 設定確認

設定が正しく行われているか確認：

```bash
py main.py status
```

成功すると以下のような出力が表示されます：
```
✅ OpenAI API接続: 正常
✅ 設定ファイル: 読み込み完了
✅ データベース: 接続成功
```

## トラブルシューティング

### よくあるエラー

#### "Invalid API key"
- APIキーが正しく設定されているか確認
- APIキーにタイポがないか確認
- APIキーが有効期限内か確認

#### "Rate limit exceeded"
- APIの使用制限に達している
- しばらく待ってから再実行
- プランのアップグレードを検討

#### "Model not found"
- 指定したモデルが利用可能か確認
- アカウントでGPT-4 Visionが使用可能か確認

### 設定ファイル関連

#### config.yamlが見つからない
```bash
# テンプレートファイルが存在するか確認
ls config.yaml*

# 存在しない場合、新規作成
cp config.yaml.example config.yaml
```

## セキュリティのベストプラクティス

1. **APIキーの管理**
   - APIキーをGitにコミットしない
   - `.gitignore`に`config.yaml`を追加済み
   - 定期的にAPIキーをローテーション

2. **アクセス制御**
   - 必要最小限の権限のみ付与
   - 使用量の監視を設定

3. **バックアップ**
   - 設定ファイルの安全なバックアップ
   - 災害復旧計画の策定

## 料金について

- GPT-4 Visionは使用量に応じて課金されます
- 詳細は[OpenAI Pricing](https://openai.com/pricing)を確認
- システムの`batch_size`設定で使用量を調整可能

## サポート

設定で問題が発生した場合：
1. このガイドのトラブルシューティングを確認
2. `logs/main.log`でエラー詳細を確認
3. OpenAI Platform のステータスページを確認