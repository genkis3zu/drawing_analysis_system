# src/ui/pages/templates.py

import streamlit as st
import pandas as pd
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import plotly.express as px
import json

from src.utils.config import SystemConfig
from src.utils.database import DatabaseManager
from src.models.template import DrawingTemplate
from src.ui.components import NotificationManager, MetricsDisplay

def show():
    """テンプレート管理ページを表示"""
    
    st.title("テンプレート管理")
    
    # 初期化
    if 'template_action' not in st.session_state:
        st.session_state.template_action = 'list'  # list, create, edit, view
    
    if 'current_template_id' not in st.session_state:
        st.session_state.current_template_id = None
    
    if 'template_filter' not in st.session_state:
        st.session_state.template_filter = 'all'
    
    # データベース接続
    config = SystemConfig()
    db_manager = DatabaseManager(config.get('database.path'))
    
    # タブ
    tab1, tab2, tab3 = st.tabs(["📋 テンプレート一覧", "➕ 新規作成", "📊 統計"])
    
    with tab1:
        show_template_list(db_manager)
    
    with tab2:
        show_template_creation()
    
    with tab3:
        show_template_statistics(db_manager)

def show_template_list(db_manager: DatabaseManager):
    """テンプレート一覧を表示"""
    
    # フィルター
    product_types = ["すべて"]
    templates_by_type = db_manager.get_templates_by_type(None)
    
    # 製品タイプのリストを作成
    for template in templates_by_type:
        if template['product_type'] not in product_types:
            product_types.append(template['product_type'])
    
    selected_type = st.selectbox(
        "製品タイプでフィルター:",
        product_types,
        index=0
    )
    
    # テンプレート一覧を取得
    if selected_type == "すべて":
        templates = templates_by_type
    else:
        templates = db_manager.get_templates_by_type(selected_type)
    
    if not templates:
        st.info("テンプレートが登録されていません。「新規作成」タブから作成してください。")
        return
    
    # テンプレート一覧表示
    st.subheader(f"テンプレート一覧 ({len(templates)}件)")
    
    # データフレーム用のデータ作成
    template_data = []
    for template in templates:
        template_data.append({
            'ID': template['template_id'],
            'テンプレート名': template['template_name'],
            '製品タイプ': template['product_type'],
            '向き': template['orientation'],
            'フィールド数': len(template['fields']),
            '信頼度閾値': f"{template['confidence_threshold']:.1%}"
        })
    
    if template_data:
        df = pd.DataFrame(template_data)
        st.dataframe(df, use_container_width=True)
        
        # テンプレート選択
        selected_template_id = st.selectbox(
            "詳細表示するテンプレートを選択:",
            [t['ID'] for t in template_data],
            format_func=lambda x: next((t['テンプレート名'] for t in template_data if t['ID'] == x), x)
        )
        
        if selected_template_id:
            st.session_state.current_template_id = selected_template_id
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("詳細表示", use_container_width=True):
                    st.session_state.template_action = 'view'
                    st.rerun()
            
            with col2:
                if st.button("編集", use_container_width=True):
                    st.session_state.template_action = 'edit'
                    st.rerun()
            
            with col3:
                if st.button("削除", use_container_width=True, type="primary", help="このテンプレートを削除します"):
                    if delete_template(db_manager, selected_template_id):
                        st.success("テンプレートを削除しました")
                        st.rerun()
    
    # テンプレート詳細表示
    if st.session_state.template_action == 'view' and st.session_state.current_template_id:
        show_template_details(db_manager, st.session_state.current_template_id)
    
    # テンプレート編集
    elif st.session_state.template_action == 'edit' and st.session_state.current_template_id:
        edit_template(db_manager, st.session_state.current_template_id)

def show_template_creation():
    """テンプレート作成フォームを表示"""
    
    st.subheader("新規テンプレート作成")
    
    with st.form("template_creation_form"):
        template_name = st.text_input("テンプレート名", placeholder="例: 機械部品A4図面")
        product_type = st.text_input("製品タイプ", placeholder="例: 機械部品")
        
        orientation = st.selectbox(
            "図面の向き",
            ["縦向き", "横向き"],
            index=0
        )
        
        confidence_threshold = st.slider(
            "信頼度閾値",
            min_value=0.5,
            max_value=0.95,
            value=0.7,
            step=0.05,
            format="%.1f",
            help="この値以上の信頼度を持つフィールドのみが抽出されます"
        )
        
        # フィールド定義
        st.subheader("抽出フィールド定義")
        
        field_count = st.number_input("フィールド数", min_value=1, max_value=20, value=5)
        
        fields = []
        for i in range(field_count):
            col1, col2 = st.columns(2)
            
            with col1:
                field_name = st.text_input(f"フィールド名 {i+1}", key=f"field_name_{i}")
            
            with col2:
                field_type = st.selectbox(
                    f"データ型 {i+1}",
                    ["テキスト", "数値", "日付", "選択肢"],
                    key=f"field_type_{i}"
                )
            
            if field_name:
                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'required': True
                })
        
        # 送信ボタン
        submit_button = st.form_submit_button("テンプレートを作成")
        
        if submit_button:
            if not template_name or not product_type or not fields:
                st.error("必須項目を入力してください")
            else:
                # テンプレート作成
                template_id = str(uuid.uuid4())
                
                template_data = {
                    'template_id': template_id,
                    'template_name': template_name,
                    'product_type': product_type,
                    'orientation': orientation,
                    'fields': fields,
                    'confidence_threshold': confidence_threshold
                }
                
                if create_template(template_data):
                    st.success(f"テンプレート「{template_name}」を作成しました")
                    
                    # 一覧に戻る
                    st.session_state.template_action = 'list'
                    st.rerun()

def show_template_details(db_manager: DatabaseManager, template_id: str):
    """テンプレート詳細を表示"""
    
    template = db_manager.get_template(template_id)
    
    if not template:
        st.error("テンプレートが見つかりません")
        return
    
    st.subheader(f"テンプレート詳細: {template['template_name']}")
    
    # 基本情報
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("製品タイプ", template['product_type'])
    
    with col2:
        st.metric("向き", template['orientation'])
    
    with col3:
        st.metric("信頼度閾値", f"{template['confidence_threshold']:.1%}")
    
    # フィールド一覧
    st.subheader("抽出フィールド")
    
    field_data = []
    for field in template['fields']:
        field_data.append({
            'フィールド名': field['name'],
            'データ型': field['type'],
            '必須': "はい" if field.get('required', False) else "いいえ"
        })
    
    if field_data:
        st.dataframe(pd.DataFrame(field_data), use_container_width=True)
    
    # レイアウト特徴
    if template.get('layout_features'):
        st.subheader("レイアウト特徴")
        st.json(template['layout_features'])
    
    # 戻るボタン
    if st.button("一覧に戻る"):
        st.session_state.template_action = 'list'
        st.rerun()

def edit_template(db_manager: DatabaseManager, template_id: str):
    """テンプレート編集フォームを表示"""
    
    template = db_manager.get_template(template_id)
    
    if not template:
        st.error("テンプレートが見つかりません")
        return
    
    st.subheader(f"テンプレート編集: {template['template_name']}")
    
    with st.form("template_edit_form"):
        template_name = st.text_input("テンプレート名", value=template['template_name'])
        product_type = st.text_input("製品タイプ", value=template['product_type'])
        
        orientation = st.selectbox(
            "図面の向き",
            ["縦向き", "横向き"],
            index=0 if template['orientation'] == "縦向き" else 1
        )
        
        confidence_threshold = st.slider(
            "信頼度閾値",
            min_value=0.5,
            max_value=0.95,
            value=float(template['confidence_threshold']),
            step=0.05,
            format="%.1f",
            help="この値以上の信頼度を持つフィールドのみが抽出されます"
        )
        
        # フィールド定義
        st.subheader("抽出フィールド定義")
        
        # 既存フィールド
        existing_fields = template['fields']
        field_count = st.number_input("フィールド数", min_value=1, max_value=20, value=len(existing_fields))
        
        fields = []
        for i in range(field_count):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            # 既存フィールドの値を取得
            existing_field = existing_fields[i] if i < len(existing_fields) else {'name': '', 'type': 'テキスト', 'required': True}
            
            with col1:
                field_name = st.text_input(
                    f"フィールド名 {i+1}", 
                    value=existing_field.get('name', ''),
                    key=f"edit_field_name_{i}"
                )
            
            with col2:
                field_type = st.selectbox(
                    f"データ型 {i+1}",
                    ["テキスト", "数値", "日付", "選択肢"],
                    index=["テキスト", "数値", "日付", "選択肢"].index(existing_field.get('type', 'テキスト')),
                    key=f"edit_field_type_{i}"
                )
            
            with col3:
                field_required = st.checkbox(
                    "必須",
                    value=existing_field.get('required', True),
                    key=f"edit_field_required_{i}"
                )
            
            if field_name:
                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'required': field_required
                })
        
        # 送信ボタン
        submit_button = st.form_submit_button("テンプレートを更新")
        
        if submit_button:
            if not template_name or not product_type or not fields:
                st.error("必須項目を入力してください")
            else:
                # テンプレート更新
                template_data = {
                    'template_name': template_name,
                    'product_type': product_type,
                    'orientation': orientation,
                    'fields': fields,
                    'confidence_threshold': confidence_threshold,
                    'layout_features': template.get('layout_features')
                }
                
                try:
                    db_manager.update_template(template_id, template_data)
                    st.success(f"テンプレート「{template_name}」を更新しました")
                    
                    # 一覧に戻る
                    st.session_state.template_action = 'list'
                    st.rerun()
                except Exception as e:
                    st.error(f"テンプレート更新エラー: {e}")
    
    # 戻るボタン
    if st.button("キャンセル"):
        st.session_state.template_action = 'list'
        st.rerun()

def create_template(template_data: Dict[str, Any]) -> bool:
    """テンプレートを作成"""
    
    try:
        config = SystemConfig()
        db_manager = DatabaseManager(config.get('database.path'))
        
        # テンプレートテーブルに挿入
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO templates (
                template_id, template_name, product_type, orientation,
                fields, confidence_threshold
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template_data['template_id'],
                template_data['template_name'],
                template_data['product_type'],
                template_data['orientation'],
                json.dumps(template_data['fields']),
                template_data['confidence_threshold']
            ))
            
            conn.commit()
        
        return True
    
    except Exception as e:
        st.error(f"テンプレート作成エラー: {e}")
        return False

def delete_template(db_manager: DatabaseManager, template_id: str) -> bool:
    """テンプレートを削除"""
    
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 使用状況確認
            cursor.execute("""
            SELECT COUNT(*) FROM analysis_results
            WHERE template_id = ?
            """, (template_id,))
            
            usage_count = cursor.fetchone()[0]
            
            if usage_count > 0:
                if not st.warning(f"このテンプレートは{usage_count}件の解析で使用されています。削除しますか？"):
                    return False
            
            # 削除実行
            cursor.execute("""
            DELETE FROM templates
            WHERE template_id = ?
            """, (template_id,))
            
            conn.commit()
            
            return True
    
    except Exception as e:
        st.error(f"テンプレート削除エラー: {e}")
        return False

def show_template_statistics(db_manager: DatabaseManager):
    """テンプレート統計を表示"""
    
    st.subheader("テンプレート統計")
    
    try:
        # テンプレート数
        templates = db_manager.get_templates_by_type(None)
        
        if not templates:
            st.info("テンプレートが登録されていません")
            return
        
        # 基本統計
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総テンプレート数", len(templates))
        
        # 製品タイプ別集計
        product_types = {}
        for template in templates:
            product_type = template['product_type']
            product_types[product_type] = product_types.get(product_type, 0) + 1
        
        with col2:
            st.metric("製品タイプ数", len(product_types))
        
        # フィールド数の平均
        total_fields = sum(len(template['fields']) for template in templates)
        avg_fields = total_fields / len(templates) if templates else 0
        
        with col3:
            st.metric("平均フィールド数", f"{avg_fields:.1f}")
        
        # 製品タイプ別グラフ
        if product_types:
            df = pd.DataFrame({
                '製品タイプ': list(product_types.keys()),
                'テンプレート数': list(product_types.values())
            })
            
            fig = px.bar(
                df, 
                x='製品タイプ', 
                y='テンプレート数',
                title="製品タイプ別テンプレート数"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # テンプレート使用状況
        st.subheader("テンプレート使用状況")
        
        # 解析結果からテンプレート使用回数を取得
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT t.template_name, COUNT(a.result_id) as usage_count
            FROM templates t
            LEFT JOIN analysis_results a ON t.template_id = a.template_id
            GROUP BY t.template_id
            ORDER BY usage_count DESC
            """)
            
            usage_data = []
            for row in cursor.fetchall():
                usage_data.append({
                    'テンプレート名': row[0],
                    '使用回数': row[1]
                })
            
            if usage_data:
                usage_df = pd.DataFrame(usage_data)
                st.dataframe(usage_df, use_container_width=True)
                
                # 使用回数グラフ
                fig = px.pie(
                    usage_df, 
                    names='テンプレート名', 
                    values='使用回数',
                    title="テンプレート使用割合"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("テンプレート使用データがありません")
    
    except Exception as e:
        st.error(f"統計取得エラー: {e}")

def import_template():
    """テンプレートをインポート"""
    
    st.subheader("テンプレートインポート")
    
    uploaded_file = st.file_uploader(
        "テンプレートJSONファイル",
        type=['json'],
        help="エクスポートしたテンプレートJSONファイルをアップロード"
    )
    
    if uploaded_file:
        try:
            template_data = json.load(uploaded_file)
            
            # 基本検証
            required_fields = ['template_name', 'product_type', 'orientation', 'fields']
            for field in required_fields:
                if field not in template_data:
                    st.error(f"テンプレートに必須フィールド '{field}' がありません")
                    return
            
            # IDがない場合は新規作成
            if 'template_id' not in template_data:
                template_data['template_id'] = str(uuid.uuid4())
            
            # 信頼度閾値がない場合はデフォルト値
            if 'confidence_threshold' not in template_data:
                template_data['confidence_threshold'] = 0.7
            
            # テンプレート作成
            if create_template(template_data):
                st.success(f"テンプレート「{template_data['template_name']}」をインポートしました")
                
                # 一覧に戻る
                st.session_state.template_action = 'list'
                st.rerun()
        
        except Exception as e:
            st.error(f"テンプレートインポートエラー: {e}")

def export_template(db_manager: DatabaseManager, template_id: str):
    """テンプレートをエクスポート"""
    
    template = db_manager.get_template(template_id)
    
    if not template:
        st.error("テンプレートが見つかりません")
        return
    
    # JSONに変換
    template_json = json.dumps(template, indent=2, ensure_ascii=False)
    
    # ダウンロードボタン
    st.download_button(
        label="テンプレートをエクスポート",
        data=template_json,
        file_name=f"template_{template['template_name']}_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json"
    )
