# src/ui/pages/__init__.py

"""
Streamlit ページモジュール

各機能別のページを提供します。
- 図面解析ページ
- テンプレート管理ページ
- バッチ処理ページ
- システム設定ページ
"""

from . import analysis
from . import templates
from . import batch
from . import settings

__all__ = [
    "analysis",
    "templates", 
    "batch",
    "settings"
]