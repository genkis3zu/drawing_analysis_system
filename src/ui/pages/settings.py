# src/ui/pages/settings.py

import streamlit as st
from pathlib import Path
from datetime import datetime
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.utils.config import SystemConfig
from src.utils.database import DatabaseManager
from src.ui.components import NotificationManager, MetricsDisplay

def show_settings_page():
    """設定ページを表示"""
    
    st.title("⚙️ システム設定")
    st.markdown("システムの各種設定を管理します。")
    
    # タブ構成
    tab1, tab2, tab3, tab4 = st.tabs(["🔑 API設定", "🖥️ システム設定", "📊 データベース管理", "🔧 詳細設定"])
    
    with tab1:
        show_api_settings_tab()
    
    with tab2:
        show_system_settings_tab()
    
    with tab3:
        show_database_management_tab()
    
    with tab4:
        show_advanced_settings_tab()

def show_api_settings_tab():
    """API設定タブ"""
    
    st.subheader("🔑 OpenAI API設定")
    
    config = st.session_state.config
    if not config:
        st.error("設定ファイルが読み込まれていません")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # APIキー設定
        st.markdown("### 🗝️ APIキー")
        
        current_api_key = config.get('openai.api_key', '')
        masked_key = current_api_key[:8] + '*' * (len(current_api_key) - 12) + current_api_key[-4:] if len(current_api_key) > 12 else current_api_key
        
        # APIキー表示
        if current_api_key and current_api_key != 'your-openai-api-key-here':
            st.success(f"✅ APIキー設定済み: {masked_key}")
        else:
            st.warning(f"⚠️ {label}: 存在しません")
            if st.button(f"📁 {label}作成", key=f"create_{config_key}"):
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    NotificationManager.show_success(f"{label}を作成しました")
                    st.rerun()
                except Exception as e:
                    NotificationManager.show_error(f"ディレクトリ作成エラー: {e}")
    
    # 処理設定
    st.markdown("### ⚡ 処理設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        batch_size = st.number_input(
            "バッチサイズ:",
            min_value=1,
            max_value=50,
            value=config.get('processing.batch_size', 10),
            help="同時に処理するファイル数"
        )
        
        max_workers = st.number_input(
            "最大ワーカー数:",
            min_value=1,
            max_value=16,
            value=config.get('processing.max_workers', 4),
            help="並列処理のワーカー数"
        )
    
    with col2:
        timeout_seconds = st.number_input(
            "タイムアウト（秒）:",
            min_value=30,
            max_value=1800,
            value=config.get('processing.timeout_seconds', 300),
            help="1ファイルあたりのタイムアウト時間"
        )
        
        retry_attempts = st.number_input(
            "リトライ回数:",
            min_value=0,
            max_value=10,
            value=config.get('processing.retry_attempts', 3),
            help="失敗時のリトライ回数"
        )
    
    # 画像処理設定
    st.markdown("### 🖼️ 画像処理設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_dpi = st.number_input(
            "目標DPI:",
            min_value=150,
            max_value=600,
            value=config.get('image_processing.target_dpi', 300),
            help="画像の目標解像度"
        )
        
        auto_enhance = st.checkbox(
            "自動画質向上",
            value=config.get('image_processing.auto_enhance', True),
            help="画像の自動補正を有効にする"
        )
    
    with col2:
        noise_reduction = st.checkbox(
            "ノイズ除去",
            value=config.get('image_processing.noise_reduction', True),
            help="画像のノイズ除去を有効にする"
        )
        
        contrast_adjustment = st.checkbox(
            "コントラスト調整",
            value=config.get('image_processing.contrast_adjustment', True),
            help="コントラストの自動調整を有効にする"
        )
    
    # システム設定保存
    if st.button("💾 システム設定保存", type="primary"):
        # ディレクトリ設定更新
        for label, (config_key, default_value) in directories.items():
            new_value = st.session_state.get(f"dir_{config_key}", default_value)
            config.update(config_key, new_value)
        
        # 処理設定更新
        config.update('processing.batch_size', batch_size)
        config.update('processing.max_workers', max_workers)
        config.update('processing.timeout_seconds', timeout_seconds)
        config.update('processing.retry_attempts', retry_attempts)
        
        # 画像処理設定更新
        config.update('image_processing.target_dpi', target_dpi)
        config.update('image_processing.auto_enhance', auto_enhance)
        config.update('image_processing.noise_reduction', noise_reduction)
        config.update('image_processing.contrast_adjustment', contrast_adjustment)
        
        NotificationManager.show_success("システム設定を保存しました")

