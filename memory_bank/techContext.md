# 技術コンテキスト：A4図面解析システム

## 技術スタック

### フロントエンド
- **Streamlit**: Pythonベースの高速WebUIフレームワーク
  - バージョン: 1.22.0以上
  - 主な用途: インタラクティブなユーザーインターフェース構築
  - 利点: 少ないコードで高機能なUIを構築可能、データサイエンス向け機能が充実

### バックエンド
- **Python**: コアプログラミング言語
  - バージョン: 3.8以上（3.10推奨）
  - 主な用途: 全体のロジック実装、画像処理、API連携
  - 利点: 豊富なライブラリ、読みやすい構文、AI/ML分野での標準言語

- **OpenAI API**: 図面解析のAIエンジン
  - モデル: GPT-4 Vision
  - 主な用途: 図面からのテキスト・要素抽出、コンテキスト理解
  - 利点: 高精度な画像認識、柔軟なプロンプト設計、継続的な改善

### 画像処理
- **OpenCV**: コンピュータビジョンライブラリ
  - バージョン: 4.5以上
  - 主な用途: 図面の前処理、特徴抽出、品質向上
  - 利点: 高速処理、豊富な画像処理アルゴリズム

- **Pillow (PIL)**: Pythonイメージ処理ライブラリ
  - バージョン: 9.0以上
  - 主な用途: 基本的な画像操作、メタデータ処理
  - 利点: 使いやすいAPI、幅広いフォーマットサポート

- **pdf2image**: PDF変換ライブラリ
  - バージョン: 1.16以上
  - 主な用途: PDFファイルを画像に変換
  - 依存: Poppler（外部依存）

### データ処理
- **Pandas**: データ分析ライブラリ
  - バージョン: 1.4以上
  - 主な用途: 抽出データの構造化、集計、変換
  - 利点: 強力なデータフレーム操作、高速処理

- **NumPy**: 数値計算ライブラリ
  - バージョン: 1.20以上
  - 主な用途: 行列操作、数値計算
  - 利点: 効率的な数値演算、多次元配列サポート

- **OpenPyXL**: Excelファイル操作ライブラリ
  - バージョン: 3.0以上
  - 主な用途: エクセルファイルの生成、書式設定
  - 利点: 詳細なエクセル書式制御、セル単位の操作

### データベース
- **SQLite**: 軽量データベース
  - バージョン: 3.35以上
  - 主な用途: 解析結果、テンプレート、学習データの保存
  - 利点: ファイルベースで導入が容易、トランザクションサポート

## 開発環境

### 推奨開発環境
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **IDE**: Visual Studio Code + Python拡張
- **パッケージ管理**: pip, venv（仮想環境）
- **バージョン管理**: Git
- **テスト**: pytest
- **コード品質**: flake8, black, isort

### 環境構築手順
```bash
# リポジトリクローン
git clone <repository-url>
cd drawing_analysis_system

# 仮想環境作成
python -m venv venv

# 仮想環境アクティベート
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 開発用依存関係（オプション）
pip install -r requirements-dev.txt
```

### 外部依存関係
- **Poppler**: PDFレンダリングライブラリ（pdf2imageの依存）
  - Windows: poppler-windows
  - Mac: brew install poppler
  - Linux: apt-get install poppler-utils

## 技術的制約

### OpenAI API制約
- **レート制限**: 1分あたりのリクエスト数制限（ティアによる）
- **トークン制限**: リクエスト/レスポンスのトークン数上限
- **画像サイズ制限**: 最大20MBまでの画像サイズ
- **コスト**: APIコール数に応じた課金

### 画像処理制約
- **メモリ使用量**: 高解像度画像処理時のメモリ消費
- **処理時間**: 複雑な画像処理の実行時間
- **対応フォーマット**: PNG, JPEG, PDF, TIFFのみサポート

### システム要件
- **最小メモリ**: 4GB RAM（8GB以上推奨）
- **ストレージ**: 5GB以上の空き容量
- **CPU**: マルチコアプロセッサ推奨
- **ネットワーク**: OpenAI API接続用の安定したインターネット接続

## アーキテクチャ詳細

