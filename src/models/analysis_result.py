# src/models/analysis_result.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json

class ExtractionMethod(Enum):
    """抽出方法"""
    OCR = "ocr"
    AI_VISION = "ai_vision"
    PATTERN_MATCH = "pattern_match"
    TEMPLATE_BASED = "template_based"
    MANUAL = "manual"

class FieldType(Enum):
    """フィールドタイプ"""
    TEXT = "text"
    NUMBER = "number"
    DIMENSION = "dimension"
    DATE = "date"
    BOOLEAN = "boolean"
    LIST = "list"

@dataclass
class ExtractionResult:
    """個別フィールドの抽出結果"""
    field_name: str
    value: Any
    confidence: float
    position: Optional[Dict[str, int]] = None  # {'x': x, 'y': y, 'width': w, 'height': h}
    extraction_method: ExtractionMethod = ExtractionMethod.AI_VISION
    field_type: FieldType = FieldType.TEXT
    raw_value: Optional[str] = None  # OCR等の生の抽出値
    validation_status: str = "unknown"  # valid, invalid, warning, unknown
    notes: Optional[str] = None
    
    @property
    def is_high_confidence(self) -> bool:
        """高信頼度かどうか"""
        return self.confidence >= 0.8
    
    @property
    def is_valid(self) -> bool:
        """有効な値かどうか"""
        return self.validation_status == "valid"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'field_name': self.field_name,
            'value': self.value,
            'confidence': self.confidence,
            'position': self.position,
            'extraction_method': self.extraction_method.value,
            'field_type': self.field_type.value,
            'raw_value': self.raw_value,
            'validation_status': self.validation_status,
            'notes': self.notes,
            'is_high_confidence': self.is_high_confidence,
            'is_valid': self.is_valid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionResult':
        """辞書から作成"""
        return cls(
            field_name=data['field_name'],
            value=data['value'],
            confidence=data['confidence'],
            position=data.get('position'),
            extraction_method=ExtractionMethod(data.get('extraction_method', 'ai_vision')),
            field_type=FieldType(data.get('field_type', 'text')),
            raw_value=data.get('raw_value'),
            validation_status=data.get('validation_status', 'unknown'),
            notes=data.get('notes')
        )

@dataclass
class QualityMetrics:
    """品質メトリクス"""
    overall_confidence: float = 0.0
    high_confidence_fields: int = 0
    total_fields: int = 0
    extraction_completeness: float = 0.0  # 期待フィールド数に対する割合
    validation_pass_rate: float = 0.0
    
    @property
    def confidence_distribution(self) -> Dict[str, int]:
        """信頼度分布"""
        # 実装では各信頼度レンジのカウントを返す
        return {
            'high': self.high_confidence_fields,
            'medium': max(0, self.total_fields - self.high_confidence_fields),
            'low': 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'overall_confidence': self.overall_confidence,
            'high_confidence_fields': self.high_confidence_fields,
            'total_fields': self.total_fields,
            'extraction_completeness': self.extraction_completeness,
            'validation_pass_rate': self.validation_pass_rate,
            'confidence_distribution': self.confidence_distribution
        }

@dataclass
class ProcessingMetrics:
    """処理メトリクス"""
    processing_time: float = 0.0
    api_calls: int = 0
    tokens_used: int = 0
    image_preprocessing_time: float = 0.0
    ai_analysis_time: float = 0.0
    post_processing_time: float = 0.0
    
    @property
    def total_time(self) -> float:
        """総処理時間"""
        return (self.image_preprocessing_time + 
                self.ai_analysis_time + 
                self.post_processing_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'processing_time': self.processing_time,
            'api_calls': self.api_calls,
            'tokens_used': self.tokens_used,
            'image_preprocessing_time': self.image_preprocessing_time,
            'ai_analysis_time': self.ai_analysis_time,
            'post_processing_time': self.post_processing_time,
            'total_time': self.total_time
        }

