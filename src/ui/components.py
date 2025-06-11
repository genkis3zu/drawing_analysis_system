# src/ui/components.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import base64
from pathlib import Path

class FileUploader:
    """ファイルアップローダーコンポーネント"""
    
    @staticmethod
    def show_uploader(
        label: str = "図面ファイル",
        accept_multiple: bool = False,
        file_types: List[str] = None,
        help_text: str = None,
        key: str = None
    ):
        """ファイルアップローダーを表示"""
        
        if file_types is None:
            file_types = ['jpg', 'jpeg', 'png', 'pdf']
        
        if help_text is None:
            help_text = f"対応形式: {', '.join([f.upper() for f in file_types])}"
        
        uploaded_files = st.file_uploader(
            label,
            type=file_types,
            accept_multiple_files=accept_multiple,
            help=help_text,
            key=key
        )
        
        if uploaded_files:
            if accept_multiple:
                st.success(f"📁 {len(uploaded_files)}個のファイルが選択されました")
                
                # ファイル一覧表示
                with st.expander("📋 ファイル一覧", expanded=False):
                    for i, file in enumerate(uploaded_files, 1):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.text(f"{i}. {file.name}")
                        with col2:
                            st.text(f"{file.size:,} bytes")
                        with col3:
                            st.text(file.type or "不明")
            else:
                st.success(f"📄 ファイル選択: {uploaded_files.name}")
                
                # ファイル情報表示
                file_info = {
                    "ファイル名": uploaded_files.name,
                    "サイズ": f"{uploaded_files.size:,} bytes",
                    "タイプ": uploaded_files.type or "不明"
                }
                
                cols = st.columns(len(file_info))
                for i, (key, value) in enumerate(file_info.items()):
                    with cols[i]:
                        st.metric(key, value)
        
        return uploaded_files

class ProgressTracker:
    """進捗追跡コンポーネント"""
    
    @staticmethod
    def show_progress(steps: List[str], current_step: int, show_details: bool = True):
        """進捗を表示"""
        
        st.subheader("📈 処理進捗")
        
        # 全体の進捗バー
        progress = current_step / len(steps) if steps else 0
        st.progress(progress)
        
        # 進捗率表示
        st.markdown(f"**進捗: {current_step}/{len(steps)} ({progress*100:.0f}%)**")
        
        if show_details:
            # ステップ詳細
            for i, step in enumerate(steps):
                if i < current_step:
                    st.markdown(f"✅ {step}")
                elif i == current_step:
                    st.markdown(f"🔄 {step} **（処理中）**")
                else:
                    st.markdown(f"⏳ {step}")
    
    @staticmethod
    def show_processing_status(status: str, elapsed_time: float = None):
        """処理状況を表示"""
        
        status_colors = {
            '待機中': '🟡',
            '処理中': '🔵',
            '完了': '🟢', 
            'エラー': '🔴',
            '警告': '🟠'
        }
        
        color = status_colors.get(status, '⚪')
        st.markdown(f"**状態:** {color} {status}")
        
        if elapsed_time is not None:
            st.markdown(f"**経過時間:** {elapsed_time:.1f}秒")

