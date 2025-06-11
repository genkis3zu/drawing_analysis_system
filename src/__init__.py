# src/__init__.py

"""
A4図面解析システム

OpenAI GPT-4 Visionを使用したA4図面の自動データ抽出システム
"""

__version__ = "1.0.0"
__author__ = "Your Company"
__description__ = "A4図面自動解析システム"

# パッケージレベルのインポート
from .core.agent import DrawingAnalysisAgent
from .utils.config import SystemConfig
from .utils.image_processor import A4ImageProcessor

__all__ = [
    "DrawingAnalysisAgent",
    "SystemConfig", 
    "A4ImageProcessor"
]