@dataclass
class AnalysisResult:
    """図面解析結果"""
    drawing_path: str
    extracted_data: Dict[str, ExtractionResult]
    template_id: Optional[str] = None
    product_type: Optional[str] = None
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    processing_metrics: ProcessingMetrics = field(default_factory=ProcessingMetrics)
    a4_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    result_id: Optional[str] = None
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.result_id:
            self.result_id = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 品質メトリクスを計算
        self._calculate_quality_metrics()
    
    def _calculate_quality_metrics(self):
        """品質メトリクスを計算"""
        if not self.extracted_data:
            return
        
        confidences = [result.confidence for result in self.extracted_data.values()]
        high_conf_count = sum(1 for c in confidences if c >= 0.8)
        valid_count = sum(1 for result in self.extracted_data.values() if result.is_valid)
        
        self.quality_metrics = QualityMetrics(
            overall_confidence=sum(confidences) / len(confidences),
            high_confidence_fields=high_conf_count,
            total_fields=len(self.extracted_data),
            extraction_completeness=1.0,  # 実装では期待フィールド数と比較
            validation_pass_rate=valid_count / len(self.extracted_data)
        )
    
    @property
    def is_successful(self) -> bool:
        """解析が成功したかどうか"""
        return (self.quality_metrics.overall_confidence >= 0.6 and
                len(self.extracted_data) > 0)
    
    @property
    def confidence_score(self) -> float:
        """総合信頼度スコア"""
        return self.quality_metrics.overall_confidence
    
    def get_field_value(self, field_name: str) -> Any:
        """フィールド値を取得"""
        if field_name in self.extracted_data:
            return self.extracted_data[field_name].value
        return None
    
    def get_high_confidence_fields(self) -> Dict[str, ExtractionResult]:
        """高信頼度フィールドを取得"""
        return {
            name: result for name, result in self.extracted_data.items()
            if result.is_high_confidence
        }
    
    def get_low_confidence_fields(self) -> Dict[str, ExtractionResult]:
        """低信頼度フィールドを取得"""
        return {
            name: result for name, result in self.extracted_data.items()
            if not result.is_high_confidence
        }
    
    def update_field(self, field_name: str, new_value: Any, notes: str = None):
        """フィールド値を更新"""
        if field_name in self.extracted_data:
            self.extracted_data[field_name].value = new_value
            self.extracted_data[field_name].extraction_method = ExtractionMethod.MANUAL
            self.extracted_data[field_name].confidence = 1.0  # 手動修正は最高信頼度
            if notes:
                self.extracted_data[field_name].notes = notes
            
            # 品質メトリクス再計算
            self._calculate_quality_metrics()
    
    def add_field(self, field_name: str, value: Any, confidence: float = 1.0):
        """新しいフィールドを追加"""
        self.extracted_data[field_name] = ExtractionResult(
            field_name=field_name,
            value=value,
            confidence=confidence,
            extraction_method=ExtractionMethod.MANUAL
        )
        
        # 品質メトリクス再計算
        self._calculate_quality_metrics()
    
    def remove_field(self, field_name: str):
        """フィールドを削除"""
        if field_name in self.extracted_data:
            del self.extracted_data[field_name]
            # 品質メトリクス再計算
            self._calculate_quality_metrics()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'result_id': self.result_id,
            'drawing_path': self.drawing_path,
            'extracted_data': {
                name: result.to_dict() 
                for name, result in self.extracted_data.items()
            },
            'template_id': self.template_id,
            'product_type': self.product_type,
            'quality_metrics': self.quality_metrics.to_dict(),
            'processing_metrics': self.processing_metrics.to_dict(),
            'a4_info': self.a4_info,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'is_successful': self.is_successful,
            'confidence_score': self.confidence_score
        }
    
    def to_json(self) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """辞書から作成"""
        extracted_data = {}
        for name, result_data in data.get('extracted_data', {}).items():
            extracted_data[name] = ExtractionResult.from_dict(result_data)
        
        quality_metrics = QualityMetrics(**data.get('quality_metrics', {}))
        processing_metrics = ProcessingMetrics(**data.get('processing_metrics', {}))
        
        created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        
        return cls(
            result_id=data.get('result_id'),
            drawing_path=data['drawing_path'],
            extracted_data=extracted_data,
            template_id=data.get('template_id'),
            product_type=data.get('product_type'),
            quality_metrics=quality_metrics,
            processing_metrics=processing_metrics,
            a4_info=data.get('a4_info', {}),
            metadata=data.get('metadata', {}),
            created_at=created_at
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AnalysisResult':
        """JSON文字列から作成"""
        data = json.loads(json_str)
        return cls.from_dict(data)

@dataclass
class AnalysisComparison:
    """解析結果の比較"""
    original_result: AnalysisResult
    modified_result: AnalysisResult
    differences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """比較を実行"""
        self._calculate_differences()
    
    def _calculate_differences(self):
        """差分を計算"""
        original_fields = set(self.original_result.extracted_data.keys())
        modified_fields = set(self.modified_result.extracted_data.keys())
        
        # 追加されたフィールド
        added_fields = modified_fields - original_fields
        for field in added_fields:
            self.differences[field] = {
                'type': 'added',
                'new_value': self.modified_result.extracted_data[field].value,
                'confidence': self.modified_result.extracted_data[field].confidence
            }
        
        # 削除されたフィールド
        removed_fields = original_fields - modified_fields
        for field in removed_fields:
            self.differences[field] = {
                'type': 'removed',
                'old_value': self.original_result.extracted_data[field].value
            }
        
        # 変更されたフィールド
        common_fields = original_fields & modified_fields
        for field in common_fields:
            orig_value = self.original_result.extracted_data[field].value
            mod_value = self.modified_result.extracted_data[field].value
            
            if orig_value != mod_value:
                self.differences[field] = {
                    'type': 'modified',
                    'old_value': orig_value,
                    'new_value': mod_value,
                    'old_confidence': self.original_result.extracted_data[field].confidence,
                    'new_confidence': self.modified_result.extracted_data[field].confidence
                }
    
    @property
    def has_differences(self) -> bool:
        """差分があるかどうか"""
        return len(self.differences) > 0
    
    @property
    def improvement_score(self) -> float:
        """改善スコア"""
        if not self.has_differences:
            return 0.0
        
        orig_confidence = self.original_result.confidence_score
        mod_confidence = self.modified_result.confidence_score
        
        return mod_confidence - orig_confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'original_confidence': self.original_result.confidence_score,
            'modified_confidence': self.modified_result.confidence_score,
            'improvement_score': self.improvement_score,
            'differences': self.differences,
            'has_differences': self.has_differences
        }