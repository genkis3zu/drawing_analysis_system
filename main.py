#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A4図面解析システム メインエントリーポイント

Usage:
    python main.py ui                    # Streamlit UIを起動
    python main.py batch [options]      # バッチ処理実行
    python main.py setup                # システムセットアップ
    python main.py status               # システム状態確認
"""

import sys
import argparse
import logging
import subprocess
from pathlib import Path
import os

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import SystemConfig
from src.utils.database import DatabaseManager
from src.utils.file_handler import FileHandler

def setup_logging(config: SystemConfig):
    """ログ設定"""
    
    log_config = {
        'level': getattr(logging, config.get('logging.level', 'INFO')),
        'format': config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        'handlers': []
    }
    
    # ファイルハンドラー
    log_file = config.get('logging.file', 'logs/main.log')
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_config['format']))
    log_config['handlers'].append(file_handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_config['format']))
    log_config['handlers'].append(console_handler)
    
    logging.basicConfig(**log_config)

def init_project_structure():
    """プロジェクト構造を初期化"""
    
    directories = [
        'data/input',
        'data/output',
        'data/samples', 
        'data/temp',
        'data/excel_templates',
        'data/excel_output',
        'database',
        'logs'
    ]
    
    created_dirs = []
    for directory in directories:
        dir_path = PROJECT_ROOT / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(directory)
    
    if created_dirs:
        print(f"✅ ディレクトリを作成しました: {', '.join(created_dirs)}")
    
    return True

def run_streamlit_app():
    """Streamlit アプリケーションを起動"""
    
    try:
        streamlit_path = PROJECT_ROOT / "src" / "ui" / "streamlit_app.py"
        
        if not streamlit_path.exists():
            print(f"❌ Streamlitアプリファイルが見つかりません: {streamlit_path}")
            return False

def show_system_status():
    """システム状態を表示"""
    
    try:
        config = SystemConfig()
        
        print("📊 A4図面解析システム 状態確認")
        print("=" * 60)
        
        # 基本情報
        print("🏠 プロジェクト情報")
        print(f"   📂 プロジェクトルート: {PROJECT_ROOT}")
        print(f"   📄 設定ファイル: {config.config_path}")
        print(f"   ✅ 設定有効性: {'有効' if config.validate() else '無効'}")
        
        # データベース状態
        print("\n💾 データベース情報")
        db_config = config.get_database_config()
        db_path = Path(db_config['path'])
        
        if db_path.exists():
            db_size = db_path.stat().st_size / (1024 * 1024)  # MB
            print(f"   📍 パス: {db_path}")
            print(f"   📏 サイズ: {db_size:.2f} MB")
            
            # データベース統計
            try:
                db_manager = DatabaseManager(str(db_path))
                db_info = db_manager.get_database_info()
                
                if 'table_counts' in db_info:
                    print("   📋 テーブル情報:")
                    for table, count in db_info['table_counts'].items():
                        print(f"      - {table}: {count}件")
                
            except Exception as e:
                print(f"   ⚠️  データベース詳細取得エラー: {e}")
        else:
            print("   ❌ データベースファイルが存在しません")
        
        # ディレクトリ状態
        print("\n📁 ディレクトリ状態")
        directories = [
            ('入力', config.get('files.input_directory', 'data/input')),
            ('出力', config.get('files.output_directory', 'data/output')),
            ('サンプル', config.get('files.samples_directory', 'data/samples')),
            ('テンプレート', config.get('excel.template_directory', 'data/excel_templates'))
        ]
        
        for name, dir_path in directories:
            path = Path(dir_path)
            if path.exists():
                file_count = len(list(path.iterdir())) if path.is_dir() else 0
                print(f"   ✅ {name}: {path} ({file_count}ファイル)")
            else:
                print(f"   ❌ {name}: {path} (存在しません)")
        
        # API設定
        print("\n🔑 API設定")
        api_key = config.get('openai.api_key', '')
        if api_key and api_key != 'your-openai-api-key-here':
            print(f"   ✅ OpenAI API: 設定済み (***{api_key[-4:]})")
        else:
            print("   ❌ OpenAI API: 未設定")
        
        print(f"   🤖 モデル: {config.get('openai.model', 'gpt-4-vision-preview')}")
        
        # 依存関係チェック
        print("\n📦 依存関係")
        required_packages = [
            'openai', 'streamlit', 'pandas', 'opencv-python', 
            'Pillow', 'openpyxl', 'PyYAML'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package}: インストール済み")
            except ImportError:
                print(f"   ❌ {package}: 未インストール")
                missing.append(package)
        
        if missing:
            print(f"\n💡 不足パッケージのインストール:")
            print(f"   pip install {' '.join(missing)}")
        
        return len(missing) == 0
        
    except Exception as e:
        print(f"❌ システム状態確認エラー: {e}")
        return False

def setup_system():
    """システムセットアップ"""
    
    print("🔧 A4図面解析システム セットアップ")
    print("=" * 60)
    
    try:
        # 1. ディレクトリ初期化
        print("1️⃣ ディレクトリ構造を初期化...")
        init_project_structure()
        
        # 2. 設定ファイル確認・作成
        print("\n2️⃣ 設定ファイルを確認...")
        config = SystemConfig()
        
        if config.validate():
            print("   ✅ 設定ファイルは有効です")
        else:
            print("   ⚠️  設定ファイルに問題があります")
        
        # 3. データベース初期化
        print("\n3️⃣ データベースを初期化...")
        try:
            db_config = config.get_database_config()
            db_manager = DatabaseManager(db_config['path'])
            print("   ✅ データベース初期化完了")
        except Exception as e:
            print(f"   ❌ データベース初期化エラー: {e}")
        
        # 4. サンプルファイル作成
        print("\n4️⃣ サンプルファイルを作成...")
        create_sample_files()
        
        # 5. 依存関係チェック
        print("\n5️⃣ 依存関係をチェック...")
        if check_dependencies():
            print("   ✅ 全ての依存関係が満たされています")
        else:
            print("   ⚠️  不足している依存関係があります")
        
        print("\n" + "=" * 60)
        print("✅ セットアップ完了!")
        print("\n📋 次のステップ:")
        print("1. config.yaml でOpenAI APIキーを設定")
        print("2. python main.py ui でWebアプリを起動")
        print("3. data/samples/ のサンプル図面で動作確認")
        print("4. python main.py status でシステム状態を確認")
        
        return True
        
    except Exception as e:
        print(f"❌ セットアップエラー: {e}")
        return False

def create_sample_files():
    """サンプルファイルを作成"""
    
    # README for samples
    samples_dir = PROJECT_ROOT / "data" / "samples"
    readme_content = """# A4図面サンプルディレクトリ

