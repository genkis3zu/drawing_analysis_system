# CLAUDE.md

Claude Code (claude.ai/code) 向けの開発ガイドライン。このドキュメントはA4図面解析システムの開発規約、アーキテクチャ、TDDガイドラインを含みます。

## Claude Code Hooks設定

プロジェクトには以下のフックが設定されています：

### 利用可能なフック
- **pre-commit.sh**: コミット前に変更内容を確認し、適切なコミットを促す
- **task-complete.sh**: タスク完了時に未コミットの変更を確認し、GitHubへのプッシュを促す

### フックの動作
これらのフックは開発の節目で自動的に実行され、以下を促します：
1. 変更内容の確認
2. 適切なコミットメッセージの作成
3. GitHubへのプッシュ

これにより、重要な作業が失われることなく、適切にバージョン管理されます。

## プロジェクト概要

A4図面解析システム - OpenAI GPT-4 Visionを使用してA4サイズ（210×297mm）の技術図面からデータを抽出し、Excelに出力するAIシステム。日本語技術図面に特化。

### 主要な目的
- 手動データ入力の非効率性を解決（15-20分の作業を数十秒に短縮）
- 図面解析の専門知識依存性を削減
- データの一貫性と品質を向上（目標精度80%以上）
- 図面のデジタル変換を促進

## 開発規約とコーディングスタンダード


### 言語・フレームワーク別ガイドライン例

```markdown
## JavaScript/TypeScript
- ESModules使用（CommonJS禁止）
- 分割代入でimport
- Prettier/ESLint設定の遵守
- 環境変数は process.env 経由でアクセス

## Python
- Type hintsの必須使用
- Black/isortによるフォーマット
- pytest + coverage の使用
- settings.py での設定管理

## Java/Spring
- Constructor injection使用
- @Value アノテーションで外部化
- JUnit 5 + Mockito使用
- application.yml での設定管理


### Python開発規約
```python
# ファイル構成
- 1ファイル1クラスを原則とする
- ファイル名はスネークケース: image_processor.py
- クラス名はパスカルケース: A4ImageProcessor
- 関数名・変数名はスネークケース: analyze_drawing()

# インポート順序
1. 標準ライブラリ
2. サードパーティライブラリ  
3. ローカルモジュール
（各グループ内はアルファベット順）

# ドキュメント文字列
- すべてのクラス・関数にdocstringを記述
- Google Styleまたはnumpy Styleを使用
- 日本語での記述を推奨
```

### 型ヒントの使用
```python
from typing import Dict, List, Optional, Tuple

def analyze_drawing(
    self, 
    image_path: str, 
    request: Optional[DrawingAnalysisRequest] = None
) -> AnalysisResult:
    """図面を解析してデータを抽出する
    
    Args:
        image_path: 解析する図面のパス
        request: 解析リクエストの詳細設定
        
    Returns:
        AnalysisResult: 抽出されたデータと解析メトリクス
    """
```

### エラーハンドリング
```python
# 具体的な例外を使用
try:
    result = self._process_image(image_path)
except FileNotFoundError:
    logger.error(f"図面ファイルが見つかりません: {image_path}")
    raise
except ImageProcessingError as e:
    logger.warning(f"画像処理エラー、フォールバック処理を実行: {e}")
    result = self._fallback_process(image_path)
```

## TDD（テスト駆動開発）ガイドライン

### TDDサイクル
## TDD原則の適用
- **Red**: 失敗するテストを先に書く
- **Green**: テストが通る最小限のコードを書く  
- **Refactor**: コードを改善し、ハードコードを排除

## 禁止事項
- テスト値の直接的なハードコード
- magic numberの使用
- 環境固有の値の埋め込み
- 一時的な回避策としてのハードコード

### テスト構造
```
tests/
├── unit/                    # ユニットテスト
│   ├── test_image_processor.py
│   ├── test_agent.py
│   └── test_excel_manager.py
├── integration/             # 統合テスト
│   ├── test_drawing_analysis_flow.py
│   └── test_template_matching.py
├── fixtures/               # テストデータ
│   ├── sample_drawings/
│   └── mock_responses/
└── conftest.py            # pytest設定
```

### テストの書き方
```python
# tests/unit/test_image_processor.py
import pytest
from src.utils.image_processor import A4ImageProcessor

