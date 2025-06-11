# src/utils/database.py

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)
        
        # データベースディレクトリ作成
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # テーブル初期化
        self._initialize_tables()
    
    def _initialize_tables(self):
        """テーブルを初期化"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 解析結果テーブル
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drawing_path TEXT NOT NULL,
                    template_id TEXT,
                    product_type TEXT,
                    extracted_data TEXT NOT NULL,
                    confidence_score REAL,
                    processing_time REAL,
                    a4_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # テンプレートテーブル
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    template_id TEXT PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    product_type TEXT NOT NULL,
                    orientation TEXT NOT NULL,
                    fields TEXT NOT NULL,
                    layout_features TEXT,
                    confidence_threshold REAL DEFAULT 0.7,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # 学習データテーブル
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_data (
                    learning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id TEXT,
                    edited_results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES templates (template_id)
                )
                """)
                
                # バッチ処理結果テーブル
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_results (
                    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_files INTEGER NOT NULL,
                    successful_files INTEGER NOT NULL,
                    error_files INTEGER NOT NULL,
                    total_time REAL NOT NULL,
                    file_results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # システムメトリクステーブル
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                conn.commit()
        
        except Exception as e:
            self.logger.error(f"テーブル初期化エラー: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        return sqlite3.connect(self.database_path)
    
    def save_analysis_result(self, result_data: Dict[str, Any]) -> int:
        """解析結果を保存"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO analysis_results (
                    drawing_path, template_id, product_type, extracted_data,
                    confidence_score, processing_time, a4_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    result_data['drawing_path'],
                    result_data['template_id'],
                    result_data['product_type'],
                    json.dumps(result_data['extracted_data']),
                    result_data['confidence_score'],
                    result_data['processing_time'],
                    json.dumps(result_data['a4_info'])
                ))
                
                return cursor.lastrowid
        
        except Exception as e:
            self.logger.error(f"解析結果保存エラー: {e}")
            raise
    
    def save_learning_data(self, learning_data: Dict[str, Any]) -> int:
        """学習データを保存"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO learning_data (template_id, edited_results)
                VALUES (?, ?)
                """, (
                    learning_data['template_id'],
                    json.dumps(learning_data['edited_results'])
                ))
                
                return cursor.lastrowid
        
        except Exception as e:
            self.logger.error(f"学習データ保存エラー: {e}")
            raise
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """テンプレートを取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT template_id, template_name, product_type, orientation,
                       fields, layout_features, confidence_threshold
                FROM templates
                WHERE template_id = ?
                """, (template_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'template_id': row[0],
                        'template_name': row[1],
                        'product_type': row[2],
                        'orientation': row[3],
                        'fields': json.loads(row[4]),
                        'layout_features': json.loads(row[5]) if row[5] else None,
                        'confidence_threshold': row[6]
                    }
                
                return None
        
        except Exception as e:
            self.logger.error(f"テンプレート取得エラー: {e}")
            raise
    
    def get_templates_by_type(self, product_type: Optional[str]) -> List[Dict[str, Any]]:
        """製品タイプ別のテンプレートを取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if product_type:
                    cursor.execute("""
                    SELECT template_id, template_name, product_type, orientation,
                           fields, layout_features, confidence_threshold
                    FROM templates
                    WHERE product_type = ?
                    """, (product_type,))
                else:
                    cursor.execute("""
                    SELECT template_id, template_name, product_type, orientation,
                           fields, layout_features, confidence_threshold
                    FROM templates
                    """)
                
                templates = []
                for row in cursor.fetchall():
                    templates.append({
                        'template_id': row[0],
                        'template_name': row[1],
                        'product_type': row[2],
                        'orientation': row[3],
                        'fields': json.loads(row[4]),
                        'layout_features': json.loads(row[5]) if row[5] else None,
                        'confidence_threshold': row[6]
                    })
                
                return templates
        
        except Exception as e:
            self.logger.error(f"テンプレート取得エラー: {e}")
            raise
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]):
        """テンプレートを更新"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                UPDATE templates
                SET fields = ?,
                    layout_features = ?,
                    confidence_threshold = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE template_id = ?
                """, (
                    json.dumps(template_data['fields']),
                    json.dumps(template_data.get('layout_features')),
                    template_data.get('confidence_threshold', 0.7),
                    template_id
                ))
                
                conn.commit()
        
        except Exception as e:
            self.logger.error(f"テンプレート更新エラー: {e}")
            raise
    
    def get_batch_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """バッチ処理履歴を取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT batch_id, total_files, successful_files, error_files,
                       total_time, file_results, created_at
                FROM batch_results
                ORDER BY created_at DESC
                LIMIT ?
                """, (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'batch_id': row[0],
                        'total_files': row[1],
                        'successful_files': row[2],
                        'error_files': row[3],
                        'total_time': row[4],
                        'file_results': json.loads(row[5]),
                        'created_at': row[6]
                    })
                
                return history
        
        except Exception as e:
            self.logger.error(f"バッチ履歴取得エラー: {e}")
            raise
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """バッチ処理統計を取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 基本統計
                cursor.execute("""
                SELECT COUNT(*) as total_batches,
                       SUM(total_files) as total_files,
                       SUM(successful_files) as successful_files,
                       SUM(error_files) as error_files,
                       SUM(total_time) as total_processing_time,
                       AVG(total_time / total_files) as avg_time_per_file
                FROM batch_results
                """)
                
                row = cursor.fetchone()
                
                return {
                    'total_batches': row[0],
                    'total_files': row[1],
                    'successful_files': row[2],
                    'error_files': row[3],
                    'total_processing_time': row[4],
                    'avg_time_per_file': row[5]
                }
        
        except Exception as e:
            self.logger.error(f"バッチ統計取得エラー: {e}")
            raise
    
    def get_batch_time_series(self, days: int = 30) -> List[Dict[str, Any]]:
        """バッチ処理の時系列データを取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT DATE(created_at) as date,
                       COUNT(*) as batch_count,
                       SUM(total_files) as processed_files,
                       AVG(total_time / total_files) as avg_time_per_file
                FROM batch_results
                WHERE created_at >= DATE('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date
                """, (f'-{days} days',))
                
                time_series = []
                for row in cursor.fetchall():
                    time_series.append({
                        'date': row[0],
                        'batch_count': row[1],
                        'processed_files': row[2],
                        'avg_time_per_file': row[3]
                    })
                
                return time_series
        
        except Exception as e:
            self.logger.error(f"時系列データ取得エラー: {e}")
            raise
    
    def get_processing_time_distribution(self) -> List[float]:
        """処理時間の分布を取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT total_time / total_files as time_per_file
                FROM batch_results
                WHERE total_files > 0
                """)
                
                return [row[0] for row in cursor.fetchall()]
        
        except Exception as e:
            self.logger.error(f"処理時間分布取得エラー: {e}")
            raise
    
    def get_error_type_distribution(self) -> Dict[str, int]:
        """エラータイプの分布を取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT file_results
                FROM batch_results
                WHERE error_files > 0
                """)
                
                error_types = {}
                for row in cursor.fetchall():
                    file_results = json.loads(row[0])
                    for result in file_results:
                        if not result.get('success'):
                            error_type = result.get('error', 'unknown')
                            error_types[error_type] = error_types.get(error_type, 0) + 1
                
                return error_types
        
        except Exception as e:
            self.logger.error(f"エラー分布取得エラー: {e}")
            raise
    
    def record_system_metric(self, metric_type: str, metric_value: float, metadata: Optional[Dict[str, Any]] = None):
        """システムメトリクスを記録"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT INTO system_metrics (metric_type, metric_value, metadata)
                VALUES (?, ?, ?)
                """, (
                    metric_type,
                    metric_value,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
        
        except Exception as e:
            self.logger.error(f"メトリクス記録エラー: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """データベース情報を取得"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # データベースファイルサイズ
                db_path = Path(self.database_path)
                size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
                
                # テーブル別レコード数
                table_counts = {}
                for table in ['analysis_results', 'templates', 'learning_data', 'batch_results', 'system_metrics']:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                
                return {
                    'exists': db_path.exists(),
                    'size_mb': size_mb,
                    'table_counts': table_counts,
                    'last_modified': datetime.fromtimestamp(db_path.stat().st_mtime).isoformat() if db_path.exists() else None
                }
        
        except Exception as e:
            self.logger.error(f"データベース情報取得エラー: {e}")
            raise
    
    def vacuum_database(self):
        """データベースを最適化"""
        
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
        
        except Exception as e:
            self.logger.error(f"データベース最適化エラー: {e}")
            raise
    
    def check_integrity(self) -> bool:
        """データベースの整合性をチェック"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                return result == "ok"
        
        except Exception as e:
            self.logger.error(f"整合性チェックエラー: {e}")
            return False
    
    def update_statistics(self):
        """データベース統計を更新"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("ANALYZE")
                conn.commit()
        
        except Exception as e:
            self.logger.error(f"統計更新エラー: {e}")
            raise
    
    def cleanup_old_data(self, days: int) -> int:
        """古いデータを削除"""
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                DELETE FROM analysis_results
                WHERE created_at < datetime('now', ?)
                """, (f'-{days} days',))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
        
        except Exception as e:
            self.logger.error(f"データクリーンアップエラー: {e}")
            raise
