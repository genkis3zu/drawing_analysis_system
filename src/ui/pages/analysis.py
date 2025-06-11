# src/ui/pages/analysis.py

import streamlit as st
import tempfile
import time
import json
from pathlib import Path
from datetime import datetime
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.core.agent import create_agent_from_config
from src.utils.image_processor import A4ImageProcessor
from src.utils.excel_manager import ExcelManager
from src.models.drawing import DrawingAnalysisRequest, ProductType, create_drawing_info_from_file
from src.ui.components import (
    FileUploader, ProgressTracker, ResultsDisplay, 
    ImagePreview, DataExporter, NotificationManager, SettingsPanel
)

def show_analysis_page():
    """図面解析ページを表示"""
    
    st.title("🔍 図面解析")
    st.markdown("A4図面をアップロードして、自動的にデータを抽出します。")
    
    # タブ構成
    tab1, tab2, tab3 = st.tabs(["📄 単一図面解析", "📊 解析結果", "⚙️ 解析設定"])
    
    with tab1:
        show_single_analysis_tab()
    
    with tab2:
        show_results_tab()
    
    with tab3:
        show_settings_tab()

def show_single_analysis_tab():
    """単一図面解析タブ"""
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📁 図面ファイル選択")
        
        # ファイルアップロード
        uploaded_file = FileUploader.show_uploader(
            label="A4図面ファイル",
            accept_multiple=False,
            file_types=['jpg', 'jpeg', 'png', 'pdf'],
            help="A4サイズの図面ファイルをアップロード（PNG, PDF推奨）",
            key="analysis_file_uploader"
        )
        
        # グローバルファイルがある場合は使用
        if not uploaded_file and st.session_state.get('uploaded_file'):
            uploaded_file = st.session_state.uploaded_file
            st.info("📄 サイドバーで選択されたファイルを使用")
        
        # 製品タイプ選択
        st.subheader("🏷️ 製品タイプ")
        product_type_options = {
            "機械部品": ProductType.MECHANICAL_PART,
            "電気部品": ProductType.ELECTRICAL_COMPONENT,
            "組立図": ProductType.ASSEMBLY_DRAWING,
            "配線図": ProductType.WIRING_DIAGRAM,
            "その他": ProductType.OTHER
        }
        
        selected_product_type_name = st.selectbox(
            "製品タイプを選択:",
            list(product_type_options.keys()),
            help="適切な製品タイプを選択すると解析精度が向上します"
        )
        selected_product_type = product_type_options[selected_product_type_name]
        
        # 解析オプション
        st.subheader("🔧 解析オプション")
        
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            use_template = st.checkbox(
                "既存テンプレートを使用",
                value=True,
                help="類似した図面のテンプレートがある場合に使用"
            )
            
            high_precision = st.checkbox(
                "高精度モード",
                value=False,
                help="処理時間は長くなりますが、より正確な解析を行います"
            )
        
        with col_opt2:
            extract_dimensions = st.checkbox(
                "寸法抽出",
                value=True,
                help="図面から寸法情報を抽出"
            )
            
            extract_materials = st.checkbox(
                "材質抽出",
                value=True,
                help="材質・仕様情報を抽出"
            )
        
        # 対象フィールド設定
        with st.expander("🎯 抽出対象フィールド", expanded=False):
            default_fields = [
                "部品番号", "製品名", "材質", "寸法", "重量",
                "表面処理", "精度", "図面番号", "作成者", "作成日"
            ]
            
            selected_fields = st.multiselect(
                "抽出するフィールドを選択:",
                default_fields,
                default=["部品番号", "材質", "寸法"],
                help="空の場合は全フィールドを対象とします"
            )
        
        # 解析実行ボタン
        st.markdown("---")
        
        if st.button("🚀 解析開始", type="primary", use_container_width=True):
            if uploaded_file:
                execute_analysis(
                    uploaded_file,
                    selected_product_type,
                    {
                        'use_template': use_template,
                        'high_precision_mode': high_precision,
                        'extract_dimensions': extract_dimensions,
                        'extract_materials': extract_materials,
                        'target_fields': selected_fields
                    }
                )
            else:
                NotificationManager.show_error("図面ファイルを選択してください")
    
    with col2:
        st.subheader("👁️ プレビュー・解析状況")
        
        # ファイルプレビュー
        if uploaded_file or st.session_state.get('uploaded_file'):
            display_file = uploaded_file or st.session_state.uploaded_file
            ImagePreview.show_image_preview(display_file, show_analysis_info=True)
        
        # 処理状況表示
        if st.session_state.get('processing_status') == '処理中':
            show_processing_status()
        
        # 最近の解析履歴
        show_recent_history()