### モジュール構成
```
drawing_analysis_system/
├── src/                       # ソースコード
│   ├── core/                  # コア機能
│   │   ├── agent.py          # 図面解析エージェント
│   │   └── template_manager.py # テンプレート管理
│   │
│   ├── ui/                    # Streamlit UI
│   │   ├── streamlit_app.py  # メインアプリ
│   │   ├── components.py     # UIコンポーネント
│   │   └── pages/            # 各ページ
│   │
│   ├── utils/                 # ユーティリティ
│   │   ├── config.py         # 設定管理
│   │   ├── database.py       # データベース操作
│   │   ├── image_processor.py # A4画像処理
│   │   ├── file_handler.py   # ファイル操作
│   │   └── excel_manager.py  # エクセル出力
│   │
│   └── models/               # データモデル
│       ├── drawing.py        # 図面データモデル
│       ├── template.py       # テンプレートモデル
│       └── analysis_result.py # 解析結果モデル
```

### 主要クラス
1. **DrawingAnalysisAgent**: 図面解析の中核クラス
   - OpenAI APIとの連携
   - 解析ワークフロー管理
   - テンプレート活用

2. **A4ImageProcessor**: A4図面特化の画像処理クラス
   - A4サイズ検出・最適化
   - 画質向上処理
   - レイアウト特徴抽出

3. **ExcelManager**: エクセル出力管理クラス
   - 解析結果のエクセル変換
   - 書式設定と視覚化
   - バッチレポート生成

4. **DatabaseManager**: データベース操作クラス
   - 解析結果の保存・取得
   - テンプレート管理
   - 学習データ蓄積

### データモデル
1. **DrawingInfo**: 図面の基本情報
   ```python
   class DrawingInfo:
       file_path: str
       file_name: str
       file_size: int
       file_format: DrawingFormat
       dimensions: DrawingDimensions
       orientation: DrawingOrientation
       quality: DrawingQuality
   ```

2. **AnalysisResult**: 解析結果
   ```python
   class AnalysisResult:
       result_id: str
       drawing_path: str
       extracted_data: Dict[str, ExtractionResult]
       template_id: Optional[str]
       product_type: Optional[str]
       confidence_score: float
       processing_metrics: ProcessingMetrics
       quality_metrics: QualityMetrics
       a4_info: Dict[str, Any]
       metadata: Dict[str, Any]
       created_at: datetime
   ```

3. **ExtractionResult**: 抽出フィールド結果
   ```python
   class ExtractionResult:
       field_name: str
       value: Any
       confidence: float
       position: Optional[Dict[str, int]]
       extraction_method: ExtractionMethod
       field_type: FieldType
       validation_status: str
       raw_value: Optional[str]
       notes: Optional[str]
   ```

## API設計

### OpenAI Vision API連携
```python
def _analyze_with_template(self, image_path: str, template: DrawingTemplate, request: DrawingAnalysisRequest) -> Dict[str, Any]:
    # 画像をbase64エンコード
    image_data = self._encode_image(image_path)
    
    # テンプレート専用プロンプト
    template_prompt = f"""
{self.base_prompt}

## テンプレート情報
テンプレート名: {template.template_name}
製品タイプ: {template.product_type.value}
図面向き: {template.orientation.value}

## 抽出対象フィールド
{template.generate_extraction_prompt()}
"""
    
    # API呼び出し
    response = self.client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": template_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }
                ]
            }
        ],
        max_tokens=2500,
        temperature=0.1
    )
    
    # 結果をJSONとしてパース
    result = json.loads(response.choices[0].message.content)
    return result
```

### データベースAPI
```python
def save_analysis_result(self, result_data: Dict[str, Any]) -> int:
    """解析結果をデータベースに保存"""
    
    with self.get_connection() as conn:
        cursor = conn.cursor()
        
        # 基本情報の保存
        cursor.execute("""
        INSERT INTO analysis_results
        (drawing_path, template_id, product_type, confidence_score, 
         processing_time, extracted_data, a4_info, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            result_data['drawing_path'],
            result_data['template_id'],
            result_data['product_type'],
            result_data['confidence_score'],
            result_data['processing_time'],
            json.dumps(result_data['extracted_data']),
            json.dumps(result_data.get('a4_info', {}))
        ))
        
        result_id = cursor.lastrowid
        return result_id
```

## 設定管理

### 設定ファイル (config.yaml)
```yaml
# OpenAI API設定
openai:
  api_key: "your-api-key-here"
  model: "gpt-4-vision-preview"
  max_tokens: 2000
  temperature: 0.1
  retry_attempts: 3
  retry_delay: 2

# 画像処理設定
image_processing:
  target_dpi: 300
  auto_enhance: true
  noise_reduction: true
  contrast_adjustment: true
  max_image_size_mb: 10

# 抽出設定
extraction:
  confidence_threshold: 0.7
  auto_correction: true
  default_fields:
    - "部品番号"
    - "材質"
    - "寸法"
    - "表面処理"
    - "公差"

# データベース設定
database:
  path: "database/drawing_analysis.db"
  backup_interval: 7  # 日数

# バッチ処理設定
processing:
  max_workers: 4
  batch_size: 10
  timeout: 120  # 秒
```