このディレクトリにA4図面ファイルを配置してテストしてください。

## 対応フォーマット
- PNG (推奨)
- PDF
- JPG/JPEG  
- TIFF

## 推奨仕様
- A4サイズ (210×297mm)
- 解像度: 300DPI以上
- 文字が鮮明に読める品質

## 使用方法
1. 図面ファイルをこのディレクトリに配置
2. WebアプリまたはCLIで解析実行
3. 結果を確認・修正
4. 学習データとして蓄積

## サンプル図面の例
- 機械部品図面: ボルト、ナット、ブラケットなど
- 電気部品図面: 抵抗、コンデンサ、ICなど
- 組立図面: 製品の組み立て手順図
"""
    
    readme_path = samples_dir / "README.md"
    if not readme_path.exists():
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("   📄 サンプルREADME作成")
    
    # gitkeep for empty directories
    empty_dirs = [
        PROJECT_ROOT / "data" / "input",
        PROJECT_ROOT / "data" / "output",
        PROJECT_ROOT / "data" / "temp",
        PROJECT_ROOT / "data" / "excel_output"
    ]
    
    for dir_path in empty_dirs:
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()

def check_dependencies() -> bool:
    """依存関係をチェック"""
    
    required_packages = [
        'openai',
        'streamlit',
        'pandas', 
        'numpy',
        'opencv-python',
        'Pillow',
        'openpyxl',
        'PyYAML',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # パッケージ名の正規化
            import_name = package.replace('-', '_').replace('opencv_python', 'cv2')
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("   ❌ 不足している依存関係:")
        for package in missing_packages:
            print(f"      - {package}")
        print(f"\n   💡 インストールコマンド:")
        print(f"      pip install {' '.join(missing_packages)}")
        return False
    
    return True

def run_tests():
    """基本的なテストを実行"""
    
    print("🧪 システムテスト実行")
    print("=" * 40)
    
    tests_passed = 0
    tests_total = 0
    
    # テスト1: 設定ファイル読み込み
    tests_total += 1
    try:
        config = SystemConfig()
        if config.validate():
            print("✅ 設定ファイル読み込み")
            tests_passed += 1
        else:
            print("❌ 設定ファイル検証失敗")
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
    
    # テスト2: データベース接続
    tests_total += 1
    try:
        config = SystemConfig()
        db_manager = DatabaseManager(config.get('database.path'))
        db_info = db_manager.get_database_info()
        if db_info.get('exists', False):
            print("✅ データベース接続")
            tests_passed += 1
        else:
            print("❌ データベース接続失敗")
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
    
    # テスト3: 画像処理
    tests_total += 1
    try:
        from src.utils.image_processor import A4ImageProcessor
        processor = A4ImageProcessor()
        print("✅ 画像処理モジュール")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 画像処理モジュールエラー: {e}")
    
    # テスト4: エクセル処理
    tests_total += 1
    try:
        from src.utils.excel_manager import ExcelManager
        excel_manager = ExcelManager()
        print("✅ エクセル処理モジュール")
        tests_passed += 1
    except Exception as e:
        print(f"❌ エクセル処理モジュールエラー: {e}")
    
    print(f"\n📊 テスト結果: {tests_passed}/{tests_total} 通過")
    return tests_passed == tests_total

def main():
    """メイン関数"""
    
    parser = argparse.ArgumentParser(
        description="A4図面解析システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py ui                     # WebアプリUI起動
  python main.py batch                  # バッチ処理実行
  python main.py batch -i input/ -o output/  # ディレクトリ指定バッチ処理
  python main.py setup                  # システムセットアップ
  python main.py status                 # システム状態確認
  python main.py test                   # システムテスト実行
        """
    )
    
    parser.add_argument(
        'command',
        choices=['ui', 'batch', 'setup', 'status', 'test'],
        help='実行コマンド'
    )
    
    parser.add_argument(
        '--input', '-i',
        help='入力ディレクトリ (batch用)',
        default=None
    )
    
    parser.add_argument(
        '--output', '-o', 
        help='出力ディレクトリ (batch用)',
        default=None
    )
    
    parser.add_argument(
        '--config', '-c',
        help='設定ファイルパス',
        default='config.yaml'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細ログ出力'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Streamlitポート番号 (ui用)'
    )
    
    args = parser.parse_args()
    
    # 設定読み込み
    try:
        os.environ['STREAMLIT_CONFIG_PATH'] = args.config
        config = SystemConfig(args.config)
        
        if args.verbose:
            config.set('logging.level', 'DEBUG')
        
        setup_logging(config)
        
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        if args.command != 'setup':
            print("💡 python main.py setup でセットアップを実行してください")
            return 1
    
    # ログ設定
    logger = logging.getLogger(__name__)
    logger.info(f"A4図面解析システム開始: {args.command}")
    
    try:
        success = False
        
        if args.command == 'ui':
            success = run_streamlit_app()
            
        elif args.command == 'batch':
            success = run_batch_processing(
                input_dir=args.input,
                output_dir=args.output
            )
            
        elif args.command == 'setup':
            success = setup_system()
            
        elif args.command == 'status':
            success = show_system_status()
            
        elif args.command == 'test':
            success = run_tests()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 ユーザーによって中断されました")
        return 1
        
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        print(f"❌ 予期しないエラーが発生しました: {e}")
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        return 1