def show_processing_status():
    """処理状況を表示"""
    
    st.markdown("### ⏳ 処理状況")
    
    # 処理ステップ
    steps = [
        "ファイル前処理",
        "A4画像最適化",
        "AI解析実行",
        "結果検証",
        "データ構造化"
    ]
    
    current_step = st.session_state.get('current_processing_step', 0)
    
    ProgressTracker.show_progress(steps, current_step)
    
    # 処理時間表示
    if 'processing_start_time' in st.session_state:
        elapsed = time.time() - st.session_state.processing_start_time
        st.metric("経過時間", f"{elapsed:.1f}秒")

def show_recent_history():
    """最近の解析履歴を表示"""
    
    with st.expander("📝 最近の解析履歴", expanded=False):
        try:
            config = st.session_state.config
            if config:
                from src.core.agent import DrawingAnalysisAgent
                agent = create_agent_from_config(config)
                history = agent.get_analysis_history(limit=5)
                
                if history:
                    for item in history:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            filename = Path(item['drawing_path']).name
                            st.text(f"📄 {filename}")
                        
                        with col2:
                            confidence = item.get('confidence_score', 0)
                            st.text(f"信頼度: {confidence:.1%}")
                        
                        with col3:
                            created_at = item.get('created_at', '')
                            if created_at:
                                dt = datetime.fromisoformat(created_at)
                                st.text(dt.strftime("%m/%d %H:%M"))
                else:
                    st.text("履歴がありません")
        except Exception as e:
            st.text(f"履歴取得エラー: {e}")

def execute_analysis(uploaded_file, product_type, options):
    """解析を実行"""
    
    st.session_state.processing_status = '処理中'
    st.session_state.processing_start_time = time.time()
    st.session_state.current_processing_step = 0
    
    try:
        with st.spinner("解析を実行中..."):
            
            # ステップ1: ファイル前処理
            st.session_state.current_processing_step = 1
            
            # 一時ファイル作成
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
            
            # ステップ2: A4画像最適化
            st.session_state.current_processing_step = 2
            
            processor = A4ImageProcessor()
            drawing_info = processor.analyze_a4_drawing(tmp_path)
            
            # A4最適化
            optimized_path = tmp_path
            if not drawing_info.is_valid_a4:
                optimized_path = processor.optimize_a4_drawing(tmp_path)
                NotificationManager.show_warning("非A4サイズのため最適化を実行しました")
            
            # ステップ3: AI解析実行
            st.session_state.current_processing_step = 3
            
            # 解析リクエスト作成
            drawing_info_obj = create_drawing_info_from_file(optimized_path)
            request = DrawingAnalysisRequest(
                drawing_info=drawing_info_obj,
                product_type=product_type,
                target_fields=options.get('target_fields', []),
                use_template=options.get('use_template', True),
                high_precision_mode=options.get('high_precision_mode', False),
                extract_dimensions=options.get('extract_dimensions', True),
                extract_materials=options.get('extract_materials', True)
            )
            
            # エージェント初期化
            config = st.session_state.config
            if not config:
                raise ValueError("システム設定が読み込まれていません")
            
            api_key = config.get('openai.api_key')
            if not api_key or api_key == 'your-openai-api-key-here':
                raise ValueError("OpenAI APIキーが設定されていません。設定ページで設定してください。")
            
            agent = create_agent_from_config(config)
            
            # 解析実行
            results = agent.analyze_drawing(optimized_path, request)
            
            # ステップ4: 結果検証
            st.session_state.current_processing_step = 4
            
            # ステップ5: データ構造化
            st.session_state.current_processing_step = 5