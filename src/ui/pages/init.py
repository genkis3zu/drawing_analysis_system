# src/ui/pages/init.py

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.utils.config import SystemConfig
from src.ui.components import NotificationManager, MetricsDisplay

def show():
    """初期設定ページを表示"""
    
    st.title("🚀 システム初期設定")
    st.markdown("A4図面解析システムの初期設定を行います。")
    
    # 初期化状態確認
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    
    if st.session_state.initialized:
        show_initialized_state()
    else:
        show_initialization_form()

def show_initialized_state():
    """初期化済み状態を表示"""
    
    st.success("✅ システムは初期化されています")
    
    # 設定情報表示
    config = st.session_state.config
    
    if config:
        st.subheader("📊 システム情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 基本設定")
            st.markdown(f"**データベース**: `{config.get('database.path')}`")
            st.markdown(f"**入力ディレクトリ**: `{config.get('files.input_directory')}`")
            st.markdown(f"**出力ディレクトリ**: `{config.get('files.output_directory')}`")
        
        with col2:
            st.markdown("### 🤖 AI設定")
            api_key = config.get('openai.api_key', '')
            masked_key = "設定済み" if api_key and api_key != 'your-openai-api-key-here' else "未設定"
            st.markdown(f"**APIキー**: {masked_key}")
            st.markdown(f"**モデル**: `{config.get('openai.model')}`")
            st.markdown(f"**Temperature**: `{config.get('openai.temperature')}`")
    
    # ディレクトリ状態
    st.subheader("📁 ディレクトリ状態")
    
    directories = {
        "入力ディレクトリ": config.get('files.input_directory', 'data/input'),
        "出力ディレクトリ": config.get('files.output_directory', 'data/output'),
        "エクセル出力": config.get('excel.output_directory', 'data/excel_output'),
        "データベース": Path(config.get('database.path', 'database/drawing_analysis.db')).parent
    }
    
    col1, col2 = st.columns(2)
    
    for i, (name, path) in enumerate(directories.items()):
        with col1 if i % 2 == 0 else col2:
            path_obj = Path(path)
            if path_obj.exists():
                st.success(f"✅ {name}: 存在")
            else:
                st.error(f"❌ {name}: 存在しません")
                if st.button(f"{name}を作成", key=f"create_{i}"):
                    path_obj.mkdir(parents=True, exist_ok=True)
                    st.success(f"{name}を作成しました")
                    st.rerun()
    
    # 再初期化オプション
    with st.expander("🔄 再初期化", expanded=False):
        st.warning("⚠️ 再初期化を行うと、一部の設定がリセットされます")
        
        if st.button("再初期化を実行"):
            st.session_state.initialized = False
            st.rerun()

def show_initialization_form():
    """初期化フォームを表示"""
    
    st.info("🔧 初期設定を行います。必要な情報を入力してください。")
    
    with st.form("initialization_form"):
        st.subheader("🔑 OpenAI API設定")
        
        api_key = st.text_input(
            "OpenAI APIキー:",
            type="password",
            help="OpenAI APIキーを入力してください",
            placeholder="sk-..."
        )
        
        model = st.selectbox(
            "使用モデル:",
            ["gpt-4-vision-preview", "gpt-4", "gpt-4-turbo"],
            index=0,
            help="解析に使用するAIモデル"
        )
        
        st.subheader("📁 ディレクトリ設定")
        
        input_directory = st.text_input(
            "入力ディレクトリ:",
            value="data/input",
            help="処理対象の図面ファイルがあるディレクトリ"
        )
        
        output_directory = st.text_input(
            "出力ディレクトリ:",
            value="data/output",
            help="処理結果を保存するディレクトリ"
        )
        
        excel_directory = st.text_input(
            "エクセル出力ディレクトリ:",
            value="data/excel_output",
            help="エクセルファイルを保存するディレクトリ"
        )
        
        database_path = st.text_input(
            "データベースパス:",
            value="database/drawing_analysis.db",
            help="データベースファイルのパス"
        )
        
        # 初期化ボタン
        submit_button = st.form_submit_button("初期化を実行")
        
        if submit_button:
            if not api_key or not api_key.startswith('sk-'):
                st.error("有効なOpenAI APIキーを入力してください")
            else:
                initialize_system(
                    api_key=api_key,
                    model=model,
                    input_directory=input_directory,
                    output_directory=output_directory,
                    excel_directory=excel_directory,
                    database_path=database_path
                )
                st.success("✅ 初期化が完了しました")
                st.session_state.initialized = True
                st.rerun()

def initialize_system(api_key, model, input_directory, output_directory, excel_directory, database_path):
    """システムを初期化"""
    
    try:
        # 設定ファイル作成
        config = SystemConfig()
        
        # OpenAI設定
        config.update('openai.api_key', api_key)
        config.update('openai.model', model)
        config.update('openai.temperature', 0.1)
        config.update('openai.max_tokens', 2000)
        
        # ディレクトリ設定
        config.update('files.input_directory', input_directory)
        config.update('files.output_directory', output_directory)
        config.update('files.temp_directory', 'data/temp')
        
        # エクセル設定
        config.update('excel.template_directory', 'data/excel_templates')
        config.update('excel.output_directory', excel_directory)
        
        # データベース設定
        config.update('database.path', database_path)
        
        # 処理設定
        config.update('processing.batch_size', 10)
        config.update('processing.max_workers', 4)
        config.update('processing.timeout_seconds', 300)
        config.update('processing.retry_attempts', 3)
        
        # 画像処理設定
        config.update('image_processing.target_dpi', 300)
        config.update('image_processing.auto_enhance', True)
        config.update('image_processing.noise_reduction', True)
        config.update('image_processing.contrast_adjustment', True)
        
        # 抽出設定
        config.update('extraction.confidence_threshold', 0.7)
        config.update('extraction.auto_correction', True)
        
        # 学習設定
        config.update('learning.similarity_threshold', 0.85)
        config.update('learning.auto_learning', True)
        
        # UI設定
        config.update('ui.show_tips', True)
        config.update('ui.sidebar_state', 'expanded')
        config.update('ui.theme', 'light')
        
        # ロギング設定
        config.update('logging.level', 'INFO')
        config.update('logging.max_size_mb', 100)
        config.update('logging.backup_count', 5)
        
        # 設定保存
        config.save()
        
        # セッションに設定を保存
        st.session_state.config = config
        
        # ディレクトリ作成
        for directory in [input_directory, output_directory, excel_directory, 'data/temp', 'data/excel_templates']:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # データベースディレクトリ作成
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初期化完了フラグ
        st.session_state.initialized = True
        
        # 通知
        NotificationManager.show_success("システム初期化が完了しました")
        
    except Exception as e:
        st.error(f"初期化エラー: {e}")
        raise