class ResultsDisplay:
    """結果表示コンポーネント"""
    
    @staticmethod
    def show_extraction_results(extracted_data: Dict[str, Any], editable: bool = True):
        """抽出結果を表示"""
        
        if not extracted_data:
            st.warning("表示する結果がありません")
            return None
        
        st.subheader("📊 抽出結果")
        
        # データフレーム作成
        data = []
        for field_name, field_data in extracted_data.items():
            data.append({
                'フィールド名': field_name,
                '抽出値': field_data.get('value', ''),
                '信頼度': field_data.get('confidence', 0),
                '位置': str(field_data.get('position', '')),
                '抽出方法': field_data.get('extraction_method', 'AI'),
                'バリデーション': field_data.get('validation_status', 'unknown')
            })
        
        df = pd.DataFrame(data)
        
        if editable:
            # 編集可能なテーブル
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "信頼度": st.column_config.ProgressColumn(
                        "信頼度",
                        help="抽出の信頼度",
                        min_value=0,
                        max_value=1,
                        format="%.0f%%"
                    ),
                    "抽出値": st.column_config.TextColumn(
                        "抽出値",
                        help="抽出されたデータ（編集可能）",
                        max_chars=100
                    ),
                    "バリデーション": st.column_config.SelectboxColumn(
                        "バリデーション",
                        help="データの妥当性",
                        options=['valid', 'invalid', 'warning', 'unknown']
                    )
                }
            )
            
            # 変更検出
            if not df.equals(edited_df):
                st.session_state.results_modified = True
                st.session_state.edited_results = edited_df
                st.info("💡 結果が変更されました。「学習データ追加」で改善に活用できます。")
            
            return edited_df
        else:
            # 読み取り専用テーブル
            st.dataframe(df, use_container_width=True, hide_index=True)
            return df
    
    @staticmethod
    def show_confidence_chart(extracted_data: Dict[str, Any]):
        """信頼度チャートを表示"""
        
        if not extracted_data:
            return
        
        st.subheader("📊 信頼度分析")
        
        # データ準備
        fields = []
        confidences = []
        
        for field_name, field_data in extracted_data.items():
            fields.append(field_name)
            confidences.append(field_data.get('confidence', 0))
        
        # チャート作成
        fig = px.bar(
            x=fields,
            y=confidences,
            title="フィールド別信頼度",
            labels={'x': 'フィールド名', 'y': '信頼度'},
            color=confidences,
            color_continuous_scale=['red', 'yellow', 'green'],
            range_color=[0, 1]
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        
        # 信頼度レベルの横線を追加
        fig.add_hline(y=0.8, line_dash="dash", line_color="green", 
                     annotation_text="高信頼度ライン (80%)")
        fig.add_hline(y=0.6, line_dash="dash", line_color="orange",
                     annotation_text="中信頼度ライン (60%)")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 統計サマリー
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        high_conf_count = sum(1 for c in confidences if c >= 0.8)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均信頼度", f"{avg_confidence:.1%}")
        with col2:
            st.metric("高信頼度フィールド", f"{high_conf_count}/{len(confidences)}")
        with col3:
            st.metric("信頼度スコア", f"{avg_confidence:.2f}")

class MetricsDisplay:
    """メトリクス表示コンポーネント"""
    
    @staticmethod
    def show_metrics(metrics_data: Dict[str, Any]):
        """メトリクスを表示"""
        
        if not metrics_data:
            return
        
        # メトリクス数に応じて列数を調整
        num_metrics = len(metrics_data)
        cols = st.columns(min(num_metrics, 4))
        
        for i, (key, value) in enumerate(metrics_data.items()):
            with cols[i % len(cols)]:
                if isinstance(value, dict):
                    st.metric(
                        label=key,
                        value=value.get('value', 0),
                        delta=value.get('delta', None),
                        help=value.get('help', None)
                    )
                else:
                    st.metric(label=key, value=value)
    
    @staticmethod
    def show_system_status():
        """システム状態メトリクスを表示"""
        
        st.subheader("🖥️ システム状態")
        
        # サンプルメトリクス（実際のデータに置き換え）
        metrics = {
            "データベース": "🟢 正常",
            "API接続": "🟢 正常", 
            "処理キュー": "0件",
            "ディスク使用量": "45%"
        }
        
        cols = st.columns(len(metrics))
        for i, (key, value) in enumerate(metrics.items()):
            with cols[i]:
                st.metric(key, value)

class ImagePreview:
    """画像プレビューコンポーネント"""
    
    @staticmethod
    def show_image_preview(uploaded_file, show_analysis_info: bool = True):
        """画像プレビューを表示"""
        
        if uploaded_file is None:
            st.info("📤 図面ファイルをアップロードしてください")
            return
        
        st.subheader("👁️ 図面プレビュー")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 画像表示
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
            else:
                st.info("📄 PDFファイルがアップロードされました")
                st.text("プレビューは表示できません")
        
        if show_analysis_info:
            with col2:
                st.markdown("### 📋 ファイル情報")
                
                # 基本情報
                st.text(f"ファイル名: {uploaded_file.name}")
                st.text(f"サイズ: {uploaded_file.size / 1024:.1f} KB")
                st.text(f"形式: {uploaded_file.type}")
                
                # 画像の場合は追加情報
                if uploaded_file.type.startswith('image'):
                    import PIL.Image
                    image = PIL.Image.open(uploaded_file)
                    st.text(f"解像度: {image.size[0]}x{image.size[1]}")
                    st.text(f"モード: {image.mode}")
                    if 'dpi' in image.info:
                        st.text(f"DPI: {image.info['dpi']}")

class NotificationManager:
    """通知管理コンポーネント"""
    
    @staticmethod
    def show_success(message: str):
        """成功通知を表示"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def show_error(message: str):
        """エラー通知を表示"""
        st.error(f"❌ {message}")
    
    @staticmethod
    def show_warning(message: str):
        """警告通知を表示"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info(message: str):
        """情報通知を表示"""
        st.info(f"ℹ️ {message}")

class DataExporter:
    """データエクスポートコンポーネント"""
    
    @staticmethod
    def export_to_excel(data: pd.DataFrame, filename: str = "export.xlsx"):
        """Excelファイルとしてエクスポート"""
        
        try:
            # Excel形式に変換
            buffer = pd.ExcelWriter(filename, engine='xlsxwriter')
            data.to_excel(buffer, index=False, sheet_name='Data')
            
            # ダウンロードボタン表示
            st.download_button(
                label="📥 Excelファイルをダウンロード",
                data=buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            NotificationManager.show_success("エクスポート準備完了")
            
        except Exception as e:
            NotificationManager.show_error(f"エクスポートエラー: {e}")
    
    @staticmethod
    def export_to_csv(data: pd.DataFrame, filename: str = "export.csv"):
        """CSVファイルとしてエクスポート"""
        
        try:
            # CSV形式に変換
            csv = data.to_csv(index=False)
            
            # ダウンロードボタン表示
            st.download_button(
                label="📥 CSVファイルをダウンロード",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
            
            NotificationManager.show_success("エクスポート準備完了")
            
        except Exception as e:
            NotificationManager.show_error(f"エクスポートエラー: {e}")
    
    @staticmethod
    def export_to_json(data: Dict[str, Any], filename: str = "export.json"):
        """JSONファイルとしてエクスポート"""
        
        try:
            import json
            
            # JSON形式に変換
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            
            # ダウンロードボタン表示
            st.download_button(
                label="📥 JSONファイルをダウンロード",
                data=json_str,
                file_name=filename,
                mime="application/json"
            )
            
            NotificationManager.show_success("エクスポート準備完了")
            
        except Exception as e:
            NotificationManager.show_error(f"エクスポートエラー: {e}")

class StatisticsChart:
    """統計チャートコンポーネント"""
    
    @staticmethod
    def show_time_series(data: pd.DataFrame, x_col: str, y_col: str, title: str = None):
        """時系列チャートを表示"""
        
        fig = px.line(
            data,
            x=x_col,
            y=y_col,
            title=title
        )
        
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def show_distribution(data: List[float], title: str = None):
        """分布チャートを表示"""
        
        fig = px.histogram(
            x=data,
            title=title,
            nbins=30
        )
        
        fig.update_layout(
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def show_comparison(categories: List[str], values: List[float], title: str = None):
        """比較チャートを表示"""
        
        fig = px.bar(
            x=categories,
            y=values,
            title=title
        )
        
        fig.update_layout(
            xaxis_title="カテゴリ",
            yaxis_title="値",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
