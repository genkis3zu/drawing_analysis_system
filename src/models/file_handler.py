# src/utils/file_handler.py

import os
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import mimetypes

class FileHandler:
    """ファイル操作管理クラス"""
    
    SUPPORTED_FORMATS = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg', 
        '.png': 'image/png',
        '.pdf': 'application/pdf',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.bmp': 'image/bmp'
    }
    
    def __init__(self, temp_dir: str = "data/temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """ファイルを検証"""
        try:
            file_path = Path(file_path)
            
            validation_result = {
                'is_valid': False,
                'file_exists': file_path.exists(),
                'file_size': 0,
                'file_format': None,
                'mime_type': None,
                'is_supported': False,
                'errors': []
            }
            
            if not file_path.exists():
                validation_result['errors'].append("ファイルが存在しません")
                return validation_result
            
            # ファイルサイズ
            file_size = file_path.stat().st_size
            validation_result['file_size'] = file_size
            
            # サイズチェック（100MB制限）
            if file_size > 100 * 1024 * 1024:
                validation_result['errors'].append("ファイルサイズが大きすぎます（100MB制限）")
            
            if file_size == 0:
                validation_result['errors'].append("ファイルが空です")
            
            # 拡張子チェック
            file_extension = file_path.suffix.lower()
            validation_result['file_format'] = file_extension
            
            if file_extension in self.SUPPORTED_FORMATS:
                validation_result['is_supported'] = True
                validation_result['mime_type'] = self.SUPPORTED_FORMATS[file_extension]
            else:
                validation_result['errors'].append(f"サポートされていないファイル形式: {file_extension}")
            
            # MIMEタイプ検証
            detected_mime, _ = mimetypes.guess_type(str(file_path))
            if detected_mime and detected_mime != validation_result['mime_type']:
                validation_result['errors'].append("ファイル拡張子とMIMEタイプが一致しません")
            
            # 全体の検証結果
            validation_result['is_valid'] = (
                validation_result['file_exists'] and 
                validation_result['is_supported'] and 
                len(validation_result['errors']) == 0
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"ファイル検証エラー: {e}")
            return {
                'is_valid': False,
                'errors': [f"検証エラー: {str(e)}"]
            }
    
    def create_temp_file(self, original_path: str, prefix: str = "drawing_") -> str:
        """一時ファイルを作成"""
        try:
            original_path = Path(original_path)
            
            # ハッシュ値を含む一意なファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = self._calculate_file_hash(original_path)[:8]
            
            temp_filename = f"{prefix}{timestamp}_{file_hash}{original_path.suffix}"
            temp_path = self.temp_dir / temp_filename
            
            # ファイルをコピー
            shutil.copy2(original_path, temp_path)
            
            self.logger.info(f"一時ファイル作成: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            self.logger.error(f"一時ファイル作成エラー: {e}")
            raise
    
    def save_uploaded_file(self, uploaded_file, target_dir: str) -> str:
        """アップロードファイルを保存"""
        try:
            target_dir = Path(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名の安全化
            safe_filename = self._sanitize_filename(uploaded_file.name)
            
            # 重複回避のためタイムスタンプ追加
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = Path(safe_filename)
            final_filename = f"{name_parts.stem}_{timestamp}{name_parts.suffix}"
            
            target_path = target_dir / final_filename
            
            # ファイル保存
            with open(target_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            self.logger.info(f"ファイル保存完了: {target_path}")
            return str(target_path)
            
        except Exception as e:
            self.logger.error(f"ファイル保存エラー: {e}")
            raise
    
    def organize_files_by_date(self, source_dir: str, target_dir: str):
        """ファイルを日付別に整理"""
        try:
            source_dir = Path(source_dir)
            target_dir = Path(target_dir)
            
            if not source_dir.exists():
                self.logger.warning(f"ソースディレクトリが存在しません: {source_dir}")
                return
            
            moved_count = 0
            
            for file_path in source_dir.iterdir():
                if file_path.is_file():
                    # ファイルの更新日時を取得
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    date_str = mtime.strftime("%Y%m%d")
                    
                    # 日付別ディレクトリ作成
                    date_dir = target_dir / date_str
                    date_dir.mkdir(parents=True, exist_ok=True)
                    
                    # ファイル移動
                    target_path = date_dir / file_path.name
                    
                    # 重複チェック
                    if target_path.exists():
                        counter = 1
                        while target_path.exists():
                            name_parts = Path(file_path.name)
                            new_name = f"{name_parts.stem}_{counter}{name_parts.suffix}"
                            target_path = date_dir / new_name
                            counter += 1
                    
                    shutil.move(str(file_path), str(target_path))
                    moved_count += 1
            
            self.logger.info(f"ファイル整理完了: {moved_count}ファイルを移動")
            
        except Exception as e:
            self.logger.error(f"ファイル整理エラー: {e}")
            raise
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """古い一時ファイルを削除"""
        try:
            current_time = datetime.now().timestamp()
            cutoff_time = current_time - (max_age_hours * 3600)
            
            deleted_count = 0
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_mtime = file_path.stat().st_mtime
                    
                    if file_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            self.logger.info(f"一時ファイルクリーンアップ完了: {deleted_count}ファイル削除")
            
        except Exception as e:
            self.logger.error(f"一時ファイルクリーンアップエラー: {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """ファイル情報を取得"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'error': 'ファイルが存在しません'}
            
            stat = file_path.stat()
            
            return {
                'name': file_path.name,
                'path': str(file_path.absolute()),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': file_path.suffix.lower(),
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'hash_md5': self._calculate_file_hash(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"ファイル情報取得エラー: {e}")
            return {'error': str(e)}
    
    def find_files_by_pattern(self, directory: str, pattern: str) -> List[str]:
        """パターンでファイルを検索"""
        try:
            directory = Path(directory)
            
            if not directory.exists():
                return []
            
            matching_files = []
            
            for file_path in directory.rglob(pattern):
                if file_path.is_file():
                    matching_files.append(str(file_path))
            
            return sorted(matching_files)
            
        except Exception as e:
            self.logger.error(f"ファイル検索エラー: {e}")
            return []
    
    def batch_validate_files(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """複数ファイルの一括検証"""
        try:
            results = {}
            
            for file_path in file_paths:
                results[file_path] = self.validate_file(file_path)
            
            return results
            
        except Exception as e:
            self.logger.error(f"一括ファイル検証エラー: {e}")
            return {}
    
    def create_directory_structure(self, base_dir: str, structure: Dict[str, Any]):
        """ディレクトリ構造を作成"""
        try:
            base_path = Path(base_dir)
            
            def create_recursive(current_path: Path, struct: Dict):
                for name, content in struct.items():
                    new_path = current_path / name
                    
                    if isinstance(content, dict):
                        new_path.mkdir(parents=True, exist_ok=True)
                        create_recursive(new_path, content)
                    else:
                        new_path.mkdir(parents=True, exist_ok=True)
            
            create_recursive(base_path, structure)
            self.logger.info(f"ディレクトリ構造作成完了: {base_dir}")
            
        except Exception as e:
            self.logger.error(f"ディレクトリ構造作成エラー: {e}")
            raise
    
    def get_directory_size(self, directory: str) -> Dict[str, Any]:
        """ディレクトリサイズを取得"""
        try:
            directory = Path(directory)
            
            if not directory.exists():
                return {'error': 'ディレクトリが存在しません'}
            
            total_size = 0
            file_count = 0
            
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'directory': str(directory.absolute())
            }
            
        except Exception as e:
            self.logger.error(f"ディレクトリサイズ取得エラー: {e}")
            return {'error': str(e)}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのMD5ハッシュを計算"""
        try:
            hash_md5 = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            return hash_md5.hexdigest()
            
        except Exception as e:
            self.logger.error(f"ハッシュ計算エラー: {e}")
            return ""
    
    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名を安全化"""
        import re
        
        # 危険な文字を除去
        safe_chars = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # 連続するアンダースコアを一つに
        safe_chars = re.sub(r'_+', '_', safe_chars)
        
        # 長すぎるファイル名を短縮
        if len(safe_chars) > 100:
            name_part = safe_chars[:80]
            ext_part = Path(safe_chars).suffix
            safe_chars = name_part + ext_part
        
        return safe_chars
    
    def archive_old_files(self, source_dir: str, archive_dir: str, days_old: int = 30):
        """古いファイルをアーカイブ"""
        try:
            source_dir = Path(source_dir)
            archive_dir = Path(archive_dir)
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            archived_count = 0
            
            for file_path in source_dir.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        # アーカイブディレクトリに移動
                        archive_path = archive_dir / file_path.name
                        
                        # 重複回避
                        counter = 1
                        while archive_path.exists():
                            name_parts = Path(file_path.name)
                            new_name = f"{name_parts.stem}_{counter}{name_parts.suffix}"
                            archive_path = archive_dir / new_name
                            counter += 1
                        
                        shutil.move(str(file_path), str(archive_path))
                        archived_count += 1
            
            self.logger.info(f"ファイルアーカイブ完了: {archived_count}ファイル")
            return archived_count
            
        except Exception as e:
            self.logger.error(f"ファイルアーカイブエラー: {e}")
            return 0