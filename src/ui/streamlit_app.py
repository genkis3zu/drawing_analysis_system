# src/ui/streamlit_app.py

import streamlit as st
import sys
from pathlib import Path
import logging

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

if __name__ == "__main__":
    main()
