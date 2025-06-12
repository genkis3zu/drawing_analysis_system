# src/ui/pages/batch.py

import streamlit as st
import pandas as pd
import time
from pathlib import Path
from datetime import datetime
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.agent import create_agent_from_config
from src.utils.batch_processor import BatchProcessor
from src.utils.file_handler import FileHandler
from src.utils.excel_manager import ExcelManager
from src.ui.components import (
    FileUploader, ProgressTracker, NotificationManager, 
    MetricsDisplay, DataExporter, StatisticsChart
)

def show():
    """バッチ処理ページを表示"""
    
    st.title("🔄 バッチ処理")
    st.markdown("複数の図面ファイルを一括で処理します。")
    
    # タブ構成
    tab1, tab2, tab3 = st.tabs(["📁 バッチ実行", "📊 処理結果", "📈 統計・履歴"])
    
    # アクティブタブの管理
    if 'active_batch_tab' not in st.session_state:
        st.session_state.active_batch_tab = "📁 バッチ実行"
    
    # タブ切り替え
    if st.session_state.active_batch_tab == "📁 バッチ実行":
        with tab1:
            show_batch_execution_tab()
    elif st.session_state.active_batch_tab == "📊 処理結果":
        with tab2:
            show_batch_results_tab()
    else:
        with tab3:
            show_batch_statistics_tab()

def show_batch_execution_tab():
    """バッチ実行タブ"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📂 ディレクトリ設定")
        
        # 入力ディレクトリ設定
        default_input = st.session_state.config.get('files.input_directory', 'data/input') if st.session_state.config else 'data/input'
        input_directory = st.text_input(
            "入力ディレクトリ:",
            value=default_input,
            help="処理対象の図面ファイルがあるディレクトリ"
        )
        
        # 出力ディレクトリ設定
        default_output = st.session_state.config.get('files.output_directory', 'data/output') if st.session_state.config else 'data/output'
        output_directory = st.text_input(
            "出力ディレクトリ:",
            value=default_output,
            help="処理結果を保存するディレクトリ"
        )
        
        # ディレクトリ状態確認
        check_directories(input_directory, output_directory)
        
        # ファイル一覧表示
        show_file_list(input_directory)
        
        # バッチ処理設定
        st.subheader("⚙️ バッチ処理設定")
        
        col_set1, col_set2 = st.columns(2)
        
        with col_set1:
            batch_size = st.number_input(
                "バッチサイズ:",
                min_value=1,
                max_value=50,
                value=10,
                help="同時に処理するファイル数"
            )
            
            max_workers = st.number_input(
                "並列処理数:",
                min_value=1,
                max_value=8,
                value=4,
                help="並列で実行するワーカー数"
            )
        
        with col_set2:
            timeout_minutes = st.number_input(
                "タイムアウト（分）:",
                min_value=1,
                max_value=60,
                value=5,
                help="1ファイルあたりのタイムアウト時間"
            )
            
            retry_attempts = st.number_input(
                "リトライ回数:",
                min_value=0,
                max_value=5,
                value=2,
                help="失敗時のリトライ回数"
            )
        
        # 処理オプション
        with st.expander("🔧 処理オプション", expanded=False):
            
            # 製品タイプ自動判定
            auto_product_type = st.checkbox(
                "製品タイプ自動判定",
                value=True,
                help="ファイル名や内容から製品タイプを自動判定"
            )
            
            # デフォルト製品タイプ
            if not auto_product_type:
                default_product_type = st.selectbox(
                    "デフォルト製品タイプ:",
                    ["機械部品", "電気部品", "組立図", "配線図", "その他"],
                    help="自動判定しない場合のデフォルト"
                )
            else:
                default_product_type = None
            
            # エラー処理
            error_handling = st.selectbox(
                "エラー処理:",
                ["続行", "停止", "スキップ"],
                index=0,
                help="エラー発生時の処理方法"
            )
            
            # 出力形式
            output_formats = st.multiselect(
                "出力形式:",
                ["JSON", "Excel", "CSV"],
                default=["JSON", "Excel"],
                help="処理結果の出力形式"
            )
        
        # バッチ実行ボタン
        st.markdown("---")
        
        if st.button("🚀 バッチ処理開始", type="primary", use_container_width=True):
            execute_batch_processing(
                input_directory,
                output_directory,
                {
                    'batch_size': batch_size,
                    'max_workers': max_workers,
                    'timeout_minutes': timeout_minutes,
                    'retry_attempts': retry_attempts,
                    'auto_product_type': auto_product_type,
                    'default_product_type': default_product_type,
                    'error_handling': error_handling,
                    'output_formats': output_formats
                }
            )
    
    with col2:
        st.subheader("📊 処理状況")
        
        # 現在の処理状況
        if st.session_state.get('batch_processing', False):
            show_batch_progress()
        else:
            show_batch_summary()
        
        # 最近のバッチ履歴
        show_recent_batch_history()

def check_directories(input_dir, output_dir):
    """ディレクトリの存在確認"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        input_path = Path(input_dir)
        if input_path.exists():
            file_count = len(list(input_path.glob('*')))
            st.success(f"✅ 入力ディレクトリ存在 ({file_count}ファイル)")
        else:
            st.error("❌ 入力ディレクトリが存在しません")
    
    with col2:
        output_path = Path(output_dir)
        if output_path.exists():
            st.success("✅ 出力ディレクトリ存在")
        else:
            st.warning("⚠️ 出力ディレクトリを作成します")

