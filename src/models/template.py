# src/models/template.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import json
import numpy as np

from .drawing import DrawingOrientation, ProductType, DrawingRegion
from .analysis_result import FieldType, ExtractionMethod

class TemplateStatus(Enum):
    """テンプレートの状態"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class ValidationRule(Enum):
    """バリデーションルール"""
    REQUIRED = "required"
    PATTERN = "pattern"
    RANGE = "range"
    LENGTH = "length"
    FORMAT = "format"

@dataclass
class FieldValidation:
    """フィールドバリデーション設定"""
    rule_type: ValidationRule
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    
    def validate(self, value: Any) -> Tuple[bool, str]:
        """値をバリデーション"""
        try:
            if self.rule_type == ValidationRule.REQUIRED:
                is_valid = value is not None and str(value).strip() != ""
                return is_valid, "" if is_valid else "必須項目です"
            
            elif self.rule_type == ValidationRule.PATTERN:
                import re
                pattern = self.parameters.get('pattern', '')
                is_valid = bool(re.match(pattern, str(value)))
                return is_valid, "" if is_valid else f"パターンに一致しません: {pattern}"
            
            elif self.rule_type == ValidationRule.RANGE:
                min_val = self.parameters.get('min')
                max_val = self.parameters.get('max')
                try:
                    num_value = float(value)
                    is_valid = True
                    if min_val is not None and num_value < min_val:
                        is_valid = False
                    if max_val is not None and num_value > max_val:
                        is_valid = False
                    return is_valid, "" if is_valid else f"範囲外の値です ({min_val}-{max_val})"
                except ValueError:
                    return False, "数値ではありません"
            
            elif self.rule_type == ValidationRule.LENGTH:
                min_len = self.parameters.get('min', 0)
                max_len = self.parameters.get('max', float('inf'))
                length = len(str(value))
                is_valid = min_len <= length <= max_len
                return is_valid, "" if is_valid else f"文字数が範囲外です ({min_len}-{max_len})"
            
            elif self.rule_type == ValidationRule.FORMAT:
                format_type = self.parameters.get('format')
                if format_type == 'email':
                    import re
                    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    is_valid = bool(re.match(pattern, str(value)))
                    return is_valid, "" if is_valid else "有効なメールアドレスではありません"
                elif format_type == 'date':
                    try:
                        datetime.strptime(str(value), self.parameters.get('date_format', '%Y-%m-%d'))
                        return True, ""
                    except ValueError:
                        return False, "有効な日付ではありません"
                
            return True, ""
            
        except Exception as e:
            return False, f"バリデーションエラー: {str(e)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'rule_type': self.rule_type.value,
            'parameters': self.parameters,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldValidation':
        """辞書から作成"""
        return cls(
            rule_type=ValidationRule(data['rule_type']),
            parameters=data.get('parameters', {}),
            error_message=data.get('error_message', '')
        )

@dataclass
class TemplateField:
    """テンプレートフィールド定義"""
    field_name: str
    field_type: FieldType
    display_name: str = ""
    description: str = ""
    expected_region: Optional[DrawingRegion] = None
    extraction_method: ExtractionMethod = ExtractionMethod.AI_VISION
    default_value: Any = None
    is_required: bool = False
    validations: List[FieldValidation] = field(default_factory=list)
    extraction_hints: Dict[str, Any] = field(default_factory=dict)
    confidence_threshold: float = 0.7
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.display_name:
            self.display_name = self.field_name
    
    def validate_value(self, value: Any) -> Tuple[bool, List[str]]:
        """値を全バリデーションルールでチェック"""
        errors = []
        
        for validation in self.validations:
            is_valid, error_msg = validation.validate(value)
            if not is_valid:
                errors.append(error_msg or validation.error_message)
        
        return len(errors) == 0, errors
    
    def get_extraction_prompt(self) -> str:
        """抽出用プロンプトを生成"""
        prompt_parts = [f"フィールド名: {self.display_name}"]
        
        if self.description:
            prompt_parts.append(f"説明: {self.description}")
        
        if self.field_type != FieldType.TEXT:
            prompt_parts.append(f"データ型: {self.field_type.value}")
        
        if self.expected_region:
            prompt_parts.append(f"想定位置: x={self.expected_region.x}, y={self.expected_region.y}")
        
        if self.extraction_hints:
            hints = []
            for key, value in self.extraction_hints.items():
                hints.append(f"{key}: {value}")
            prompt_parts.append(f"抽出ヒント: {', '.join(hints)}")
        
        return " | ".join(prompt_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'field_name': self.field_name,
            'field_type': self.field_type.value,
            'display_name': self.display_name,
            'description': self.description,
            'expected_region': self.expected_region.to_dict() if self.expected_region else None,
            'extraction_method': self.extraction_method.value,
            'default_value': self.default_value,
            'is_required': self.is_required,
            'validations': [v.to_dict() for v in self.validations],
            'extraction_hints': self.extraction_hints,
            'confidence_threshold': self.confidence_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateField':
        """辞書から作成"""
        expected_region = None
        if data.get('expected_region'):
            region_data = data['expected_region']
            expected_region = DrawingRegion(
                x=region_data['x'],
                y=region_data['y'],
                width=region_data['width'],
                height=region_data['height'],
                confidence=region_data.get('confidence', 0.0),
                region_type=region_data.get('region_type', 'text')
            )
        
        validations = [
            FieldValidation.from_dict(v_data) 
            for v_data in data.get('validations', [])
        ]
        
        return cls(
            field_name=data['field_name'],
            field_type=FieldType(data['field_type']),
            display_name=data.get('display_name', ''),
            description=data.get('description', ''),
            expected_region=expected_region,
            extraction_method=ExtractionMethod(data.get('extraction_method', 'ai_vision')),
            default_value=data.get('default_value'),
            is_required=data.get('is_required', False),
            validations=validations,
            extraction_hints=data.get('extraction_hints', {}),
            confidence_threshold=data.get('confidence_threshold', 0.7)
        )

@dataclass
class TemplateMetadata:
    """テンプレートメタデータ"""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_by: str = ""
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat(),
            'version': self.version,
            'tags': self.tags,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateMetadata':
        """辞書から作成"""
        return cls(
            created_by=data.get('created_by', ''),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_by=data.get('updated_by', ''),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            version=data.get('version', '1.0'),
            tags=data.get('tags', []),
            notes=data.get('notes', '')
        )

@dataclass
class TemplateStatistics:
    """テンプレート使用統計"""
    usage_count: int = 0
    success_rate: float = 0.0
    average_confidence: float = 0.0
    last_used: Optional[datetime] = None
    total_processing_time: float = 0.0
    field_success_rates: Dict[str, float] = field(default_factory=dict)
    
    def update_usage(self, success: bool, confidence: float, processing_time: float, 
                    field_confidences: Dict[str, float]):
        """使用統計を更新"""
        self.usage_count += 1
        self.last_used = datetime.now()
        self.total_processing_time += processing_time
        
        # 成功率更新
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
            self.average_confidence = confidence
        else:
            # 移動平均
            weight = 1.0 / self.usage_count
            self.success_rate = (1 - weight) * self.success_rate + weight * (1.0 if success else 0.0)
            self.average_confidence = (1 - weight) * self.average_confidence + weight * confidence
        
        # フィールド別成功率更新
        for field_name, field_confidence in field_confidences.items():
            if field_name not in self.field_success_rates:
                self.field_success_rates[field_name] = field_confidence
            else:
                self.field_success_rates[field_name] = (
                    (1 - weight) * self.field_success_rates[field_name] + 
                    weight * field_confidence
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'average_confidence': self.average_confidence,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'total_processing_time': self.total_processing_time,
            'field_success_rates': self.field_success_rates
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateStatistics':
        """辞書から作成"""
        last_used = None
        if data.get('last_used'):
            last_used = datetime.fromisoformat(data['last_used'])
        
        return cls(
            usage_count=data.get('usage_count', 0),
            success_rate=data.get('success_rate', 0.0),
            average_confidence=data.get('average_confidence', 0.0),
            last_used=last_used,
            total_processing_time=data.get('total_processing_time', 0.0),
            field_success_rates=data.get('field_success_rates', {})
        )

@dataclass
class DrawingTemplate:
    """図面テンプレート"""
    template_id: str
    template_name: str
    product_type: ProductType
    orientation: DrawingOrientation
    fields: Dict[str, TemplateField]
    status: TemplateStatus = TemplateStatus.ACTIVE
    confidence_threshold: float = 0.7
    image_features: Optional[np.ndarray] = None
    layout_features: Dict[str, Any] = field(default_factory=dict)
    metadata: TemplateMetadata = field(default_factory=TemplateMetadata)
    statistics: TemplateStatistics = field(default_factory=TemplateStatistics)
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.template_id:
            self.template_id = f"tpl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    @property
    def field_count(self) -> int:
        """フィールド数"""
        return len(self.fields)
    
    @property
    def required_field_count(self) -> int:
        """必須フィールド数"""
        return sum(1 for field in self.fields.values() if field.is_required)
    
    @property
    def is_active(self) -> bool:
        """アクティブかどうか"""
        return self.status == TemplateStatus.ACTIVE
    
    def get_field(self, field_name: str) -> Optional[TemplateField]:
        """フィールドを取得"""
        return self.fields.get(field_name)
    
    def add_field(self, field: TemplateField):
        """フィールドを追加"""
        self.fields[field.field_name] = field
        self.metadata.updated_at = datetime.now()
    
    def remove_field(self, field_name: str) -> bool:
        """フィールドを削除"""
        if field_name in self.fields:
            del self.fields[field_name]
            self.metadata.updated_at = datetime.now()
            return True
        return False
    
    def update_field(self, field_name: str, field: TemplateField):
        """フィールドを更新"""
        if field_name in self.fields:
            self.fields[field_name] = field
            self.metadata.updated_at = datetime.now()
    
    def validate_extracted_data(self, extracted_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """抽出データをバリデーション"""
        validation_errors = {}
        
        for field_name, field in self.fields.items():
            value = extracted_data.get(field_name)
            
            # 必須チェック
            if field.is_required and (value is None or str(value).strip() == ""):
                validation_errors[field_name] = ["必須フィールドです"]
                continue
            
            # 値が存在する場合のバリデーション
            if value is not None:
                is_valid, errors = field.validate_value(value)
                if not is_valid:
                    validation_errors[field_name] = errors
        
        return validation_errors
    
    def generate_extraction_prompt(self) -> str:
        """抽出用プロンプトを生成"""
        prompt_parts = [
            f"テンプレート: {self.template_name}",
            f"製品タイプ: {self.product_type.value}",
            f"図面向き: {self.orientation.value}",
            "",
            "抽出対象フィールド:"
        ]
        
        for field in self.fields.values():
            prompt_parts.append(f"- {field.get_extraction_prompt()}")
        
        return "\n".join(prompt_parts)
    
    def calculate_similarity(self, other_features: np.ndarray) -> float:
        """他の特徴量との類似度を計算"""
        if self.image_features is None or other_features is None:
            return 0.0
        
        try:
            # コサイン類似度を計算
            dot_product = np.dot(self.image_features, other_features)
            norms = np.linalg.norm(self.image_features) * np.linalg.norm(other_features)
            
            if norms == 0:
                return 0.0
            
            similarity = dot_product / norms
            return max(0.0, similarity)  # 負の値は0にクリップ
            
        except Exception:
            return 0.0
    
    def update_statistics(self, success: bool, confidence: float, processing_time: float,
                         field_confidences: Dict[str, float]):
        """統計情報を更新"""
        self.statistics.update_usage(success, confidence, processing_time, field_confidences)
    
    def clone(self, new_template_id: str = None, new_name: str = None) -> 'DrawingTemplate':
        """テンプレートを複製"""
        cloned_template = DrawingTemplate(
            template_id=new_template_id or f"{self.template_id}_copy",
            template_name=new_name or f"{self.template_name} (コピー)",
            product_type=self.product_type,
            orientation=self.orientation,
            fields=self.fields.copy(),
            status=TemplateStatus.DRAFT,
            confidence_threshold=self.confidence_threshold,
            image_features=self.image_features.copy() if self.image_features is not None else None,
            layout_features=self.layout_features.copy(),
            metadata=TemplateMetadata(
                created_by=self.metadata.created_by,
                version="1.0"
            ),
            statistics=TemplateStatistics()
        )
        
        return cloned_template
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'template_id': self.template_id,
            'template_name': self.template_name,
            'product_type': self.product_type.value,
            'orientation': self.orientation.value,
            'fields': {name: field.to_dict() for name, field in self.fields.items()},
            'status': self.status.value,
            'confidence_threshold': self.confidence_threshold,
            'image_features': self.image_features.tolist() if self.image_features is not None else None,
            'layout_features': self.layout_features,
            'metadata': self.metadata.to_dict(),
            'statistics': self.statistics.to_dict(),
            'field_count': self.field_count,
            'required_field_count': self.required_field_count
        }
    
    def to_json(self) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DrawingTemplate':
        """辞書から作成"""
        fields = {}
        for name, field_data in data.get('fields', {}).items():
            fields[name] = TemplateField.from_dict(field_data)
        
        image_features = None
        if data.get('image_features'):
            image_features = np.array(data['image_features'])
        
        metadata = TemplateMetadata.from_dict(data.get('metadata', {}))
        statistics = TemplateStatistics.from_dict(data.get('statistics', {}))
        
        return cls(
            template_id=data['template_id'],
            template_name=data['template_name'],
            product_type=ProductType(data['product_type']),
            orientation=DrawingOrientation(data['orientation']),
            fields=fields,
            status=TemplateStatus(data.get('status', 'active')),
            confidence_threshold=data.get('confidence_threshold', 0.7),
            image_features=image_features,
            layout_features=data.get('layout_features', {}),
            metadata=metadata,
            statistics=statistics
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DrawingTemplate':
        """JSON文字列から作成"""
        data = json.loads(json_str)
        return cls.from_dict(data)

# テンプレート作成用のヘルパー関数
def create_standard_template(product_type: ProductType, orientation: DrawingOrientation) -> DrawingTemplate:
    """標準テンプレートを作成"""
    
    template_id = f"std_{product_type.value}_{orientation.value}"
    template_name = f"標準{product_type.value}テンプレート ({orientation.value})"
    
    # 基本フィールド
    basic_fields = {
        '部品番号': TemplateField(
            field_name='部品番号',
            field_type=FieldType.TEXT,
            display_name='部品番号',
            is_required=True,
            validations=[
                FieldValidation(ValidationRule.REQUIRED),
                FieldValidation(ValidationRule.PATTERN, {'pattern': r'^[A-Z0-9\-]+$'})
            ]
        ),
        '材質': TemplateField(
            field_name='材質',
            field_type=FieldType.TEXT,
            display_name='材質',
            is_required=True
        ),
        '寸法': TemplateField(
            field_name='寸法',
            field_type=FieldType.DIMENSION,
            display_name='寸法',
            is_required=True
        )
    }
    
    # 製品タイプ別の追加フィールド
    if product_type == ProductType.MECHANICAL_PART:
        basic_fields.update({
            '表面処理': TemplateField(
                field_name='表面処理',
                field_type=FieldType.TEXT,
                display_name='表面処理'
            ),
            '精度': TemplateField(
                field_name='精度',
                field_type=FieldType.TEXT,
                display_name='精度'
            )
        })
    elif product_type == ProductType.ELECTRICAL_COMPONENT:
        basic_fields.update({
            '定格': TemplateField(
                field_name='定格',
                field_type=FieldType.TEXT,
                display_name='定格'
            ),
            '温度範囲': TemplateField(
                field_name='温度範囲',
                field_type=FieldType.TEXT,
                display_name='温度範囲'
            )
        })
    
    return DrawingTemplate(
        template_id=template_id,
        template_name=template_name,
        product_type=product_type,
        orientation=orientation,
        fields=basic_fields,
        metadata=TemplateMetadata(
            created_by='system',
            notes='システム作成の標準テンプレート'
        )
    )