class TestA4ImageProcessor:
    """A4ImageProcessorのユニットテスト"""
    
    @pytest.fixture
    def processor(self):
        """テスト用のプロセッサインスタンス"""
        return A4ImageProcessor()
    
    def test_a4サイズ検出_正常なA4縦向き(self, processor):
        """正常なA4縦向き図面のサイズ検出をテスト"""
        # Given
        test_image = "tests/fixtures/sample_a4_portrait.png"
        
        # When
        result = processor.analyze_a4_drawing(test_image)
        
        # Then
        assert result.is_valid_a4 == True
        assert result.orientation == "portrait"
        assert 208 <= result.width_mm <= 212  # ±2mm許容
        
    def test_画質向上処理_低品質画像(self, processor):
        """低品質画像の画質向上処理をテスト"""
        # Given
        low_quality_image = "tests/fixtures/low_quality_drawing.png"
        
        # When
        enhanced = processor.enhance_drawing(low_quality_image)
        
        # Then
        assert enhanced.quality_score > 0.6
        assert enhanced.contrast_improved == True
```

### モックとスタブの使用
```python
# OpenAI APIのモック
@pytest.fixture
def mock_openai_response():
    """OpenAI APIレスポンスのモック"""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "部品番号": {"value": "A-123", "confidence": 0.95},
                    "材質": {"value": "SUS304", "confidence": 0.88}
                })
            }
        }]
    }

def test_gpt4_vision解析(mocker, mock_openai_response):
    """GPT-4 Vision APIを使用した図面解析のテスト"""
    # APIコールをモック
    mocker.patch('openai.ChatCompletion.create', 
                 return_value=mock_openai_response)
    
    agent = DrawingAnalysisAgent("dummy_key", ":memory:")
    result = agent.analyze_drawing("test.png")
    
    assert "部品番号" in result.extracted_data
    assert result.extracted_data["部品番号"].confidence > 0.9
```

## 主要コマンド

### アプリケーション実行
```bash
# Web UI起動（推奨）
py main.py ui

# バッチ処理
py main.py batch
py main.py batch --input data/input --output data/output

# システムセットアップ（初回のみ）
py main.py setup

# システム状態確認
py main.py status
```

### テスト実行
```bash
# 全テスト実行
pytest

# カバレッジレポート付き
pytest --cov=src --cov-report=html

# 特定のテストのみ
pytest tests/unit/test_image_processor.py

# TDDモード（ファイル変更を監視）
pytest-watch
```

### 開発環境セットアップ
```bash
# 依存関係インストール
py -m pip install -r requirements.txt

# 開発用依存関係
py -m pip install pytest pytest-cov pytest-watch pytest-mock

# OpenAI APIキー設定（config.yaml）
```

## 🏗️ アーキテクチャ原則

### 設定管理
- 設定値は環境変数または設定ファイルから読み込む
- magic numberは定数として定義する
- ハードコードされた値は一切許可しない

### コード品質基準
- DRY原則を遵守する
- SOLID原則に従う
- 依存性注入を活用する

## 🧪 テスト戦略

### TDD実践ガイド
1. テストファーストアプローチを必須とする
2. テストケースは実際のビジネス要件を反映する
3. モックやスタブの使用時は実装詳細に依存しない
4. エッジケースを含む包括的なテストを作成する

### 禁止パターン
- テスト用の特別なコードパスの作成
- テストデータに特化したハードコード
- プロダクションコードでのテスト専用フラグ

## 🔧 開発ワークフロー

### 実装手順
1. ビジネス要件の理解と整理
2. インターフェース設計
3. テストケース作成（先にfailさせる）
4. 最小限の実装
5. リファクタリング
6. 継続的な品質チェック
7. **必須：Git コミット＆プッシュ**

### コミット前チェック
- linter/formatter実行
- すべてのテスト通過確認
- コードレビュー
- ハードコード検出ツール実行

## 🚨 Git コミット忘れ防止ルール

### 必須実行タイミング
1. **タスク完了時** - 必ずコミット
2. **エラー修正後** - 修正をすぐにコミット
3. **機能追加後** - 動作確認してからコミット
4. **リファクタリング後** - 品質向上をコミット
5. **設定変更後** - 設定の更新をコミット

### コミット忘れチェック方法
```bash
# 変更確認
git status

# まとめてコミット
git add -A && git commit -m "変更内容の説明" && git push origin main
```

### Claude Code Hooks活用
- `.claude/hooks/task-complete.sh` - タスク完了時の自動リマインダー
- `.claude/hooks/auto-commit-reminder.sh` - 強制リマインダー

### コミットメッセージ規約
```
形式: [種類] 簡潔な説明

