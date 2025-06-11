# src/utils/file_handler.py

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Union, List
import logging

class FileHandler:
    """ファイル操作を管理するクラス"""
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
        """JSONファイルとして保存"""
        
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            FileHandler.logger.info(f"JSONファイル保存完了: {file_path}")
            return True
        
        except Exception as e:
            FileHandler.logger.error(f"JSONファイル保存エラー: {e}")
            return False
    
    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """JSONファイルを読み込み"""
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            FileHandler.logger.info(f"JSONファイル読み込み完了: {file_path}")
            return data
        
        except Exception as e:
            FileHandler.logger.error(f"JSONファイル読み込みエラー: {e}")
            raise
    
    @staticmethod
    def save_excel(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
        """Excelファイルとして保存"""
        
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # データフレーム作成
            if 'file_results' in data:
                # バッチ処理結果の場合
                df = pd.DataFrame(data['file_results'])
            else:
                # 単一ファイル結果の場合
                df = pd.DataFrame([data])
            
            # Excel保存
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Results', index=False)
                
                # シート幅調整
                worksheet = writer.sheets['Results']
                for i, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    worksheet.set_column(i, i, max_length + 2)
            
            FileHandler.logger.info(f"Excelファイル保存完了: {file_path}")
            return True
        
        except Exception as e:
            FileHandler.logger.error(f"Excelファイル保存エラー: {e}")
            return False
    
    @staticmethod
    def save_csv(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
        """CSVファイルとして保存"""
        
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # データフレーム作成
            if 'file_results' in data:
                # バッチ処理結果の場合
                df = pd.DataFrame(data['file_results'])
            else:
                # 単一ファイル結果の場合
                df = pd.DataFrame([data])
            
            # CSV保存
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            FileHandler.logger.info(f"CSVファイル保存完了: {file_path}")
            return True
        
        except Exception as e:
            FileHandler.logger.error(f"CSVファイル保存エラー: {e}")
            return False
    
    @staticmethod
    def get_supported_files(directory: Union[str, Path], extensions: List[str]) -> List[Path]:
        """指定された拡張子のファイルを取得"""
        
        try:
            directory = Path(directory)
            
            if not directory.exists():
                raise FileNotFoundError(f"ディレクトリが見つかりません: {directory}")
            
            files = []
            for ext in extensions:
                # 小文字と大文字の両方を検索
                files.extend(directory.glob(f"*{ext.lower()}"))
                files.extend(directory.glob(f"*{ext.upper()}"))
            
            return sorted(files)
        
        except Exception as e:
            FileHandler.logger.error(f"ファイル検索エラー: {e}")
            raise
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> bool:
        """ディレクトリの存在を確認し、必要に応じて作成"""
        
        try:
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            return True
        
        except Exception as e:
            FileHandler.logger.error(f"ディレクトリ作成エラー: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """ファイル情報を取得"""
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
            stat = file_path.stat()
            
            return {
                'name': file_path.name,
                'stem': file_path.stem,
                'suffix': file_path.suffix,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir()
            }
        
        except Exception as e:
            FileHandler.logger.error(f"ファイル情報取得エラー: {e}")
            raise
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """ファイルを削除"""
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            FileHandler.logger.info(f"ファイル削除完了: {file_path}")
            return True
        
        except Exception as e:
            FileHandler.logger.error(f"ファイル削除エラー: {e}")
            return False
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """ファイルを移動"""
        
        try:
            src = Path(src)
            dst = Path(dst)
            
            if not src.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {src}")
            
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            
            FileHandler.logger.info(f"ファイル移動完了: {src} -> {dst}")
            return True
        
        except Exception as e:
            FileHandler.logger.error(f"ファイル移動エラー: {e}")
            return False
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """ファイルをコピー"""
        
        try:
            src = Path(src)
            dst = Path(dst)
            
            if not src.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {src}")
            
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            
            FileHandler.logger.info(f"ファイルコピー完了: {src} -> {dst}")
            return True
        
        except Exception as e:
            FileHandler.logger.error(f"ファイルコピーエラー: {e}")
            return False
