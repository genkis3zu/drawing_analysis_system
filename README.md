# A4図面解析システム

OpenAI GPT-4 Visionを使用したA4図面の自動データ抽出システムです。図面から部品番号、寸法、材質などの情報を自動抽出し、エクセルファイルに出力します。

## 🌟 主な特徴

- 📐 **A4図面特化**: A4サイズ図面に最適化された解析エンジン
- 🤖 **AI学習機能**: 使用するほど精度が向上する学習システム  
- 🖥️ **直感的なUI**: Streamlitベースの使いやすいWebインターフェース
- 📊 **エクセル出力**: 解析結果を自動的にエクセルファイルに出力
- 🔄 **バッチ処理**: 大量の図面を一括処理
- 📈 **テンプレート管理**: 類似図面の解析効率化

## 🏗️ システム構成

```
drawing_analysis_system/
├── main.py                     # メインエントリーポイント
├── config.yaml                # 設定ファイル
├── requirements.txt           # Python依存関係
│
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
│
├── data/                     # データディレクトリ
│   ├── input/               # 入力図面
│   ├── output/              # 出力結果  
│   ├── samples/             # サンプル図面
│   ├── excel_templates/     # エクセルテンプレート
│   └── excel_output/        # エクセル出力結果
│
└── database/                # SQLiteデータベース
    └── drawing_analysis.db
```

## 🚀 クイックスタート

### 1. 環境セットアップ

```bash
# リポジトリクローンまたはファイル配置
cd drawing_analysis_system

# Python仮想環境作成（推奨）
python -m venv venv

# 仮想環境アクティベート
# Windows:
venv\Scripts\activate
# Linux/Mac:  
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. システム初期化

```bash
# システムセットアップ（初回のみ）
python main.py setup

# システム状態確認
python main.py status

# 依存関係テスト
python main.py test
```

### 3. OpenAI APIキー設定

`config.yaml`を編集してAPIキーを設定：

```yaml
openai:
  api_key: "sk-your-actual-api-key-here"  # 実際のAPIキーに置き換え
```

### 4. Webアプリ起動

```bash
# StreamlitアプリをWebブラウザで起動
python main.py ui
```

ブラウザで **http://localhost:8501** にアクセス

## 📱 使用方法

### Web UI での基本操作

1. **図面アップロード**: A4図面ファイル（PNG, PDF, JPG）をアップロード
2. **製品タイプ選択**: 機械部品、電気部品などから選択  
3. **解析実行**: 「解析開始」ボタンをクリック
4. **結果確認**: 抽出されたデータを確認・修正
5. **エクセル出力**: 結果をエクセルファイルとしてダウンロード
6. **学習データ追加**: 修正内容を学習データとして保存

### コマンドライン使用

```bash
# バッチ処理（デフォルトディレクトリ）
python main.py batch

# ディレクトリ指定バッチ処理
python main.py batch --input data/input --output data/output

# システム状態確認
python main.py status

# 詳細ログ出力
python main.py ui --verbose
```

## 📋 対応ファイル形式

| 形式 | 拡張子 | 推奨度 | 備考 |
|------|--------|--------|------|
| PNG | .png | ⭐⭐⭐ | 最高品質、透明度対応 |
| PDF | .pdf | ⭐⭐⭐ | ベクター情報保持 |
| JPEG | .jpg, .jpeg | ⭐⭐ | 圧縮による品質劣化あり |
| TIFF | .tif, .tiff | ⭐⭐ | 高品質だがファイルサイズ大 |

## 🎯 抽出可能なデータ例

### 機械部品図面
- **部品番号**: P-12345、BOLT-M8x25など
- **材質**: S45C、SUS304、A5052など
- **寸法**: 100×50×25mm、φ20×30など
- **表面処理**: ニッケルメッキ、アルマイト、クロメートなど
- **精度・公差**: ±0.1mm、H7、6gなど

### 電気部品図面  
- **品番**: R-001、C-2200μFなど
- **定格**: DC12V 2A、AC100V 50/60Hzなど
- **温度範囲**: -20℃～+85℃など
- **精度**: ±5%、±1%など

## ⚙️ 主要設定項目

### OpenAI API設定
```yaml
openai:
  api_key: "your-api-key"           # APIキー
  model: "gpt-4-vision-preview"     # 使用モデル
  max_tokens: 2000                  # 最大トークン数
  temperature: 0.1                  # 一貫性重視で低く設定
