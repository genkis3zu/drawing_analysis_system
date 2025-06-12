# src/utils/config.py

import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional
import logging

class SystemConfig:
    """システム設定管理クラス"""
    
    DEFAULT_CONFIG = {
        'openai': {
            'api_key': 'your-openai-api-key-here',
            'model': 'gpt-4-vision-preview',
            'max_tokens': 2000,
            'temperature': 0.1
        },
        'database': {
            'path': 'database/drawing_analysis.db',
            'backup_path': 'database/backups/',
            'auto_backup': True,
            'backup_interval_hours': 24
        },
        'files': {
            'input_directory': 'data/input/',
            'output_directory': 'data/output/',
            'temp_directory': 'data/temp/',
            'samples_directory': 'data/samples/',
            'supported_formats': ['.jpg', '.jpeg', '.png', '.pdf', '.tiff']
        },
        'image_processing': {
            'target_dpi': 300,
            'min_dpi': 150,
            'max_dpi': 600,
            'auto_enhance': True,
            'noise_reduction': True,
            'contrast_adjustment': True
        },
        'processing': {
            'batch_size': 10,
            'max_workers': 4,
            'timeout_seconds': 300,
            'retry_attempts': 3
        },
        'extraction': {
            'confidence_threshold': 0.7,
            'auto_correction': True,
            'default_fields': [
                '部品番号', '製品名', '材質', '寸法',
                '重量', '表面処理', '精度', '図面番号'
            ]
        },
        'excel': {
            'template_directory': 'data/excel_templates/',
            'output_directory': 'data/excel_output/',
            'default_template': 'default_template.xlsx'
        },
        'learning': {
            'auto_learning': True,
            'confidence_threshold': 0.8,
            'similarity_threshold': 0.85,
            'min_training_samples': 5,
            'template_creation_threshold': 0.9
        },
        'ui': {
            'page_title': 'A4図面解析システム',
            'theme': 'light',
            'sidebar_state': 'expanded',
            'show_tips': True
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/drawing_analysis.log',
            'max_size_mb': 100,
            'backup_count': 5,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        if not self.config_path.exists():
            self.logger.info(f"設定ファイルが見つかりません。デフォルト設定を作成します: {self.config_path}")
            self._create_default_config()
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # デフォルト設定とマージ
            merged_config = self._merge_configs(self.DEFAULT_CONFIG, config)
            return merged_config
            
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            self.logger.info("デフォルト設定を使用します")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """設定をマージ"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_default_config(self):
        """デフォルト設定ファイルを作成"""
        try:
            # ディレクトリ作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            self.logger.info(f"デフォルト設定ファイルを作成しました: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"設定ファイル作成エラー: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """設定値を取得（ドット記法対応）"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
        except Exception:
            return default
    
    def set(self, key_path: str, value: Any):
        """設定値を設定"""
        keys = key_path.split('.')
        config_ref = self.config
        
        # 最後のキー以外まで辿る
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # 値を設定
        config_ref[keys[-1]] = value
    
    def update(self, key_path: str, value: Any):
        """設定値を更新して保存"""
        self.set(key_path, value)
        self.save()
    
    def save(self):
        """設定ファイルを保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False,
                         allow_unicode=True, indent=2)
            self.logger.info("設定ファイルを保存しました")
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")
    
    def validate(self) -> bool:
        """設定の妥当性をチェック"""
        errors = []
        
        # OpenAI APIキーチェック
        api_key = self.get('openai.api_key')
        if not api_key or api_key == 'your-openai-api-key-here':
            errors.append("OpenAI APIキーが設定されていません")
        
        # ディレクトリの存在チェック
        directories = [
            'files.input_directory',
            'files.output_directory', 
            'files.temp_directory'
        ]
        
        for dir_key in directories:
            dir_path = Path(self.get(dir_key, ''))
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"ディレクトリを作成しました: {dir_path}")
                except Exception as e:
                    errors.append(f"ディレクトリ作成失敗 {dir_path}: {e}")
        
        # 数値範囲チェック
        confidence_threshold = self.get('extraction.confidence_threshold', 0.7)
        if not 0.0 <= confidence_threshold <= 1.0:
            errors.append("confidence_thresholdは0.0-1.0の範囲で設定してください")
        
        if errors:
            for error in errors:
                self.logger.error(f"設定エラー: {error}")
            return False
        
        return True
    
    def get_openai_config(self) -> Dict[str, Any]:
        """OpenAI設定を取得"""
        return {
            'api_key': self.get('openai.api_key'),
            'model': self.get('openai.model', 'gpt-4-vision-preview'),
            'max_tokens': self.get('openai.max_tokens', 2000),
            'temperature': self.get('openai.temperature', 0.1)
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """データベース設定を取得"""
        return {
            'path': self.get('database.path', 'database/drawing_analysis.db'),
            'backup_path': self.get('database.backup_path', 'database/backups/'),
            'auto_backup': self.get('database.auto_backup', True),
            'backup_interval_hours': self.get('database.backup_interval_hours', 24)
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """処理設定を取得"""
        return {
            'batch_size': self.get('processing.batch_size', 10),
            'max_workers': self.get('processing.max_workers', 4),
            'timeout_seconds': self.get('processing.timeout_seconds', 300),
            'retry_attempts': self.get('processing.retry_attempts', 3)
        }
    
    def get_image_config(self) -> Dict[str, Any]:
        """画像処理設定を取得"""
        return {
            'target_dpi': self.get('image_processing.target_dpi', 300),
            'min_dpi': self.get('image_processing.min_dpi', 150),
            'max_dpi': self.get('image_processing.max_dpi', 600),
            'auto_enhance': self.get('image_processing.auto_enhance', True),
            'noise_reduction': self.get('image_processing.noise_reduction', True),
            'contrast_adjustment': self.get('image_processing.contrast_adjustment', True)
        }
    
    def __str__(self) -> str:
        """設定の文字列表現"""
        return f"SystemConfig(config_path={self.config_path})"
    
    def __repr__(self) -> str:
        return self.__str__()