### 設定読み込み
```python
class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"設定ファイル読み込みエラー: {e}")
            return {}
    
    def get_openai_config(self) -> Dict[str, Any]:
        """OpenAI API設定を取得"""
        return self.config.get('openai', {})
    
    def get_image_processing_config(self) -> Dict[str, Any]:
        """画像処理設定を取得"""
        return self.config.get('image_processing', {})
```

## テスト戦略

### ユニットテスト
- **対象**: 個別クラス・関数の機能テスト
- **ツール**: pytest
- **カバレッジ目標**: 80%以上

```python
# A4ImageProcessorのテスト例
def test_analyze_a4_drawing():
    processor = A4ImageProcessor()
    result = processor.analyze_a4_drawing("tests/data/sample_a4.png")
    
    assert result.is_valid_a4 == True
    assert result.orientation in ["portrait", "landscape"]
    assert 150 <= result.dpi <= 600
    assert 0 <= result.quality_score <= 1.0
```

### 統合テスト
- **対象**: コンポーネント間の連携テスト
- **ツール**: pytest + モック
- **重点領域**: API連携、データフロー

```python
# DrawingAnalysisAgentの統合テスト例
def test_analyze_drawing_with_template(mocker):
    # OpenAI APIをモック
    mock_response = mocker.patch('openai.ChatCompletion.create')
    mock_response.return_value = create_mock_response()
    
    # テンプレートをモック
    mock_template = mocker.patch('src.core.agent.DrawingAnalysisAgent._find_matching_template')
    mock_template.return_value = create_mock_template()
    
    agent = DrawingAnalysisAgent("dummy_key", "memory:test.db")
    result = agent.analyze_drawing("tests/data/sample_drawing.png")
    
    assert result.template_id is not None
    assert len(result.extracted_data) > 0
    assert result.confidence_score > 0.5
```

### エンドツーエンドテスト
- **対象**: 実際のワークフロー全体
- **ツール**: Streamlitテスト + Selenium
- **シナリオ**: ユーザーストーリーに基づくテスト

## パフォーマンス考慮事項

### 最適化ポイント
1. **画像処理の最適化**
   - 必要な解像度のみ処理（標準300DPI）
   - メモリ効率の良い処理方法
   - 並列処理の活用

2. **API呼び出しの最適化**
   - バッチ処理での効率的なAPI利用
   - レート制限を考慮した呼び出し間隔
   - キャッシュの活用

3. **データベースの最適化**
   - インデックス設計
   - クエリの最適化
   - 定期的なバキューム処理

### ベンチマーク
- **目標処理時間**: 1図面あたり30秒以内
- **バッチ処理効率**: 100図面/時間以上
- **メモリ使用量**: 最大1GB以内

## デプロイメント

### 開発環境から本番環境への移行
1. **環境変数の設定**
   - API鍵の安全な管理
   - 環境固有の設定分離

2. **データベース初期化**
   ```bash
   python main.py init-db
   ```

3. **初期テンプレートのインポート**
   ```bash
   python main.py import-templates --dir templates/
   ```

### 運用考慮事項
1. **バックアップ戦略**
   - データベースの定期バックアップ
   - 解析結果の定期エクスポート

2. **モニタリング**
   - API使用量の監視
   - エラー率のトラッキング
   - 処理時間の監視

3. **アップデート手順**
   ```bash
   # 最新コードの取得
   git pull origin main
   
   # 依存関係の更新
   pip install -r requirements.txt
   
   # データベースマイグレーション
   python main.py migrate
   ```

## 将来の技術的拡張

### 短期的な技術拡張
1. **マルチスレッド処理の強化**
   - 並列処理能力の向上
   - 処理キューの実装

2. **キャッシュ層の追加**
   - 頻繁に使用されるテンプレートのメモリキャッシュ
   - 解析結果の一時キャッシュ

3. **エラーハンドリングの強化**
   - より詳細なエラー分類
   - 自動リトライメカニズム

### 中長期的な技術拡張
1. **機械学習モデルの統合**
   - 独自の図面認識モデルの開発
   - OpenAI APIと併用するハイブリッドアプローチ

2. **マイクロサービス化**
   - 画像処理サービス
   - AI解析サービス
   - データ管理サービス

3. **クラウドネイティブ対応**
   - コンテナ化（Docker）
   - オーケストレーション（Kubernetes）
   - クラウドストレージ連携
