# src/ui/streamlit_app.py

import streamlit as st
import sys
from pathlib import Path
import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import tempfile
from PIL import Image
import io

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.ui.pages import analysis, batch, settings, templates
from src.utils.config import SystemConfig
from src.ui import components
from src.ui.components import ErrorLogger
from src.models.drawing import ProductType

# ページ設定
st.set_page_config(
    page_title="A4図面解析システム",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.company.com/drawing-analysis',
        'Report a bug': 'mailto:support@company.com',
        'About': "A4図面自動解析システム v1.0"
    }
)

# カスタムCSS
st.markdown("""
<style>
/* メインスタイル */
.main-header {
    background: linear-gradient(90deg, #1f77b4, #ff7f0e);
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.main-header h1 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
}

.main-header p {
    margin: 0.5rem 0 0 0;
    font-size: 1.1rem;
    opacity: 0.9;
}

/* メトリクスカード */
.metric-card {
    background: #f8f9fa;
    padding: 1.2rem;
    border-radius: 8px;
    border-left: 4px solid #1f77b4;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* ステータスメッセージ */
.success-message {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 1rem;
    color: #155724;
    margin: 1rem 0;
}

.error-message {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 5px;
    padding: 1rem;
    color: #721c24;
    margin: 1rem 0;
}

.warning-message {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 1rem;
    color: #856404;
    margin: 1rem 0;
}

.info-message {
    background: #d1ecf1;
    border: 1px solid #bee5eb;
    border-radius: 5px;
    padding: 1rem;
    color: #0c5460;
    margin: 1rem 0;
}

/* 図面プレビュー */
.drawing-preview {
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 1rem 0;
}

/* サイドバー */
.sidebar-section {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    border: 1px solid #e9ecef;
}

.sidebar-metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #e9ecef;
}

.sidebar-metric:last-child {
    border-bottom: none;
}

/* ボタンスタイル */
.stButton > button {
    border-radius: 8px;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* データテーブル */
.dataframe {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* プログレスバー */
.stProgress > div > div {
    border-radius: 10px;
}

/* ファイルアップローダー */
.uploadedFile {
    border-radius: 8px;
    border: 2px dashed #1f77b4;
    padding: 2rem;
    text-align: center;
    margin: 1rem 0;
}

/* フッター */
.footer {
    text-align: center;
    color: #666;
    padding: 2rem 0;
    border-top: 1px solid #e9ecef;
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """セッション状態を初期化"""
    
    # 設定
    if 'config' not in st.session_state:
        try:
            st.session_state.config = SystemConfig()
        except Exception as e:
            st.error(f"設定ファイル読み込みエラー: {e}")
            st.session_state.config = None
    
    # 現在のページ
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "図面解析"
    
    # 解析結果
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    # アップロードファイル
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    
    # 処理状況
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = "待機中"
    
    # アラート
    if 'alerts' not in st.session_state:
        st.session_state.alerts = []
    
    # システム統計
    if 'system_stats' not in st.session_state:
        st.session_state.system_stats = {
            'total_analyses': 0,
            'today_analyses': 0,
            'avg_confidence': 0.0,
            'template_count': 0
        }
    
    # UI設定
    if 'ui_settings' not in st.session_state:
        st.session_state.ui_settings = {
            'show_tips': True,
            'auto_save': True,
            'theme': 'light'
        }

def show_header():
    """ヘッダーを表示"""
    
    st.markdown("""
    <div class="main-header">
        <h1>📐 A4図面解析システム</h1>
        <p>OpenAI GPT-4 Visionを使用したA4図面の自動データ抽出・エクセル出力システム</p>
    </div>
    """, unsafe_allow_html=True)
    
    # アラート表示
    if st.session_state.alerts:
        for alert in st.session_state.alerts:
            if alert['type'] == 'success':
                st.success(alert['message'])
            elif alert['type'] == 'error':
                st.error(alert['message'])
            elif alert['type'] == 'warning':
                st.warning(alert['message'])
            elif alert['type'] == 'info':
                st.info(alert['message'])
        
        # アラートをクリア
        st.session_state.alerts = []

def show_sidebar():
    """サイドバーを表示"""
    
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-section">
            <h3>📂 ナビゲーション</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # ページ選択
        pages = {
            "図面解析": "🔍",
            "テンプレート管理": "📋", 
            "バッチ処理": "🔄",
            "システム設定": "⚙️"
        }
        
        selected_page = st.selectbox(
            "ページを選択:",
            list(pages.keys()),
            index=list(pages.keys()).index(st.session_state.current_page),
            format_func=lambda x: f"{pages[x]} {x}"
        )
        
        st.markdown("---")
        
        # システム状態
        st.markdown("""
        <div class="sidebar-section">
            <h4>📊 システム状態</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # 処理状況
        status_color = {
            '待機中': '🟡',
            '処理中': '🔵', 
            '完了': '🟢',
            'エラー': '🔴'
        }.get(st.session_state.processing_status, '⚪')
        
        st.markdown(f"**処理状態:** {status_color} {st.session_state.processing_status}")
        
        # 統計情報
        stats = st.session_state.system_stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("総解析数", stats['total_analyses'])
            st.metric("テンプレート", stats['template_count'])
        
        with col2:
            st.metric("今日の解析", stats['today_analyses'])
            st.metric("平均信頼度", f"{stats['avg_confidence']:.1%}")
        
        st.markdown("---")
        
        # クイックアクション
        st.markdown("""
        <div class="sidebar-section">
            <h4>⚡ クイックアクション</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 新規解析", use_container_width=True):
                st.session_state.current_page = "図面解析"
                st.rerun()
        
        with col2:
            if st.button("📊 統計確認", use_container_width=True):
                show_quick_stats()
        
        # グローバルファイルアップロード
        st.markdown("### 📁 ファイル選択")
        uploaded_file = st.file_uploader(
            "図面ファイル",
            type=['jpg', 'jpeg', 'png', 'pdf'],
            help="A4サイズの図面ファイルをアップロード",
            key="global_file_uploader"
        )
        
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
            st.success(f"📄 {uploaded_file.name}")
        
        st.markdown("---")
        
        # 設定
        if st.checkbox("💡 ヒント表示", value=st.session_state.ui_settings['show_tips']):
            st.session_state.ui_settings['show_tips'] = True
        else:
            st.session_state.ui_settings['show_tips'] = False
        
        return selected_page

def show_quick_stats():
    """クイック統計を表示"""
    
    with st.expander("📈 詳細統計", expanded=True):
        try:
            if st.session_state.config:
                from src.utils.database import DatabaseManager
                db_manager = DatabaseManager(st.session_state.config.get('database.path'))
                stats = db_manager.get_analysis_statistics()
                
                if stats:
                    # 全体統計
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("総解析数", stats.get('total_analyses', 0))
                    with col2:
                        st.metric("今日の解析", stats.get('today_analyses', 0))
                    with col3:
                        st.metric("平均信頼度", f"{stats.get('average_confidence', 0):.1%}")
                    
                    # 製品タイプ別
                    if stats.get('by_product_type'):
                        st.markdown("**製品タイプ別統計:**")
                        for item in stats['by_product_type'][:3]:
                            st.text(f"• {item['product_type']}: {item['count']}件")
                
        except Exception as e:
            st.error(f"統計取得エラー: {e}")

def show_tips():
    """ヒントを表示"""
    
    if not st.session_state.ui_settings.get('show_tips', True):
        return
    
    tips = [
        "💡 **品質向上のコツ**: 図面は300DPI以上、A4サイズで準備すると精度が向上します",
        "🎯 **効率化**: 同じ種類の図面は一度テンプレートを作成すると次回から高速処理できます",
        "📊 **信頼度**: 80%以上の信頼度が理想的です。低い場合は手動修正をお勧めします",
        "🔄 **学習機能**: 修正したデータは自動的に学習され、次回の精度向上に活用されます"
    ]
    
    import random
    tip = random.choice(tips)
    
    st.info(tip)

def show_footer():
    """フッターを表示"""
    
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        <p><strong>A4図面解析システム</strong> v1.0 | © 2024 Your Company</p>
        <p>
            <a href="mailto:support@company.com">📧 サポート</a> | 
            <a href="https://docs.company.com">📚 ドキュメント</a> | 
            <a href="https://github.com/company/drawing-analysis">💻 GitHub</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

def load_system_stats():
    """システム統計を読み込み"""
    
    try:
        if st.session_state.config:
            from src.utils.database import DatabaseManager
            db_manager = DatabaseManager(st.session_state.config.get('database.path'))
            stats = db_manager.get_analysis_statistics()
            
            if stats:
                st.session_state.system_stats.update({
                    'total_analyses': stats.get('total_analyses', 0),
                    'today_analyses': stats.get('today_analyses', 0),
                    'avg_confidence': stats.get('average_confidence', 0.0),
                    'template_count': len(stats.get('top_templates', []))
                })
    
    except Exception as e:
        st.session_state.system_stats = {
            'total_analyses': 0,
            'today_analyses': 0,
            'avg_confidence': 0.0,
            'template_count': 0
        }

def main():
    """メインアプリケーション"""
    
    # セッション状態初期化
    initialize_session_state()
    
    # システム統計読み込み
    load_system_stats()
    
    # ヘッダー表示
    show_header()
    
    # サイドバー
    selected_page = show_sidebar()
    st.session_state.current_page = selected_page
    
    # エラーログ表示
    ErrorLogger.show_error_log()
    
    # メインコンテンツ
    try:
        if selected_page == "図面解析":
            analysis.show()
        elif selected_page == "テンプレート管理":
            templates.show()
        elif selected_page == "バッチ処理":
            batch.show()
        elif selected_page == "システム設定":
            settings.show()
        else:
            st.error(f"不明なページ: {selected_page}")
    
    except Exception as e:
        st.error(f"ページ表示エラー: {str(e)}")
        
        # 例外キャプチャ
        ErrorLogger.capture_exception()
        
        # エラー報告
        if st.button("🐛 エラーを報告"):
            st.info("エラー情報をシステム管理者に送信しました。")
    
    # ヒント表示
    show_tips()
    
    # フッター
    show_footer()

def add_alert(alert_type: str, message: str):
    """アラートを追加"""
    st.session_state.alerts.append({
        'type': alert_type,
        'message': message
    })

# アラート追加のヘルパー関数
def success_alert(message: str):
    add_alert('success', message)

def error_alert(message: str):
    add_alert('error', message)

def warning_alert(message: str):
    add_alert('warning', message)

def info_alert(message: str):
    add_alert('info', message)

# テスト可能なクラスベースのStreamlitアプリコンポーネント

class UIState:
    """UIの状態管理クラス"""
    
    def __init__(self):
        self.current_result: Optional[Any] = None
        self.upload_history: List[str] = []
        self.is_processing: bool = False
    
    def set_current_result(self, result: Any) -> None:
        """現在の解析結果を設定"""
        self.current_result = result
    
    def set_processing_status(self, status: bool) -> None:
        """処理状態を設定"""
        self.is_processing = status
    
    def add_to_history(self, filename: str) -> None:
        """アップロード履歴に追加"""
        self.upload_history.append(filename)


class SessionManager:
    """セッション管理クラス"""
    
    def save_session_data(self, key: str, data: Any) -> None:
        """セッションデータを保存"""
        if hasattr(st, 'session_state'):
            st.session_state[key] = data
    
    def load_session_data(self, key: str) -> Any:
        """セッションデータを読み込み"""
        if hasattr(st, 'session_state') and key in st.session_state:
            return st.session_state[key]
        return None
    
    def initialize_session(self) -> None:
        """セッションを初期化"""
        if hasattr(st, 'session_state'):
            if 'ui_state' not in st.session_state:
                st.session_state.ui_state = UIState()


class StreamlitApp:
    """Streamlitアプリケーションのメインクラス（テスト用）"""
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: アプリケーション設定
        """
        self.upload_dir = Path(config["upload_dir"])
        self.output_dir = Path(config["output_dir"])
        self.max_file_size_mb = config.get("max_file_size_mb", 10)
        self.allowed_extensions = config.get("allowed_extensions", [".png", ".jpg", ".jpeg"])
        self.auto_save = config.get("auto_save", True)
        
        # ディレクトリ作成
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 状態管理
        self.session_manager = SessionManager()
        self.analysis_history: List[Any] = []
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
    
    def validate_uploaded_file(self, uploaded_file) -> Tuple[bool, str]:
        """アップロードファイルの検証
        
        Args:
            uploaded_file: StreamlitのUploadedFileオブジェクト
            
        Returns:
            Tuple[bool, str]: (有効かどうか, メッセージ)
        """
        # 拡張子チェック
        file_extension = Path(uploaded_file.name).suffix.lower()
        if file_extension not in self.allowed_extensions:
            return False, f"サポートされていない拡張子です: {file_extension}"
        
        # サイズチェック
        if uploaded_file.size > self.max_file_size_mb * 1024 * 1024:
            return False, f"ファイルサイズが制限を超えています: {uploaded_file.size / (1024*1024):.1f}MB > {self.max_file_size_mb}MB"
        
        return True, "有効なファイルです"
    
    def analyze_drawing(self, uploaded_file, agent) -> Any:
        """図面解析を実行
        
        Args:
            uploaded_file: アップロードされたファイル
            agent: 解析エージェント
            
        Returns:
            解析結果
        """
        # ファイルを一時保存
        temp_path = self.upload_dir / uploaded_file.name
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        try:
            # 解析実行
            result = agent.analyze_drawing(str(temp_path))
            
            # 履歴に追加
            if self.auto_save:
                self.add_to_history(result)
            
            return result
            
        finally:
            # 一時ファイル削除
            if temp_path.exists():
                temp_path.unlink()
    
    def update_analysis_result(self, result: Any, field_name: str, new_value: str) -> Any:
        """解析結果の更新
        
        Args:
            result: 解析結果
            field_name: フィールド名
            new_value: 新しい値
            
        Returns:
            更新された解析結果
        """
        result.update_field(field_name, new_value, "手動修正")
        return result
    
    def export_to_excel(self, result: Any) -> Path:
        """Excelに出力
        
        Args:
            result: 解析結果
            
        Returns:
            Path: 出力ファイルパス
        """
        from ..utils.excel_manager import ExcelManager
        
        excel_config = {
            "output_dir": str(self.output_dir),
            "template_dir": str(self.output_dir / "templates")
        }
        excel_manager = ExcelManager(excel_config)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"analysis_report_{timestamp}.xlsx"
        
        return excel_manager.export_single_result(result, output_file)
    
    def validate_a4_image(self, image_data: bytes) -> Tuple[bool, str]:
        """A4画像の検証
        
        Args:
            image_data: 画像データ
            
        Returns:
            Tuple[bool, str]: (A4かどうか, メッセージ)
        """
        try:
            return self._check_a4_dimensions(image_data)
        except Exception as e:
            return False, f"画像検証エラー: {e}"
    
    def _check_a4_dimensions(self, image_data: bytes) -> Tuple[bool, str]:
        """A4寸法のチェック（実装はモック用）"""
        # 実際の実装では画像のサイズと解像度をチェック
        return True, "有効なA4サイズです"
    
    def run_batch_processing(self, input_dir: str, agent) -> Optional[Path]:
        """バッチ処理の実行
        
        Args:
            input_dir: 入力ディレクトリ
            agent: 解析エージェント
            
        Returns:
            Optional[Path]: 結果ファイルパス
        """
        from ..utils.batch_processor import BatchProcessor
        
        config = {
            "input_dir": input_dir,
            "output_dir": str(self.output_dir),
            "max_workers": 2
        }
        
        processor = BatchProcessor(config)
        results = processor.process_batch(agent)
        
        if results:
            return processor.save_results(results)
        
        return None
    
    def add_to_history(self, result: Any) -> None:
        """履歴に追加"""
        self.analysis_history.append(result)
    
    def get_analysis_history(self) -> List[Any]:
        """解析履歴を取得"""
        return self.analysis_history
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        """設定を保存"""
        settings_file = self.output_dir / "app_settings.json"
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    
    def load_settings(self) -> Dict[str, Any]:
        """設定を読み込み"""
        settings_file = self.output_dir / "app_settings.json"
        
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # デフォルト設定
        return {
            "confidence_threshold": 0.7,
            "auto_save": True,
            "default_template": "basic"
        }
    
    def update_progress(self, current: int, total: int, message: str) -> None:
        """プログレスバーの更新（Streamlit環境でのみ動作）"""
        if hasattr(st, 'progress'):
            progress_bar = st.progress(0)
            progress_bar.progress(current / total)
            if hasattr(st, 'text'):
                st.text(message)
    
    def compare_results(self, result1: Any, result2: Any) -> Dict[str, Any]:
        """解析結果の比較"""
        from ..models.analysis_result import AnalysisComparison
        
        comparison = AnalysisComparison(result1, result2)
        return comparison.to_dict()
    
    def apply_template(self, result: Any, template_path: str) -> Path:
        """テンプレートを適用"""
        return self._apply_excel_template(result, template_path)
    
    def _apply_excel_template(self, result: Any, template_path: str) -> Path:
        """Excelテンプレートを適用（実装はモック用）"""
        from ..utils.excel_manager import ExcelManager
        
        excel_config = {
            "output_dir": str(self.output_dir),
            "template_dir": str(Path(template_path).parent)
        }
        excel_manager = ExcelManager(excel_config)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"template_result_{timestamp}.xlsx"
        
        return excel_manager.export_with_template(result, Path(template_path), output_file)


if __name__ == "__main__":
    main()
