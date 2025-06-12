# src/ui/components.py

import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import traceback
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

class NotificationManager:
    """通知管理クラス"""
    
    @staticmethod
    def show_success(message: str):
        """成功通知を表示"""
        st.success(message)
    
    @staticmethod
    def show_error(message: str):
        """エラー通知を表示"""
        st.error(message)
    
    @staticmethod
    def show_warning(message: str):
        """警告通知を表示"""
        st.warning(message)
    
    @staticmethod
    def show_info(message: str):
        """情報通知を表示"""
        st.info(message)

class MetricsDisplay:
    """メトリクス表示クラス"""
    
    @staticmethod
    def show_metrics(metrics_data: Dict[str, Any]):
        """メトリクスを表示"""
        
        if not metrics_data:
            st.info("メトリクスデータがありません")
            return
        
        # 基本メトリクス
        col1, col2, col3 = st.columns(3)
        
        with col1:
            confidence = metrics_data.get('confidence_score', 0)
            st.metric("信頼度", f"{confidence:.1%}")
        
        with col2:
            processing_time = metrics_data.get('processing_time', 0)
            st.metric("処理時間", f"{processing_time:.2f}秒")
        
        with col3:
            field_count = len(metrics_data.get('extracted_data', {}))
            st.metric("抽出フィールド", field_count)
        
        # 詳細メトリクス
        if 'processing_metrics' in metrics_data:
            with st.expander("詳細メトリクス", expanded=False):
                proc_metrics = metrics_data['processing_metrics']
                
                st.markdown("### 処理段階別時間")
                
                detail_data = {
                    "前処理": proc_metrics.get('image_preprocessing_time', 0),
                    "AI解析": proc_metrics.get('ai_analysis_time', 0),
                    "後処理": proc_metrics.get('post_processing_time', 0)
                }
                
                # 棒グラフ
                df = pd.DataFrame({
                    '処理段階': list(detail_data.keys()),
                    '処理時間(秒)': list(detail_data.values())
                })
                
                fig = px.bar(
                    df, 
                    x='処理段階', 
                    y='処理時間(秒)',
                    title="処理段階別時間"
                )
                
                st.plotly_chart(fig, use_container_width=True)

class FileUploader:
    """ファイルアップローダークラス"""
    
    @staticmethod
    def upload_drawing(key: str = "drawing_uploader") -> Optional[Tuple[str, bytes]]:
        """図面ファイルをアップロード"""
        
        uploaded_file = st.file_uploader(
            "図面ファイルをアップロード",
            type=['png', 'jpg', 'jpeg', 'pdf', 'tiff'],
            key=key
        )
        
        if uploaded_file is not None:
            # ファイル情報表示
            file_details = {
                "ファイル名": uploaded_file.name,
                "ファイルタイプ": uploaded_file.type,
                "ファイルサイズ": f"{uploaded_file.size / 1024:.1f} KB"
            }
            
            st.json(file_details)
            
            # 画像プレビュー
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, caption="アップロードされた図面", use_column_width=True)
            
            return uploaded_file.name, uploaded_file.getvalue()
        
        return None

class ProgressTracker:
    """進捗トラッカークラス"""
    
    @staticmethod
    def create_progress_bar(total_steps: int) -> Tuple[Any, Any]:
        """進捗バーを作成"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        return progress_bar, status_text
    
    @staticmethod
    def update_progress(progress_bar: Any, status_text: Any, step: int, total_steps: int, message: str):
        """進捗を更新"""
        
        progress = min(step / total_steps, 1.0)
        progress_bar.progress(progress)
        status_text.text(f"{message} ({step}/{total_steps})")

class DataExporter:
    """データエクスポートクラス"""
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, filename: str):
        """Excelにエクスポート"""
        
        # Excelファイル作成
        excel_buffer = pd.ExcelWriter(filename, engine='openpyxl')
        df.to_excel(excel_buffer, index=False, sheet_name='データ')
        excel_buffer.close()
        
        # ダウンロードボタン
        with open(filename, "rb") as f:
            st.download_button(
                label="Excelファイルをダウンロード",
                data=f,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, filename: str):
        """CSVにエクスポート"""
        
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="CSVファイルをダウンロード",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )
    
    @staticmethod
    def export_to_json(data: Dict[str, Any], filename: str):
        """JSONにエクスポート"""
        
        import json
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="JSONファイルをダウンロード",
            data=json_str,
            file_name=filename,
            mime="application/json"
        )

class StatisticsChart:
    """統計チャートクラス"""
    
    @staticmethod
    def show_time_series(df: pd.DataFrame, x_col: str, y_col: str, title: str):
        """時系列チャートを表示"""
        
        fig = px.line(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            markers=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def show_distribution(data: List[float], title: str):
        """分布チャートを表示"""
        
        fig = px.histogram(
            x=data,
            nbins=20,
            title=title
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def show_comparison(labels: List[str], values: List[float], title: str):
        """比較チャートを表示"""
        
        fig = px.bar(
            x=labels,
            y=values,
            title=title
        )
        
        st.plotly_chart(fig, use_container_width=True)

class ErrorLogger:
    """エラーログクラス"""
    
    @staticmethod
    def show_error_log():
        """エラーログを表示"""
        
        with st.expander("🐛 エラーログ", expanded=False):
            # ログファイルパス
            log_file = Path("logs/drawing_analysis.log")
            
            if log_file.exists():
                # 最新のログを表示
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = f.readlines()
                    
                    # 最新の50行を表示
                    recent_logs = logs[-50:] if len(logs) > 50 else logs
                    log_text = "".join(recent_logs)
                    
                    st.code(log_text, language="text")
                    
                    # ダウンロードボタン
                    st.download_button(
                        label="ログファイルをダウンロード",
                        data="\n".join(logs),
                        file_name="drawing_analysis.log",
                        mime="text/plain"
                    )
            else:
                st.info("ログファイルが見つかりません")
    
    @staticmethod
    def capture_exception():
        """例外をキャプチャして表示"""
        
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        if exc_type:
            # エラー情報
            error_details = {
                "エラータイプ": exc_type.__name__,
                "エラーメッセージ": str(exc_value),
                "発生時刻": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # トレースバック
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            with st.expander("🐛 エラー詳細", expanded=True):
                st.error(f"**{error_details['エラータイプ']}**: {error_details['エラーメッセージ']}")
                st.code(tb_str, language="python")
                
                # ログに記録
                logging.error(f"UI例外: {error_details['エラータイプ']} - {error_details['エラーメッセージ']}")
                logging.error(tb_str)
                
                # エラー報告ボタン
                if st.button("エラーを報告"):
                    st.session_state.reported_error = error_details
                    st.success("エラーが報告されました。ありがとうございます。")
            
            return True
        
        return False
