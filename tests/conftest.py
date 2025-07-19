"""pytestの設定とフィクスチャ"""

import os
import sys
import pytest
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト用の環境変数設定
os.environ['TESTING'] = 'true'

@pytest.fixture
def sample_a4_portrait_path():
    """A4縦向きのサンプル画像パス"""
    return str(project_root / "tests" / "fixtures" / "sample_drawings" / "sample_a4_portrait.png")

@pytest.fixture
def sample_a4_landscape_path():
    """A4横向きのサンプル画像パス"""
    return str(project_root / "tests" / "fixtures" / "sample_drawings" / "sample_a4_landscape.png")

@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリ"""
    return tmp_path

@pytest.fixture
def mock_config():
    """テスト用の設定"""
    return {
        'openai': {
            'api_key': 'test-api-key',
            'model': 'gpt-4-vision-preview',
            'max_tokens': 2000,
            'temperature': 0.1
        },
        'image_processing': {
            'target_dpi': 300,
            'auto_enhance': True,
            'noise_reduction': True
        },
        'extraction': {
            'confidence_threshold': 0.7,
            'default_fields': ['部品番号', '材質', '寸法']
        },
        'database': {
            'path': ':memory:'  # インメモリデータベース
        }
    }

@pytest.fixture
def mock_openai_response():
    """OpenAI APIレスポンスのモック"""
    return {
        "choices": [{
            "message": {
                "content": '''{
                    "部品番号": {"value": "A-123", "confidence": 0.95},
                    "材質": {"value": "SUS304", "confidence": 0.88},
                    "寸法": {"value": "100x50x3", "confidence": 0.92}
                }'''
            }
        }]
    }