例:
- feat: A4画像処理機能の追加
- fix: Unicode エンコーディングエラーの修正  
- docs: API設定ガイドの作成
- test: A4ImageProcessorのユニットテスト追加
- refactor: ハードコード値の設定ファイル化
```

## 📦 技術スタック固有ガイドライン

### [言語/フレームワーク名]
- 推奨パターン：[具体例]
- 非推奨パターン：[具体例]
- 設定管理方法：[具体例]

## 🚫 アンチパターン例

### ❌ 悪い例
```javascript
// テスト値がハードコードされている
function processUser() {
  if (userId === 123) return "test user";
  return "real user";
}

## アーキテクチャ詳細

### レイヤードアーキテクチャ
```
[UI層] - Streamlitベースのユーザーインターフェース
   ↓
[アプリケーション層] - ビジネスロジックとワークフロー管理  
   ↓
[サービス層] - 図面解析、データ処理、Excel出力などの主要機能
   ↓
[インフラ層] - データベース、ファイルシステム、外部API連携
```

### 主要コンポーネント

1. **main.py** - CLIインターフェース（ui, batch, setup, status, test）
2. **src/core/agent.py** - GPT-4 Vision解析エンジン
3. **src/utils/image_processor.py** - A4特化の画像処理
4. **src/ui/streamlit_app.py** - Webインターフェース
5. **src/utils/excel_manager.py** - Excel出力管理
6. **src/models/template.py** - テンプレート管理

### データフロー
1. 図面入力（Web UIアップロードまたはバッチディレクトリ）
2. A4検証と前処理（`image_processor.py`）
3. GPT-4 Vision解析（`agent.py`）
4. 信頼度スコアリング付きの結果抽出
5. ユーザーレビュー/修正（学習システムにフィードバック）
6. テンプレート付きExcel出力

## 重要な設定

### config.yaml構造
```yaml
openai:
  api_key: "your-api-key-here"  # 必須：GPT-4 Vision API
  model: "gpt-4-vision-preview"
  max_tokens: 2000
  temperature: 0.1

image_processing:
  target_dpi: 300  # 最適な結果のための推奨値
  auto_enhance: true
  noise_reduction: true

extraction:
  confidence_threshold: 0.7  # データ検証の閾値
  default_fields:
    - "部品番号"
    - "材質"
    - "寸法"

processing:
  batch_size: 10  # APIレート制限に基づいて調整
  max_workers: 4
```

### ディレクトリ構造
```
data/
  input/           # バッチ処理用入力図面
  output/          # 解析結果
  excel_output/    # Excel出力
  samples/         # テスト用サンプルA4図面
database/
  drawing_analysis.db  # 結果とテンプレートのSQLiteデータベース
logs/
  main.log         # アプリケーションログ
tests/
  unit/            # ユニットテスト
  integration/     # 統合テスト
  fixtures/        # テストデータ
```

## 開発上の重要事項

### A4特化の考慮事項
- システムは210×297mm図面を期待（±2mm許容）
- 非A4サイズは検証に失敗する可能性
- DPI検出と正規化が重要

### 日本語技術用語の最適化
- 部品番号、材質、寸法などの標準用語
- プロンプトエンジニアリングで日本語認識を強化
- 信頼度スコアで精度を監視

### APIレート制限の管理
- バッチ処理はOpenAIレート制限を尊重
- 設定でバッチサイズを調整可能
- リトライメカニズムを実装

### 学習システム
- ユーザー修正で将来の精度向上
- テンプレートマッチングで効率化
- 継続的な改善サイクル

## 一般的な開発タスク

### 新しい抽出フィールドの追加
1. `src/models/analysis_result.py`に新フィールド追加
2. `src/core/agent.py`のプロンプト修正
3. 関連ページにUIコンポーネント追加
4. Excelエクスポートテンプレート更新
5. **テストを先に書く（TDD）**

### 画像処理のデバッグ
- `test_image_processor_direct.py`で単独テスト
- `logs/main.log`で処理詳細確認
- `image_processor.py`でA4サイズ検出を検証

### 解析プロンプトの修正
- `src/core/agent.py`の`_create_analysis_prompt()`メソッド
- `data/samples/`のサンプル図面でテスト
- プロンプト効果の信頼度スコアを監視

## トラブルシューティング

### よくある問題
1. **ModuleNotFoundError**
   - `py -m pip install -r requirements.txt`を実行
   
2. **OpenAI API エラー**
   - config.yamlのAPIキーを確認
   - レート制限を確認
   
3. **画像処理エラー**
   - 入力画像の形式を確認（PNG推奨）
   - DPI設定を確認

### デバッグモード
```bash
# 詳細ログ出力
py main.py --debug ui

# 特定モジュールのテスト
py -m pytest tests/unit/test_image_processor.py -v
```