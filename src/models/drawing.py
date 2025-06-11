# src/models/drawing.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from pathlib import Path

class DrawingOrientation(Enum):
    """図面の向き"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

class DrawingFormat(Enum):
    """図面のファイル形式"""
    PNG = "png"
    PDF = "pdf"
    JPEG = "jpeg"
    TIFF = "tiff"

class ProductType(Enum):
    """製品タイプ"""
    MECHANICAL_PART = "mechanical_part"
    ELECTRICAL_COMPONENT = "electrical_component"
    ASSEMBLY_DRAWING = "assembly_drawing"
    WIRING_DIAGRAM = "wiring_diagram"
    OTHER = "other"

@dataclass
class DrawingDimensions:
    """図面の寸法情報"""
    width: int
    height: int
    dpi: int
    
    @property
    def width_mm(self) -> float:
        """幅をmm単位で取得"""
        return (self.width / self.dpi) * 25.4
    
    @property
    def height_mm(self) -> float:
        """高さをmm単位で取得"""
        return (self.height / self.dpi) * 25.4
    
    @property
    def aspect_ratio(self) -> float:
        """アスペクト比を取得"""
        return self.width / self.height if self.height > 0 else 0
    
    @property
    def is_a4_size(self) -> bool:
        """A4サイズかどうか判定"""
        A4_RATIO = 297 / 210  # A4の縦横比
        ratio = max(self.aspect_ratio, 1/self.aspect_ratio)
        return abs(ratio - A4_RATIO) <= 0.1

@dataclass
class DrawingQuality:
    """図面の品質情報"""
    image_quality: float = 0.0  # 0.0-1.0
    text_clarity: float = 0.0   # 0.0-1.0
    line_sharpness: float = 0.0 # 0.0-1.0
    noise_level: float = 0.0    # 0.0-1.0 (低いほど良い)
    
    @property
    def overall_quality(self) -> float:
        """総合品質スコア"""
        return (self.image_quality + self.text_clarity + self.line_sharpness + (1 - self.noise_level)) / 4

@dataclass
class DrawingInfo:
    """図面の基本情報"""
    file_path: str
    file_name: str
    file_size: int
    file_format: DrawingFormat
    dimensions: DrawingDimensions
    orientation: DrawingOrientation
    quality: DrawingQuality
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def file_size_mb(self) -> float:
        """ファイルサイズをMB単位で取得"""
        return self.file_size / (1024 * 1024)
    
    @property
    def is_high_quality(self) -> bool:
        """高品質かどうか判定"""
        return (self.quality.overall_quality >= 0.7 and 
                self.dimensions.dpi >= 200 and
                self.dimensions.is_a4_size)

@dataclass
class DrawingAnalysisRequest:
    """図面解析リクエスト"""
    drawing_info: DrawingInfo
    product_type: Optional[ProductType] = None
    target_fields: List[str] = field(default_factory=list)
    use_template: bool = True
    high_precision_mode: bool = False
    extract_dimensions: bool = True
    extract_materials: bool = True
    extract_specifications: bool = True
    confidence_threshold: float = 0.7
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'file_path': self.drawing_info.file_path,
            'product_type': self.product_type.value if self.product_type else None,
            'target_fields': self.target_fields,
            'use_template': self.use_template,
            'high_precision_mode': self.high_precision_mode,
            'extract_dimensions': self.extract_dimensions,
            'extract_materials': self.extract_materials,
            'extract_specifications': self.extract_specifications,
            'confidence_threshold': self.confidence_threshold,
            'custom_prompts': self.custom_prompts
        }

@dataclass
class DrawingRegion:
    """図面内の領域情報"""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.0
    region_type: str = "unknown"  # text, dimension, symbol, etc.
    
    @property
    def center(self) -> Tuple[int, int]:
        """中心座標を取得"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        """面積を取得"""
        return self.width * self.height
    
    def overlaps_with(self, other: 'DrawingRegion') -> bool:
        """他の領域と重複するかチェック"""
        return not (self.x + self.width <= other.x or
                   other.x + other.width <= self.x or
                   self.y + self.height <= other.y or
                   other.y + other.height <= self.y)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'confidence': self.confidence,
            'region_type': self.region_type,
            'center': self.center,
            'area': self.area
        }

@dataclass
class DrawingElement:
    """図面要素（線、円、文字など）"""
    element_type: str  # line, circle, rectangle, text, dimension
    region: DrawingRegion
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'element_type': self.element_type,
            'region': self.region.to_dict(),
            'properties': self.properties,
            'confidence': self.confidence
        }

@dataclass
class DrawingLayout:
    """図面レイアウト情報"""
    title_block: Optional[DrawingRegion] = None
    main_view: Optional[DrawingRegion] = None
    dimension_regions: List[DrawingRegion] = field(default_factory=list)
    text_regions: List[DrawingRegion] = field(default_factory=list)
    table_regions: List[DrawingRegion] = field(default_factory=list)
    border_region: Optional[DrawingRegion] = None
    
    @property
    def total_text_area(self) -> int:
        """テキスト領域の総面積"""
        return sum(region.area for region in self.text_regions)
    
    @property
    def layout_complexity(self) -> float:
        """レイアウト複雑度（0.0-1.0）"""
        region_count = (len(self.dimension_regions) + 
                       len(self.text_regions) + 
                       len(self.table_regions))
        return min(region_count / 50.0, 1.0)  # 50要素で最大値
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'title_block': self.title_block.to_dict() if self.title_block else None,
            'main_view': self.main_view.to_dict() if self.main_view else None,
            'dimension_regions': [r.to_dict() for r in self.dimension_regions],
            'text_regions': [r.to_dict() for r in self.text_regions],
            'table_regions': [r.to_dict() for r in self.table_regions],
            'border_region': self.border_region.to_dict() if self.border_region else None,
            'total_text_area': self.total_text_area,
            'layout_complexity': self.layout_complexity
        }

@dataclass
class DrawingMetadata:
    """図面メタデータ"""
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    title: Optional[str] = None
    creator: Optional[str] = None
    company: Optional[str] = None
    creation_date: Optional[datetime] = None
    scale: Optional[str] = None
    units: Optional[str] = None
    sheet_size: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'drawing_number': self.drawing_number,
            'revision': self.revision,
            'title': self.title,
            'creator': self.creator,
            'company': self.company,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'scale': self.scale,
            'units': self.units,
            'sheet_size': self.sheet_size
        }

def create_drawing_info_from_file(file_path: str) -> DrawingInfo:
    """ファイルパスから DrawingInfo を作成"""
    from PIL import Image
    import os
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    # ファイル基本情報
    file_size = file_path.stat().st_size
    file_format = DrawingFormat(file_path.suffix.lower().lstrip('.'))
    
    # 画像寸法情報（PDFの場合は別途処理が必要）
    if file_format in [DrawingFormat.PNG, DrawingFormat.JPEG, DrawingFormat.TIFF]:
        with Image.open(file_path) as img:
            width, height = img.size
            dpi_info = img.info.get('dpi', (300, 300))
            dpi = int(dpi_info[0]) if isinstance(dpi_info, tuple) else int(dpi_info)
    else:
        # PDFの場合のデフォルト値
        width, height, dpi = 2480, 3508, 300  # A4 300DPI
    
    dimensions = DrawingDimensions(width=width, height=height, dpi=dpi)
    
    # 向きの判定
    orientation = DrawingOrientation.LANDSCAPE if width > height else DrawingOrientation.PORTRAIT
    
    # 品質情報（初期値）
    quality = DrawingQuality(
        image_quality=0.8,
        text_clarity=0.8,
        line_sharpness=0.8,
        noise_level=0.2
    )
    
    return DrawingInfo(
        file_path=str(file_path),
        file_name=file_path.name,
        file_size=file_size,
        file_format=file_format,
        dimensions=dimensions,
        orientation=orientation,
        quality=quality
    )