def show_file_list(input_directory):
    """処理対象ファイル一覧を表示"""
    
    with st.expander("📋 処理対象ファイル一覧", expanded=False):
        try:
            input_path = Path(input_directory)
            if not input_path.exists():
                st.warning("ディレクトリが存在しません")
                return
            
            # 対応ファイルを検索
            supported_formats = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff']
            files = []
            
            for ext in supported_formats:
                files.extend(list(input_path.glob(f"*{ext}")))
                files.extend(list(input_path.glob(f"*{ext.upper()}")))
            
            if files:
                # ファイル情報テーブル
                file_data = []
                for file_path in sorted(files):
                    stat = file_path.stat()
                    file_data.append({
                        'ファイル名': file_path.name,
                        'サイズ': f"{stat.st_size / 1024:.1f} KB",
                        '更新日': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        '形式': file_path.suffix.upper()
                    })
                
                df = pd.DataFrame(file_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.info(f"📁 処理対象: {len(files)}ファイル")
            else:
                st.warning(f"対応ファイルが見つかりません\n対応形式: {', '.join(supported_formats)}")
        
        except Exception as e:
            st.error(f"ファイル一覧取得エラー: {e}")

def show_batch_progress():
    """バッチ処理進捗を表示"""
    
    st.markdown("### ⏳ 処理中...")
    
    # 進捗情報取得
    progress_info = st.session_state.get('batch_progress', {})
    
    # 全体進捗
    total_files = progress_info.get('total_files', 0)
    processed_files = progress_info.get('processed_files', 0)
    
    if total_files > 0:
        progress = processed_files / total_files
        st.progress(progress)
        st.text(f"進捗: {processed_files}/{total_files} ({progress*100:.0f}%)")
    
    # 詳細情報
    if progress_info:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("処理済み", processed_files)
        
        with col2:
            st.metric("成功", progress_info.get('successful', 0))
        
        with col3:
            st.metric("エラー", progress_info.get('errors', 0))
        
        # 現在処理中のファイル
        current_file = progress_info.get('current_file')
        if current_file:
            st.text(f"処理中: {current_file}")
        
        # 経過時間
        start_time = progress_info.get('start_time')
        if start_time:
            elapsed = time.time() - start_time
            st.text(f"経過時間: {elapsed:.0f}秒")

def show_batch_summary():
    """バッチ処理サマリーを表示"""
    
    st.markdown("### 📈 処理サマリー")
    
    # 最後の処理結果
    last_batch = st.session_state.get('last_batch_result')
    
    if last_batch:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総ファイル数", last_batch.get('total_files', 0))
        
        with col2:
            st.metric("成功率", f"{last_batch.get('success_rate', 0):.1%}")
        
        with col3:
            st.metric("処理時間", f"{last_batch.get('total_time', 0):.0f}秒")
        
        # エラー情報
        errors = last_batch.get('errors', [])
        if errors:
            with st.expander(f"⚠️ エラー詳細 ({len(errors)}件)", expanded=False):
                for error in errors[:10]:  # 最大10件表示
                    st.text(f"❌ {error.get('file', '不明')}: {error.get('error', 'エラー詳細なし')}")
    else:
        st.info("まだバッチ処理が実行されていません")

def show_recent_batch_history():
    """最近のバッチ履歴を表示"""
    
    with st.expander("📝 最近のバッチ履歴", expanded=False):
        try:
            config = st.session_state.config
            if config:
                agent = create_agent_from_config(config)
                history = agent.get_batch_history(limit=5)
                
                if history:
                    history_data = []
                    for item in history:
                        history_data.append({
                            "実行日時": datetime.fromisoformat(item['created_at']).strftime("%Y-%m-%d %H:%M"),
                            "ファイル数": item['total_files'],
                            "成功": item['successful_files'],
                            "エラー": item['error_files'],
                            "処理時間": f"{item['total_time']:.0f}秒"
                        })
                    
                    df = pd.DataFrame(history_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("バッチ処理履歴がありません")
        except Exception as e:
            st.error(f"履歴取得エラー: {e}")

def show_batch_results_tab():
    """バッチ処理結果タブ"""
    
    st.subheader("📊 バッチ処理結果")
    
    # 結果が存在する場合
    if 'batch_results' in st.session_state:
        results = st.session_state.batch_results
        
        # 結果サマリー
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("処理ファイル数", results['total_files'])
        
        with col2:
            st.metric("成功", results['successful_files'])
        
        with col3:
            st.metric("エラー", results['error_files'])
        
        with col4:
            st.metric("処理時間", f"{results['total_time']:.0f}秒")
        
        # 結果詳細
        st.markdown("### 📋 処理結果詳細")
        
        if results.get('file_results'):
            # データフレーム作成
            result_data = []
            for file_result in results['file_results']:
                result_data.append({
                    'ファイル名': Path(file_result['file_path']).name,
                    '状態': '成功' if file_result['success'] else 'エラー',
                    '信頼度': f"{file_result.get('confidence_score', 0):.1%}",
                    '処理時間': f"{file_result.get('processing_time', 0):.1f}秒",
                    'エラー詳細': file_result.get('error', '-')
                })
            
            df = pd.DataFrame(result_data)
            st.dataframe(df, use_container_width=True)
            
            # エクスポートオプション
            st.markdown("### 💾 結果エクスポート")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Excel出力", use_container_width=True):
                    DataExporter.export_to_excel(df, "batch_results.xlsx")
            
            with col2:
                if st.button("📥 CSV出力", use_container_width=True):
                    DataExporter.export_to_csv(df, "batch_results.csv")
            
            with col3:
                if st.button("📥 JSON出力", use_container_width=True):
                    DataExporter.export_to_json(results, "batch_results.json")
        else:
            st.info("詳細な処理結果がありません")
    else:
        st.info("バッチ処理を実行すると結果が表示されます")

def show_batch_statistics_tab():
    """バッチ処理統計タブ"""
    
    st.subheader("📈 処理統計")
    
    try:
        config = st.session_state.config
        if config:
            agent = create_agent_from_config(config)
            stats = agent.get_batch_statistics()
            
            if stats:
                # 基本統計
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("総処理数", stats['total_batches'])
                
                with col2:
                    st.metric("総ファイル数", stats['total_files'])
                
                with col3:
                    success_rate = stats['successful_files'] / stats['total_files'] if stats['total_files'] > 0 else 0
                    st.metric("平均成功率", f"{success_rate:.1%}")
                
                with col4:
                    avg_time = stats['total_processing_time'] / stats['total_files'] if stats['total_files'] > 0 else 0
                    st.metric("平均処理時間", f"{avg_time:.1f}秒/ファイル")
                
                # 時系列チャート
                if 'time_series_data' in stats:
                    st.markdown("### 📊 処理推移")
                    
                    df = pd.DataFrame(stats['time_series_data'])
                    df['date'] = pd.to_datetime(df['date'])
                    
                    StatisticsChart.show_time_series(
                        df,
                        'date',
                        'processed_files',
                        "日別処理ファイル数"
                    )
                
                # 処理時間分布
                if 'processing_times' in stats:
                    st.markdown("### 📊 処理時間分布")
                    
                    StatisticsChart.show_distribution(
                        stats['processing_times'],
                        "処理時間分布"
                    )
                
                # エラー分析
                if 'error_types' in stats:
                    st.markdown("### 📊 エラー分析")
                    
                    error_data = stats['error_types']
                    StatisticsChart.show_comparison(
                        list(error_data.keys()),
                        list(error_data.values()),
                        "エラータイプ別発生数"
                    )
            else:
                st.info("統計データがありません")
    except Exception as e:
        st.error(f"統計取得エラー: {e}")

def execute_batch_processing(input_directory: str, output_directory: str, options: dict):
    """バッチ処理を実行"""
    
    try:
        # 設定確認
        config = st.session_state.config
        if not config:
            raise ValueError("システム設定が読み込まれていません")
        
        api_key = config.get('openai.api_key')
        if not api_key or api_key == 'your-openai-api-key-here':
            raise ValueError("OpenAI APIキーが設定されていません。設定ページで設定してください。")
        
        # 入力ディレクトリ確認
        input_path = Path(input_directory)
        if not input_path.exists():
            raise ValueError(f"入力ディレクトリが存在しません: {input_directory}")
        
        # 出力ディレクトリ作成
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # バッチ処理開始
        st.session_state.batch_processing = True
        st.session_state.batch_progress = {
            'total_files': 0,
            'processed_files': 0,
            'successful': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # バッチプロセッサ初期化
        processor = BatchProcessor(
            agent=create_agent_from_config(config),
            batch_size=options['batch_size'],
            max_workers=options['max_workers'],
            timeout_minutes=options['timeout_minutes'],
            retry_attempts=options['retry_attempts']
        )
        
        # 処理実行
        results = processor.process_directory(
            input_directory=input_directory,
            output_directory=output_directory,
            auto_product_type=options['auto_product_type'],
            default_product_type=options['default_product_type'],
            error_handling=options['error_handling'],
            output_formats=options['output_formats'],
            progress_callback=update_progress
        )
        
        # 結果保存
        st.session_state.batch_results = results
        st.session_state.last_batch_result = {
            'total_files': results['total_files'],
            'success_rate': results['successful_files'] / results['total_files'] if results['total_files'] > 0 else 0,
            'total_time': results['total_time'],
            'errors': [
                {'file': r['file_path'], 'error': r['error']}
                for r in results.get('file_results', [])
                if not r['success']
            ]
        }
        
        # 処理完了
        st.session_state.batch_processing = False
        NotificationManager.show_success("バッチ処理が完了しました")
        
        # 結果タブに切り替え
        st.session_state.active_batch_tab = "📊 処理結果"
        st.rerun()
        
    except Exception as e:
        st.session_state.batch_processing = False
        NotificationManager.show_error(f"バッチ処理エラー: {e}")

def update_progress(progress_info: dict):
    """進捗情報を更新"""
    
    st.session_state.batch_progress.update(progress_info)
