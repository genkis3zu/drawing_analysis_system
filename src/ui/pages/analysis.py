# src/ui/pages/analysis.py

import streamlit as st
import pandas as pd
import time
from pathlib import Path
from datetime import datetime
import sys
import plotly.express as px

from src.core.agent import create_agent_from_config
from src.utils.batch_processor import BatchProcessor
from src.utils.file_handler import FileHandler
from src.utils.excel_manager import ExcelManager
from src.utils.image_processor import A4ImageProcessor
from src.ui.components import NotificationManager, MetricsDisplay

def show():
    st.title("図面解析")
    
    # 初期化
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = '待機中'
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    # ステータス表示
    status_color = {
        '待機中': 'blue',
        '処理中': 'orange',
        '完了': 'green',
        'エラー': 'red'
    }
    
    st.markdown(
        f"<h3 style='color: {status_color.get(st.session_state.processing_status, 'gray')};'>状態: {st.session_state.processing_status}</h3>",
        unsafe_allow_html=True
    )
    
    # ファイルアップロード
    uploaded_file = st.file_uploader("図面ファイルをアップロード", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    if uploaded_file is not None:
        # ファイルプレビュー
        st.image(uploaded_file, caption="アップロードされた図面", use_container_width=True)
        
        # 解析ボタン
        if st.button("解析開始", key="start_analysis"):
            try:
                # 処理中状態に更新
                st.session_state.processing_status = '処理中'
                
                # 一時ファイルに保存
                temp_path = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.{uploaded_file.name.split('.')[-1]}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # プログレスバー
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 解析処理
                try:
                    # 画像処理
                    status_text.text("画像処理中...")
                    progress_bar.progress(20)
                    
                    # 画像処理（A4情報の解析）
                    image_processor = A4ImageProcessor()
                    drawing_info = image_processor.analyze_a4_drawing(temp_path)
                    
                    # 必要に応じて画像を最適化
                    if not drawing_info.is_valid_a4:
                        status_text.text("画像最適化中...")
                        temp_path = image_processor.optimize_a4_drawing(temp_path)
                    
                    # エージェント作成
                    status_text.text("AIエージェント準備中...")
                    progress_bar.progress(40)
                    
                    # システム設定を取得
                    from src.utils.config import SystemConfig
                    config = SystemConfig()
                    agent = create_agent_from_config(config)
                    
                    # 解析実行
                    status_text.text("図面解析中...")
                    progress_bar.progress(60)
                    
                    analysis_result = agent.analyze_drawing(temp_path)
                    
                    # 結果保存
                    status_text.text("結果保存中...")
                    progress_bar.progress(80)
                    
                    # 結果をセッションに保存
                    st.session_state.analysis_results = analysis_result
                    
                    # Excel出力
                    excel_manager = ExcelManager()
                    excel_path = f"analysis_result_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
                    excel_path = excel_manager.create_analysis_report(analysis_result, excel_path)
                    
                    # 完了表示
                    status_text.text("完了")
                    progress_bar.progress(100)
                    
                    # 結果表示
                    st.subheader("解析結果")
                    
                    # メトリクス表示
                    MetricsDisplay.show_metrics(analysis_result.to_dict())
                    
                    # グラフ表示
                    if analysis_result.extracted_data:
                        # 抽出データからデータフレーム作成
                        data = []
                        for field_name, extraction_result in analysis_result.extracted_data.items():
                            data.append({
                                'category': field_name,
                                'confidence': extraction_result.confidence
                            })
                        df = pd.DataFrame(data)
                        fig = px.bar(df, x='category', y='confidence', title='解析信頼度')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # ダウンロードボタン
                    with open(excel_path, "rb") as file:
                        st.download_button(
                            label="解析結果をダウンロード",
                            data=file,
                            file_name=excel_path,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # 処理完了
                    st.session_state.processing_status = '完了'
                    NotificationManager.show_success("解析が完了しました")
                    
                    # 結果タブに切り替え
                    st.session_state.active_tab = "📊 解析結果"
                    st.rerun()
                    
                finally:
                    # 一時ファイルの削除
                    try:
                        Path(temp_path).unlink()
                    except:
                        pass
                    
            except Exception as e:
                st.session_state.processing_status = 'エラー'
                NotificationManager.show_error(f"解析エラー: {e}")