```

### A4画像処理設定
```yaml
image_processing:
  target_dpi: 300                   # 目標解像度
  auto_enhance: true                # 自動画質向上
  noise_reduction: true             # ノイズ除去
  contrast_adjustment: true         # コントラスト調整
```

### 抽出設定
```yaml
extraction:
  confidence_threshold: 0.7         # 信頼度閾値
  auto_correction: true             # 自動補正
  default_fields:                   # デフォルト抽出フィールド
    - "部品番号"
    - "材質"
    - "寸法"
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. OpenAI API エラー
```
Error: OpenAI API rate limit exceeded
```
**対処法**: 
- API使用量とプランを確認
- `processing.batch_size`を小さくする
- `processing.retry_attempts`を増やす

#### 2. 画像認識精度の問題
**対処法**:
- 画像解像度を300DPI以上に向上
- A4サイズに正確にスキャン  
- 手動修正による学習データ蓄積
- 図面の文字をより鮮明に

#### 3. メモリ不足エラー
```
Error: Out of memory
```
**対処法**:
- `processing.max_workers`を減らす
- `processing.batch_size`を削減
- システムメモリを増設

#### 4. Streamlit起動エラー
```
ModuleNotFoundError: No module named 'streamlit'
```
**対処法**:
```bash
pip install streamlit
```

### ログ確認
```bash
# 最新ログ確認
tail -f logs/main.log

# エラーログ抽出
grep "ERROR" logs/main.log

# 詳細デバッグ実行
python main.py ui --verbose
```

## 📊 システム監視

### ダッシュボード機能
- 処理状況のリアルタイム表示
- エラー率・成功率の監視  
- システムリソース使用状況
- テンプレート使用統計

### 品質メトリクス
- 抽出精度の推移
- フィールド別信頼度
- 処理時間の分析
- ユーザー修正頻度

## 🚀 システム要件

### 推奨環境
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8以上（3.10推奨）
- **CPU**: 4コア以上
- **メモリ**: 8GB以上（16GB推奨）
- **ストレージ**: 10GB以上の空き容量
- **ネットワーク**: 高速インターネット接続（OpenAI API用）

### 最小環境
- **Python**: 3.8以上
- **メモリ**: 4GB以上
- **ストレージ**: 5GB以上の空き容量

## 🔒 セキュリティ

### APIキー管理
- 環境変数での管理を推奨
- 定期的なキーローテーション
- アクセス権限の最小化

### データ保護
- 機密図面の取り扱い注意
- ローカルデータベースの暗号化推奨
- 定期的なバックアップ

## 📚 追加リソース

### ドキュメント
- [設定リファレンス](docs/configuration.md)
- [APIリファレンス](docs/api_reference.md)
- [トラブルシューティング詳細](docs/troubleshooting.md)

### サンプル
- [サンプル図面](data/samples/)
- [設定例](examples/)
- [カスタマイズ例](examples/customization/)

## 🤝 サポート

### 技術サポート
- **Email**: support@company.com
- **Issue Tracker**: GitHub Issues
- **ドキュメント**: 社内Wiki

### アップデート
```bash
# 最新版の確認
git fetch origin
git log HEAD..origin/main --oneline

# 更新実行
git pull origin main
pip install -r requirements.txt
```

## 📄 ライセンス

このプロジェクトは社内利用に限定されます。

## 🎉 謝辞

このプロジェクトは以下の優秀な技術を使用しています：
- [OpenAI GPT-4 Vision](https://openai.com/) - AI画像解析
- [Streamlit](https://streamlit.io/) - Webアプリフレームワーク
- [OpenCV](https://opencv.org/) - 画像処理
- [Pandas](https://pandas.pydata.org/) - データ処理
- [OpenPyXL](https://openpyxl.readthedocs.io/) - エクセル操作

---

**最終更新**: 2024年6月11日  
**バージョン**: 1.0.0  
**作成者**: Your Company Development Team