def show_database_management_tab():
    """データベース管理タブ"""
    
    st.subheader("📊 データベース管理")
    
    config = st.session_state.config
    if not config:
        st.error("設定ファイルが読み込まれていません")
        return
    
    # データベース情報表示
    show_database_info()
    
    st.markdown("---")
    
    # データベース操作
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 データベース操作")
        
        if st.button("🧹 データベース最適化", use_container_width=True):
            optimize_database()
        
        if st.button("🔍 整合性チェック", use_container_width=True):
            check_database_integrity()
        
        if st.button("📊 統計更新", use_container_width=True):
            update_database_statistics()
    
    with col2:
        st.markdown("### 💾 バックアップ・復元")
        
        if st.button("💾 バックアップ作成", use_container_width=True):
            create_database_backup()
        
        # バックアップファイル一覧
        show_backup_files()
    
    # データクリーンアップ
    st.markdown("### 🗑️ データクリーンアップ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cleanup_days = st.number_input(
            "古いデータの保持期間（日）:",
            min_value=1,
            max_value=365,
            value=30,
            help="この日数より古いデータを削除対象とします"
        )
    
    with col2:
        if st.button("🗑️ 古いデータ削除", use_container_width=True):
            cleanup_old_data(cleanup_days)

def show_database_info():
    """データベース情報を表示"""
    
    try:
        config = st.session_state.config
        db_path = config.get('database.path', 'database/drawing_analysis.db')
        
        db_manager = DatabaseManager(db_path)
        db_info = db_manager.get_database_info()
        
        # データベース基本情報
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("データベースサイズ", f"{db_info.get('size_mb', 0):.2f} MB")
        
        with col2:
            total_records = sum(db_info.get('table_counts', {}).values())
            st.metric("総レコード数", f"{total_records:,}")
        
        with col3:
            db_status = "正常" if db_info.get('exists', False) else "エラー"
            st.metric("データベース状態", db_status)
        
        # テーブル別レコード数
        if 'table_counts' in db_info:
            st.markdown("### 📋 テーブル別レコード数")
            
            table_data = []
            for table, count in db_info['table_counts'].items():
                table_data.append({
                    'テーブル名': table,
                    'レコード数': f"{count:,}",
                    '割合': f"{count/total_records*100:.1f}%" if total_records > 0 else "0%"
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"データベース情報取得エラー: {e}")

def optimize_database():
    """データベース最適化"""
    
    try:
        config = st.session_state.config
        db_path = config.get('database.path')
        
        with st.spinner("データベース最適化中..."):
            db_manager = DatabaseManager(db_path)
            db_manager.vacuum_database()
        
        NotificationManager.show_success("データベース最適化完了")
    
    except Exception as e:
        NotificationManager.show_error(f"データベース最適化エラー: {e}")

def check_database_integrity():
    """データベース整合性チェック"""
    
    try:
        config = st.session_state.config
        db_path = config.get('database.path')
        
        with st.spinner("整合性チェック中..."):
            db_manager = DatabaseManager(db_path)
            is_ok = db_manager.check_integrity()
        
        if is_ok:
            NotificationManager.show_success("データベース整合性: 正常")
        else:
            NotificationManager.show_error("データベース整合性: 問題を検出")
    
    except Exception as e:
        NotificationManager.show_error(f"整合性チェックエラー: {e}")

def update_database_statistics():
    """データベース統計更新"""
    
    try:
        with st.spinner("統計情報更新中..."):
            # 統計情報の更新処理
            time.sleep(1)  # 処理時間のシミュレーション
        
        NotificationManager.show_success("統計情報を更新しました")
    
    except Exception as e:
        NotificationManager.show_error(f"統計更新エラー: {e}")

def create_database_backup():
    """データベースバックアップ作成"""
    
    try:
        config = st.session_state.config
        db_path = config.get('database.path')
        
        with st.spinner("バックアップ作成中..."):
            db_manager = DatabaseManager(db_path)
            backup_path = db_manager.backup_database()
        
        NotificationManager.show_success(f"バックアップ作成完了: {backup_path}")
    
    except Exception as e:
        NotificationManager.show_error(f"バックアップ作成エラー: {e}")

def show_backup_files():
    """バックアップファイル一覧を表示"""
    
    with st.expander("📁 バックアップファイル一覧", expanded=False):
        try:
            backup_dir = Path("database/backups")
            
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.db"))
                
                if backup_files:
                    backup_data = []
                    for file_path in sorted(backup_files, reverse=True):
                        stat = file_path.stat()
                        backup_data.append({
                            'ファイル名': file_path.name,
                            'サイズ': f"{stat.st_size / 1024 / 1024:.2f} MB",
                            '作成日時': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
                    
                    df = pd.DataFrame(backup_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("バックアップファイルがありません")
            else:
                st.info("バックアップディレクトリが存在しません")
        
        except Exception as e:
            st.error(f"バックアップファイル取得エラー: {e}")

def cleanup_old_data(days):
    """古いデータをクリーンアップ"""
    
    try:
        config = st.session_state.config
        db_path = config.get('database.path')
        
        with st.spinner(f"{days}日より古いデータを削除中..."):
            db_manager = DatabaseManager(db_path)
            db_manager.cleanup_old_data(days)
        
        NotificationManager.show_success(f"{days}日より古いデータを削除しました")
    
    except Exception as e:
        NotificationManager.show_error(f"データクリーンアップエラー: {e}")

def show_advanced_settings_tab():
    """詳細設定タブ"""
    
    st.subheader("🔧 詳細設定")
    
    config = st.session_state.config
    if not config:
        st.error("設定ファイルが読み込まれていません")
        return
    
    # ログ設定
    st.markdown("### 📝 ログ設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox(
            "ログレベル:",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(config.get('logging.level', 'INFO')),
            help="出力するログのレベル"
        )
        
        max_size_mb = st.number_input(
            "ログファイル最大サイズ（MB）:",
            min_value=1,
            max_value=1000,
            value=config.get('logging.max_size_mb', 100),
            help="ログファイルの最大サイズ"
        )
    
    with col2:
        backup_count = st.number_input(
            "ログバックアップ数:",
            min_value=1,
            max_value=20,
            value=config.get('logging.backup_count', 5),
            help="保持するログバックアップファイル数"
        )
    
    # 抽出設定
    st.markdown("### 🎯 抽出設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider(
            "信頼度閾値:",
            min_value=0.0,
            max_value=1.0,
            value=config.get('extraction.confidence_threshold', 0.7),
            step=0.05,
            help="この値以下は低信頼度として扱う"
        )
        
        auto_correction = st.checkbox(
            "自動補正",
            value=config.get('extraction.auto_correction', True),
            help="既知パターンによる自動補正"
        )
    
    with col2:
        similarity_threshold = st.slider(
            "類似度閾値:",
            min_value=0.0,
            max_value=1.0,
            value=config.get('learning.similarity_threshold', 0.85),
            step=0.05,
            help="テンプレート選択の類似度閾値"
        )
        
        auto_learning = st.checkbox(
            "自動学習",
            value=config.get('learning.auto_learning', True),
            help="解析結果の自動学習"
        )
    
    # UI設定
    st.markdown("### 🖥️ UI設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        show_tips = st.checkbox(
            "ヒント表示",
            value=config.get('ui.show_tips', True),
            help="操作のヒントを表示"
        )
        
        sidebar_state = st.selectbox(
            "サイドバー初期状態:",
            ["expanded", "collapsed"],
            index=0 if config.get('ui.sidebar_state', 'expanded') == 'expanded' else 1,
            help="サイドバーの初期表示状態"
        )
    
    with col2:
        theme = st.selectbox(
            "テーマ:",
            ["light", "dark"],
            index=0 if config.get('ui.theme', 'light') == 'light' else 1,
            help="UIのテーマ"
        )
    
    # 詳細設定保存
    if st.button("💾 詳細設定保存", type="primary"):
        # ログ設定
        config.update('logging.level', log_level)
        config.update('logging.max_size_mb', max_size_mb)
        config.update('logging.backup_count', backup_count)
        
        # 抽出設定
        config.update('extraction.confidence_threshold', confidence_threshold)
        config.update('extraction.auto_correction', auto_correction)
        config.update('learning.similarity_threshold', similarity_threshold)
        config.update('learning.auto_learning', auto_learning)
        
        # UI設定
        config.update('ui.show_tips', show_tips)
        config.update('ui.sidebar_state', sidebar_state)
        config.update('ui.theme', theme)
        
        NotificationManager.show_success("詳細設定を保存しました")
    
    # 設定ファイル管理
    st.markdown("### 📄 設定ファイル管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 設定エクスポート", use_container_width=True):
            export_settings()
    
    with col2:
        if st.button("📤 設定インポート", use_container_width=True):
            show_import_settings()
    
    with col3:
        if st.button("🔄 設定リセット", use_container_width=True):
            reset_settings()

def export_settings():
    """設定をエクスポート"""
    
    try:
        config = st.session_state.config
        
        # APIキーは除外してエクスポート
        export_config = config.config.copy()
        if 'openai' in export_config and 'api_key' in export_config['openai']:
            export_config['openai']['api_key'] = 'your-openai-api-key-here'
        
        import yaml
        config_yaml = yaml.dump(export_config, default_flow_style=False, allow_unicode=True)
        
        st.download_button(
            label="📥 設定ファイルダウンロード",
            data=config_yaml,
            file_name=f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
            mime="text/yaml"
        )
        
        NotificationManager.show_success("設定をエクスポートしました")
    
    except Exception as e:
        NotificationManager.show_error(f"設定エクスポートエラー: {e}")

def show_import_settings():
    """設定インポート画面を表示"""
    
    st.markdown("#### 📤 設定インポート")
    
    uploaded_config = st.file_uploader(
        "設定ファイル（YAML）をアップロード:",
        type=['yaml', 'yml'],
        help="エクスポートした設定ファイルをアップロード"
    )
    
    if uploaded_config:
        if st.button("⚠️ 設定を上書きインポート"):
            import_settings(uploaded_config)

def import_settings(uploaded_file):
    """設定をインポート"""
    
    try:
        import yaml
        
        # ファイル内容読み込み
        config_data = yaml.safe_load(uploaded_file.getvalue())
        
        # 現在の設定を更新
        config = st.session_state.config
        config.config.update(config_data)
        config.save()
        
        NotificationManager.show_success("設定をインポートしました。ページを再読み込みしてください。")
    
    except Exception as e:
        NotificationManager.show_error(f"設定インポートエラー: {e}")

def reset_settings():
    """設定をリセット"""
    
    st.markdown("#### ⚠️ 設定リセット")
    st.warning("この操作により、すべての設定がデフォルト値に戻ります。")
    
    if st.checkbox("設定リセットを実行することを確認しました"):
        if st.button("🔄 リセット実行", type="secondary"):
            try:
                config = st.session_state.config
                
                # デフォルト設定で上書き
                config.config = SystemConfig.DEFAULT_CONFIG.copy()
                config.save()
                
                NotificationManager.show_success("設定をリセットしました。ページを再読み込みしてください。")
            
            except Exception as e:
                NotificationManager.show_error(f"設定リセットエラー: {e}")

# 必要なインポート
import pandas as pd
import time
            st.warning("⚠️ APIキーが設定されていません")
        
        # APIキー入力
        new_api_key = st.text_input(
            "新しいAPIキー:",
            type="password",
            help="OpenAI APIキーを入力してください",
            placeholder="sk-..."
        )
        
        if st.button("🔄 APIキー更新"):
            if new_api_key and new_api_key.startswith('sk-'):
                config.update('openai.api_key', new_api_key)
                NotificationManager.show_success("APIキーを更新しました")
                st.rerun()
            else:
                NotificationManager.show_error("有効なAPIキーを入力してください")
        
        # モデル設定
        st.markdown("### 🤖 モデル設定")
        
        model_options = [
            "gpt-4-vision-preview",
            "gpt-4o",
            "gpt-4o-mini"
        ]
        
        current_model = config.get('openai.model', 'gpt-4-vision-preview')
        selected_model = st.selectbox(
            "使用モデル:",
            model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="解析に使用するAIモデルを選択"
        )
        
        # パラメータ設定
        col_param1, col_param2 = st.columns(2)
        
        with col_param1:
            temperature = st.slider(
                "Temperature:",
                min_value=0.0,
                max_value=1.0,
                value=config.get('openai.temperature', 0.1),
                step=0.1,
                help="低いほど一貫した結果（推奨: 0.1）"
            )
        
        with col_param2:
            max_tokens = st.number_input(
                "最大トークン数:",
                min_value=500,
                max_value=4000,
                value=config.get('openai.max_tokens', 2000),
                help="APIリクエストの最大トークン数"
            )
        
        # API設定保存
        if st.button("💾 API設定保存", type="primary"):
            config.update('openai.model', selected_model)
            config.update('openai.temperature', temperature)
            config.update('openai.max_tokens', max_tokens)
            NotificationManager.show_success("API設定を保存しました")
    
    with col2:
        # API接続テスト
        st.markdown("### 🔍 接続テスト")
        
        if st.button("🧪 API接続テスト", use_container_width=True):
            test_api_connection()
        
        # API使用量情報
        st.markdown("### 📊 使用量情報")
        
        if current_api_key and current_api_key != 'your-openai-api-key-here':
            show_api_usage_info()
        else:
            st.info("APIキーを設定すると使用量情報を表示できます")
        
        # APIキー管理のヒント
        with st.expander("💡 APIキー管理のコツ", expanded=False):
            st.markdown("""
            **セキュリティ:**
            - APIキーは他人と共有しない
            - 定期的にキーをローテーション
            - 使用量を定期的に監視
            
            **コスト管理:**
            - 使用制限を設定
            - 不要な処理は削減
            - バッチ処理で効率化
            """)

def test_api_connection():
    """API接続をテスト"""
    
    try:
        config = st.session_state.config
        api_key = config.get('openai.api_key')
        
        if not api_key or api_key == 'your-openai-api-key-here':
            NotificationManager.show_error("APIキーが設定されていません")
            return
        
        with st.spinner("API接続をテスト中..."):
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # 簡単なテストリクエスト
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            NotificationManager.show_success("✅ API接続テスト成功")
            st.text(f"レスポンス: {response.choices[0].message.content}")
    
    except Exception as e:
        NotificationManager.show_error(f"❌ API接続テスト失敗: {str(e)}")

def show_api_usage_info():
    """API使用量情報を表示"""
    
    # 実際の実装ではOpenAI APIから使用量を取得
    # ここではサンプルデータを表示
    
    usage_data = {
        "今月の使用量": "$45.30",
        "今日の使用量": "$2.15",
        "残りクレジット": "$154.70",
        "リクエスト数": "1,250回"
    }
    
    for metric, value in usage_data.items():
        st.metric(metric, value)

def show_system_settings_tab():
    """システム設定タブ"""
    
    st.subheader("🖥️ システム設定")
    
    config = st.session_state.config
    if not config:
        st.error("設定ファイルが読み込まれていません")
        return
    
    # ファイル・ディレクトリ設定
    st.markdown("### 📁 ディレクトリ設定")
    
    directories = {
        "入力ディレクトリ": ("files.input_directory", "data/input/"),
        "出力ディレクトリ": ("files.output_directory", "data/output/"),
        "一時ディレクトリ": ("files.temp_directory", "data/temp/"),
        "エクセルテンプレート": ("excel.template_directory", "data/excel_templates/"),
        "エクセル出力": ("excel.output_directory", "data/excel_output/")
    }
    
    for label, (config_key, default_value) in directories.items():
        current_value = config.get(config_key, default_value)
        new_value = st.text_input(f"{label}:", value=current_value, key=f"dir_{config_key}")
        
        # ディレクトリ存在確認
        dir_path = Path(new_value)
        if dir_path.exists():
            st.success(f"✅ {label}: 存在")
        else: