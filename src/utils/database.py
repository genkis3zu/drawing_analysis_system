# src/utils/database.py

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import shutil

class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = "database/drawing_analysis.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
        # データベースディレクトリ作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # データベース初期化
        self.initialize_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 列名でアクセス可能にする
        return conn
    
    def initialize_database(self):
        """データベースを初期化"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # テンプレートテーブル
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS templates (
                    template_id TEXT PRIMARY KEY,
                    product_type TEXT NOT NULL,
                    orientation TEXT NOT NULL,
                    field_mapping TEXT NOT NULL,  -- JSON形式
                    features TEXT,  -- JSON形式の特徴量
                    confidence_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                ''')
                
                # 解析結果テーブル
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    result_id TEXT PRIMARY KEY,
                    drawing_path TEXT NOT NULL,
                    template_id TEXT,
                    product_type TEXT,
                    extracted_data TEXT NOT NULL,  -- JSON形式
                    confidence_score REAL NOT NULL,
                    processing_time REAL NOT NULL,
                    a4_info TEXT,  -- JSON形式
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (template_id) REFERENCES templates (template_id)
                )
                ''')
                
                # 学習データテーブル
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_data (
                    training_id TEXT PRIMARY KEY,
                    template_id TEXT,
                    drawing_path TEXT NOT NULL,
                    original_results TEXT NOT NULL,  -- JSON形式
                    corrected_data TEXT NOT NULL,  -- JSON形式
                    user_feedback BOOLEAN DEFAULT TRUE,
                    confidence_improvement REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (template_id) REFERENCES templates (template_id)
                )
                ''')
                
                # エクセルマッピングテーブル
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS excel_mappings (
                    mapping_id TEXT PRIMARY KEY,
                    template_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    excel_sheet TEXT NOT NULL,
                    excel_cell TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    validation_rule TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (template_id) REFERENCES templates (template_id)
                )
                ''')
                
                # テンプレート候補テーブル
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS template_candidates (
                    candidate_id TEXT PRIMARY KEY,
                    drawing_path TEXT NOT NULL,
                    product_type TEXT,
                    features TEXT NOT NULL,  -- JSON形式
                    extracted_data TEXT NOT NULL,  -- JSON形式
                    confidence_score REAL NOT NULL,
                    similarity_scores TEXT,  -- JSON形式
                    approved BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL
                )
                ''')
                
                # システムメトリクステーブル
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_id TEXT PRIMARY KEY,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT,  -- JSON形式
                    recorded_at TEXT NOT NULL
                )
                ''')
                
                # インデックス作成
                self._create_indexes(cursor)
                
                conn.commit()
                self.logger.info("データベース初期化完了")
                
        except Exception as e:
            self.logger.error(f"データベース初期化エラー: {e}")
            raise
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """インデックスを作成"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_templates_product_type ON templates(product_type)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_results_created_at ON analysis_results(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_training_data_template_id ON training_data(template_id)",
            "CREATE INDEX IF NOT EXISTS idx_excel_mappings_template_id ON excel_mappings(template_id)",
            "CREATE INDEX IF NOT EXISTS idx_template_candidates_confidence ON template_candidates(confidence_score)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type, recorded_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def save_template(self, template_data: Dict[str, Any]) -> str:
        """テンプレートを保存"""
        try:
            template_id = template_data.get('template_id') or f"tpl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO templates (
                    template_id, product_type, orientation, field_mapping,
                    features, confidence_score, usage_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template_id,
                    template_data.get('product_type', ''),
                    template_data.get('orientation', ''),
                    json.dumps(template_data.get('field_mapping', {}), ensure_ascii=False),
                    json.dumps(template_data.get('features', {}), ensure_ascii=False),
                    template_data.get('confidence_score', 0.0),
                    template_data.get('usage_count', 0),
                    template_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self.logger.info(f"テンプレート保存完了: {template_id}")
                return template_id
                
        except Exception as e:
            self.logger.error(f"テンプレート保存エラー: {e}")
            raise
    
    def get_templates_by_type(self, product_type: str = None) -> List[Dict[str, Any]]:
        """製品タイプ別にテンプレートを取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if product_type:
                    cursor.execute('''
                    SELECT * FROM templates 
                    WHERE product_type = ? 
                    ORDER BY confidence_score DESC, usage_count DESC
                    ''', (product_type,))
                else:
                    cursor.execute('''
                    SELECT * FROM templates 
                    ORDER BY confidence_score DESC, usage_count DESC
                    ''')
                
                templates = []
                for row in cursor.fetchall():
                    template = dict(row)
                    template['field_mapping'] = json.loads(template['field_mapping'])
                    template['features'] = json.loads(template['features']) if template['features'] else {}
                    templates.append(template)
                
                return templates
                
        except Exception as e:
            self.logger.error(f"テンプレート取得エラー: {e}")
            return []
    
    def save_analysis_result(self, result_data: Dict[str, Any]) -> str:
        """解析結果を保存"""
        try:
            result_id = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO analysis_results (
                    result_id, drawing_path, template_id, product_type,
                    extracted_data, confidence_score, processing_time,
                    a4_info, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result_id,
                    result_data.get('drawing_path', ''),
                    result_data.get('template_id'),
                    result_data.get('product_type', ''),
                    json.dumps(result_data.get('extracted_data', {}), ensure_ascii=False),
                    result_data.get('confidence_score', 0.0),
                    result_data.get('processing_time', 0.0),
                    json.dumps(result_data.get('a4_info', {}), ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                
                # テンプレート使用回数を更新
                if result_data.get('template_id'):
                    cursor.execute('''
                    UPDATE templates 
                    SET usage_count = usage_count + 1,
                        updated_at = ?
                    WHERE template_id = ?
                    ''', (datetime.now().isoformat(), result_data['template_id']))
                
                conn.commit()
                self.logger.info(f"解析結果保存完了: {result_id}")
                return result_id
                
        except Exception as e:
            self.logger.error(f"解析結果保存エラー: {e}")
            raise
    
    def save_training_data(self, training_data: Dict[str, Any]) -> str:
        """学習データを保存"""
        try:
            training_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO training_data (
                    training_id, template_id, drawing_path, original_results,
                    corrected_data, user_feedback, confidence_improvement, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    training_id,
                    training_data.get('template_id'),
                    training_data.get('drawing_path', ''),
                    json.dumps(training_data.get('original_results', {}), ensure_ascii=False),
                    json.dumps(training_data.get('corrected_data', {}), ensure_ascii=False),
                    training_data.get('user_feedback', True),
                    training_data.get('confidence_improvement', 0.0),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self.logger.info(f"学習データ保存完了: {training_id}")
                return training_id
                
        except Exception as e:
            self.logger.error(f"学習データ保存エラー: {e}")
            raise
    
    def save_template_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """テンプレート候補を保存"""
        try:
            candidate_id = f"cand_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO template_candidates (
                    candidate_id, drawing_path, product_type, features,
                    extracted_data, confidence_score, similarity_scores,
                    approved, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    candidate_id,
                    candidate_data.get('drawing_path', ''),
                    candidate_data.get('product_type', ''),
                    json.dumps(candidate_data.get('features', {}), ensure_ascii=False),
                    json.dumps(candidate_data.get('extracted_data', {}), ensure_ascii=False),
                    candidate_data.get('confidence_score', 0.0),
                    json.dumps(candidate_data.get('similarity_scores', {}), ensure_ascii=False),
                    False,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self.logger.info(f"テンプレート候補保存完了: {candidate_id}")
                return candidate_id
                
        except Exception as e:
            self.logger.error(f"テンプレート候補保存エラー: {e}")
            raise
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """解析統計を取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 総解析数
                cursor.execute("SELECT COUNT(*) FROM analysis_results")
                stats['total_analyses'] = cursor.fetchone()[0]
                
                # 今日の解析数
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE created_at >= ? AND created_at < ?
                """, (today, today + ' 23:59:59'))
                stats['today_analyses'] = cursor.fetchone()[0]
                
                # 平均信頼度
                cursor.execute("SELECT AVG(confidence_score) FROM analysis_results")
                avg_confidence = cursor.fetchone()[0]
                stats['average_confidence'] = round(avg_confidence, 3) if avg_confidence else 0.0
                
                # 製品タイプ別統計
                cursor.execute("""
                SELECT product_type, COUNT(*), AVG(confidence_score)
                FROM analysis_results 
                GROUP BY product_type
                ORDER BY COUNT(*) DESC
                """)
                stats['by_product_type'] = [
                    {
                        'product_type': row[0],
                        'count': row[1],
                        'avg_confidence': round(row[2], 3) if row[2] else 0.0
                    }
                    for row in cursor.fetchall()
                ]
                
                # テンプレート使用統計
                cursor.execute("""
                SELECT t.template_id, t.product_type, t.usage_count, t.confidence_score
                FROM templates t
                ORDER BY t.usage_count DESC
                LIMIT 10
                """)
                stats['top_templates'] = [
                    {
                        'template_id': row[0],
                        'product_type': row[1],
                        'usage_count': row[2],
                        'confidence_score': round(row[3], 3)
                    }
                    for row in cursor.fetchall()
                ]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"統計取得エラー: {e}")
            return {}
    
    def save_excel_mapping(self, mapping_data: Dict[str, Any]) -> str:
        """エクセルマッピングを保存"""
        try:
            mapping_id = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO excel_mappings (
                    mapping_id, template_id, field_name, excel_sheet,
                    excel_cell, data_type, validation_rule, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mapping_id,
                    mapping_data.get('template_id'),
                    mapping_data.get('field_name'),
                    mapping_data.get('excel_sheet'),
                    mapping_data.get('excel_cell'),
                    mapping_data.get('data_type', 'text'),
                    mapping_data.get('validation_rule'),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return mapping_id
                
        except Exception as e:
            self.logger.error(f"エクセルマッピング保存エラー: {e}")
            raise
    
    def get_excel_mappings(self, template_id: str) -> List[Dict[str, Any]]:
        """テンプレートのエクセルマッピングを取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM excel_mappings 
                WHERE template_id = ?
                ORDER BY field_name
                ''', (template_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"エクセルマッピング取得エラー: {e}")
            return []
    
    def record_system_metric(self, metric_type: str, metric_value: float, metadata: Dict = None):
        """システムメトリクスを記録"""
        try:
            metric_id = f"metric_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO system_metrics (
                    metric_id, metric_type, metric_value, metadata, recorded_at
                ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    metric_id,
                    metric_type,
                    metric_value,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"メトリクス記録エラー: {e}")
    
    def get_recent_training_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """最近の学習データを取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now().timestamp() - (days * 24 * 3600))
                cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
                
                cursor.execute('''
                SELECT * FROM training_data 
                WHERE created_at >= ?
                ORDER BY created_at DESC
                ''', (cutoff_iso,))
                
                training_data = []
                for row in cursor.fetchall():
                    data = dict(row)
                    data['original_results'] = json.loads(data['original_results'])
                    data['corrected_data'] = json.loads(data['corrected_data'])
                    training_data.append(data)
                
                return training_data
                
        except Exception as e:
            self.logger.error(f"学習データ取得エラー: {e}")
            return []
    
    def backup_database(self, backup_path: str = None) -> str:
        """データベースをバックアップ"""
        try:
            if backup_path is None:
                backup_dir = self.db_path.parent / "backups"
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"drawing_analysis_backup_{timestamp}.db"
            
            # データベースファイルをコピー
            shutil.copy2(self.db_path, backup_path)
            
            self.logger.info(f"データベースバックアップ完了: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"データベースバックアップエラー: {e}")
            raise
    
    def cleanup_old_data(self, days: int = 30):
        """古いデータをクリーンアップ"""
        try:
            cutoff_date = (datetime.now().timestamp() - (days * 24 * 3600))
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 古いシステムメトリクスを削除
                cursor.execute('''
                DELETE FROM system_metrics 
                WHERE recorded_at < ?
                ''', (cutoff_iso,))
                
                deleted_metrics = cursor.rowcount
                
                # 承認されていない古いテンプレート候補を削除
                cursor.execute('''
                DELETE FROM template_candidates 
                WHERE approved = FALSE AND created_at < ?
                ''', (cutoff_iso,))
                
                deleted_candidates = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(f"データクリーンアップ完了: メトリクス{deleted_metrics}件, 候補{deleted_candidates}件削除")
                
        except Exception as e:
            self.logger.error(f"データクリーンアップエラー: {e}")
    
    def vacuum_database(self):
        """データベースを最適化"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            
            self.logger.info("データベース最適化完了")
            
        except Exception as e:
            self.logger.error(f"データベース最適化エラー: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """データベース情報を取得"""
        try:
            info = {
                'path': str(self.db_path),
                'size_mb': self.db_path.stat().st_size / (1024 * 1024),
                'exists': self.db_path.exists()
            }
            
            if info['exists']:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # テーブル数と行数
                    tables = ['templates', 'analysis_results', 'training_data', 
                             'excel_mappings', 'template_candidates', 'system_metrics']
                    
                    table_info = {}
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        table_info[table] = cursor.fetchone()[0]
                    
                    info['table_counts'] = table_info
            
            return info
            
        except Exception as e:
            self.logger.error(f"データベース情報取得エラー: {e}")
            return {'error': str(e)}
    
    def check_integrity(self) -> bool:
        """データベース整合性をチェック"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                
                if result == "ok":
                    self.logger.info("データベース整合性チェック: OK")
                    return True
                else:
                    self.logger.error(f"データベース整合性エラー: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"整合性チェックエラー: {e}")
            return False
    
    def close(self):
        """データベース接続を閉じる"""
        # SQLite3では明示的な接続クローズは不要（with文で自動管理）
        self.logger.info("データベースマネージャー終了")