if __name__ == "__main__":
    exit(main())
        
        # Streamlit コマンド構築
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(streamlit_path),
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false",
            "--server.fileWatcherType", "none"
        ]
        
        print("🚀 A4図面解析システムを起動しています...")
        print("   📍 URL: http://localhost:8501")
        print("   ⏹️  停止: Ctrl+C")
        print("   📚 ヘルプ: http://localhost:8501 にアクセス後、サイドバーを確認")
        print("-" * 60)
        
        # Streamlit実行
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n✅ アプリケーションを停止しました")
        return True
    except FileNotFoundError:
        print("❌ Streamlitがインストールされていません")
        print("   💡 インストール: pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Streamlit起動エラー: {e}")
        return False

def run_batch_processing(input_dir: str = None, output_dir: str = None, **options):
    """バッチ処理を実行"""
    
    try:
        # 設定読み込み
        config = SystemConfig()
        
        # ディレクトリ設定
        input_dir = input_dir or config.get('files.input_directory', 'data/input')
        output_dir = output_dir or config.get('files.output_directory', 'data/output')
        
        print(f"📁 入力ディレクトリ: {input_dir}")
        print(f"📁 出力ディレクトリ: {output_dir}")
        
        # 入力ファイルチェック
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"❌ 入力ディレクトリが存在しません: {input_dir}")
            return False
        
        # 対応ファイル検索
        file_handler = FileHandler()
        supported_formats = config.get('files.supported_formats', ['.jpg', '.png', '.pdf'])
        
        input_files = []
        for ext in supported_formats:
            input_files.extend(input_path.glob(f"*{ext}"))
            input_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        if not input_files:
            print(f"⚠️  処理対象ファイルが見つかりません")
            print(f"   対応形式: {', '.join(supported_formats)}")
            return False
        
        print(f"🔍 処理対象: {len(input_files)}ファイル")
        print("🔄 バッチ処理を開始します...")
        
        # バッチ処理実行
        from src.core.agent import create_agent_from_config
        from src.utils.batch_processor import BatchProcessor
        
        agent = create_agent_from_config(config)
        processor = BatchProcessor(agent, config)
        
        results = processor.process_directory(input_dir, output_dir)
        
        # 結果表示
        print("\n" + "=" * 50)
        print("📊 バッチ処理結果")
        print("=" * 50)
        print(f"総ファイル数: {results.get('total_files', 0)}")
        print(f"処理成功: {results.get('processed', 0)}")
        print(f"処理失敗: {len(results.get('errors', []))}")
        print(f"処理時間: {results.get('processing_time', 0):.1f}秒")
        
        if results.get('errors'):
            print("\n❌ エラー詳細:")
            for error in results['errors'][:5]:  # 最初の5件
                print(f"   - {error.get('file', '不明')}: {error.get('error', '不明なエラー')}")
            
            if len(results['errors']) > 5:
                print(f"   ... 他{len(results['errors']) - 5}件のエラー")
        
        return True
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")