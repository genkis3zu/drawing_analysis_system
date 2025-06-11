# src/core/agent.py

import openai
import base64
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..utils.database import DatabaseManager
from ..utils.image_processor import A4ImageProcessor, A4DrawingInfo
from ..models.analysis_result import AnalysisResult, ExtractionResult, ProcessingMetrics, ExtractionMethod, FieldType
from ..models.template import DrawingTemplate
from ..models.drawing import DrawingInfo, DrawingAnalysisRequest, ProductType

class DrawingAnalysisAgent:
    """A4図面解析エージェント"""
    
    def __init__(self, api_key: str, database_path: str = "database/drawing_analysis.db"):
        self.client = openai.OpenAI(api_key=api_key)
        self.db_manager = DatabaseManager(database_path)
        self.image_processor = A4ImageProcessor()
        self.logger = logging.getLogger(__name__)
        
        # A4図面専用のベースプロンプト
        self.base_prompt = """
あなたはA4図面の専門解析AIです。以下の特徴を理解して解析してください：

## A4図面の特徴
- サイズ: 210×297mm（縦向き）または 297×210mm（横向き）
- 日本の製図規格（JIS）に準拠
- 一般的な図面枠とタイトルブロック配置
- 標準的な寸法記入方法

## 抽出対象情報
1. **識別情報**: 部品番号、製品番号、図面番号
2. **寸法情報**: 長さ、幅、高さ、直径、角度
3. **材質情報**: 材料名、材質記号、規格
4. **仕様情報**: 表面処理、精度、公差
5. **管理情報**: 作成者、承認者、作成日、改訂

## 出力形式
以下のJSON形式で結果を返してください：

```json
{
  "orientation": "portrait" | "landscape",
  "drawing_type": "機械部品" | "電気部品" | "組立図" | "配線図" | "その他",
  "extracted_data": {
    "field_name": {
      "value": "抽出された値",
      "confidence": 0.0-1.0の信頼度,
      "position": {"x": x座標, "y": y座標, "width": 幅, "height": 高さ},
      "extraction_method": "OCR" | "Pattern" | "AI",
      "field_type": "text" | "number" | "dimension" | "date"
    }
  },
  "quality_assessment": {
    "image_quality": 0.0-1.0,
    "text_clarity": 0.0-1.0,
    "completeness": 0.0-1.0
  }
}
```

## 注意点
- A4サイズの制約内での標準的な配置を考慮
- 日本語の図面文字を正確に認識
- 寸法線と寸法値の関連性を理解
- 信頼度は慎重に評価（不明確な場合は低く設定）
"""
    
    def analyze_drawing(self, image_path: str, request: Optional[DrawingAnalysisRequest] = None, **options) -> AnalysisResult:
        """A4図面を解析"""
        
        start_time = time.time()
        processing_metrics = ProcessingMetrics()
        
        try:
            self.logger.info(f"図面解析開始: {image_path}")
            
            # 1. A4図面の前処理と最適化
            preprocessing_start = time.time()
            drawing_info = self.image_processor.analyze_a4_drawing(image_path)
            
            optimized_path = image_path
            if not drawing_info.is_valid_a4:
                self.logger.warning("非A4サイズの図面です。最適化を実行します。")
                optimized_path = self.image_processor.optimize_a4_drawing(image_path)
            
            processing_metrics.image_preprocessing_time = time.time() - preprocessing_start
            
            # 2. リクエスト情報の処理
            if request is None:
                request = DrawingAnalysisRequest(
                    drawing_info=DrawingInfo(
                        file_path=image_path,
                        file_name=Path(image_path).name,
                        file_size=Path(image_path).stat().st_size,
                        file_format=Path(image_path).suffix.lower(),
                        dimensions=drawing_info,
                        orientation=drawing_info.orientation,
                        quality=drawing_info
                    ),
                    **options
                )
            
            # 3. 既存テンプレートの検索
            template = None
            if request.use_template:
                template = self._find_matching_template(optimized_path, request.product_type)
                if template:
                    self.logger.info(f"マッチするテンプレートを発見: {template.template_id}")
            
            # 4. AI解析実行
            ai_start = time.time()
            if template:
                results = self._analyze_with_template(optimized_path, template, request)
            else:
                results = self._analyze_without_template(optimized_path, request)
            
            processing_metrics.ai_analysis_time = time.time() - ai_start
            processing_metrics.api_calls = 1
            
            # 5. 後処理
            post_start = time.time()
            analysis_result = self._post_process_results(results, drawing_info, request, template)
            processing_metrics.post_processing_time = time.time() - post_start
            
            # 6. 処理メトリクス設定
            processing_metrics.processing_time = time.time() - start_time
            analysis_result.processing_metrics = processing_metrics
            
            # 7. 結果保存
            self._save_analysis_result(analysis_result)
            
            self.logger.info(f"図面解析完了: {processing_metrics.processing_time:.2f}秒")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"図面解析エラー: {e}")
            # エラー時も基本的な結果を返す
            return AnalysisResult(
                drawing_path=image_path,
                extracted_data={},
                processing_metrics=ProcessingMetrics(processing_time=time.time() - start_time),
                metadata={'error': str(e)}
            )
    
    def _find_matching_template(self, image_path: str, product_type: Optional[ProductType]) -> Optional[DrawingTemplate]:
        """マッチするテンプレートを検索"""
        
        try:
            # 画像特徴量を抽出
            features = self.image_processor.extract_layout_features(image_path)
            
            # データベースからテンプレートを検索
            product_type_str = product_type.value if product_type else None
            templates = self.db_manager.get_templates_by_type(product_type_str)
            
            if not templates:
                return None
            
            best_match = None
            best_similarity = 0.0
            
            for template_data in templates:
                # テンプレートオブジェクトに変換
                template = DrawingTemplate.from_dict(template_data)
                
                # 簡易的な類似度計算（実際はより詳細な特徴量比較を行う）
                similarity = self._calculate_template_similarity(features, template.layout_features)
                
                if similarity > best_similarity and similarity > 0.75:  # 閾値
                    best_similarity = similarity
                    best_match = template
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"テンプレート検索エラー: {e}")
            return None
    
    def _calculate_template_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """テンプレート類似度を計算"""
        
        try:
            # 基本的な特徴量比較
            score = 0.0
            total_weight = 0.0
            
            # 輪郭数の類似度
            if 'contour_count' in features1 and 'contour_count' in features2:
                diff = abs(features1['contour_count'] - features2['contour_count'])
                max_count = max(features1['contour_count'], features2['contour_count'], 1)
                score += (1.0 - diff / max_count) * 0.3
                total_weight += 0.3
            
            # 水平線・垂直線の類似度
            for line_type in ['horizontal_lines', 'vertical_lines']:
                if line_type in features1 and line_type in features2:
                    diff = abs(features1[line_type] - features2[line_type])
                    max_lines = max(features1[line_type], features2[line_type], 1)
                    score += (1.0 - diff / max_lines) * 0.2
                    total_weight += 0.2
            
            # レイアウト複雑度の類似度
            if 'layout_complexity' in features1 and 'layout_complexity' in features2:
                diff = abs(features1['layout_complexity'] - features2['layout_complexity'])
                score += (1.0 - diff) * 0.3
                total_weight += 0.3
            
            return score / total_weight if total_weight > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _analyze_with_template(self, image_path: str, template: DrawingTemplate, request: DrawingAnalysisRequest) -> Dict[str, Any]:
        """テンプレートを使用した解析"""
        
        # 画像をbase64エンコード
        image_data = self._encode_image(image_path)
        
        # テンプレート専用プロンプト
        template_prompt = f"""
{self.base_prompt}

## テンプレート情報
テンプレート名: {template.template_name}
製品タイプ: {template.product_type.value}
図面向き: {template.orientation.value}

## 抽出対象フィールド
{template.generate_extraction_prompt()}

## 注意事項
- このテンプレートの学習データに基づいて解析してください
- フィールドの想定位置を考慮してください
- テンプレートで定義された信頼度閾値: {template.confidence_threshold}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=request.custom_prompts.get('model', 'gpt-4-vision-preview'),
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": template_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=2500,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            result['template_id'] = template.template_id
            result['template_confidence'] = 0.9
            
            return result
            
        except Exception as e:
            self.logger.error(f"テンプレート解析エラー: {e}")
            # フォールバック: テンプレートなしで解析
            return self._analyze_without_template(image_path, request)
    
    def _analyze_without_template(self, image_path: str, request: DrawingAnalysisRequest) -> Dict[str, Any]:
        """テンプレートなしの新規解析"""
        
        # 画像をbase64エンコード
        image_data = self._encode_image(image_path)
        
        # 新規解析プロンプト
        analysis_prompt = f"""
{self.base_prompt}

## 解析リクエスト情報
製品タイプ: {request.product_type.value if request.product_type else '不明'}
高精度モード: {request.high_precision_mode}
寸法抽出: {request.extract_dimensions}
材質抽出: {request.extract_materials}
仕様抽出: {request.extract_specifications}

## 対象フィールド
{', '.join(request.target_fields) if request.target_fields else '全フィールド'}

## 解析手順
1. 図面の向きと種類を判定
2. 図面枠とタイトルブロックを特定
3. 主要な図形・形状を認識
4. テキスト領域を特定して文字認識
5. 寸法線と寸法値を抽出
6. 材質・仕様情報を特定
7. 各フィールドの信頼度を評価

信頼度閾値: {request.confidence_threshold}
"""
        
        try:
            response = self.client.chat.completions.create(
                model='gpt-4-vision-preview',
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=3000,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            result['is_new_analysis'] = True
            result['template_id'] = None
            
            return result
            
        except Exception as e:
            self.logger.error(f"新規解析エラー: {e}")
            raise
    
    def _post_process_results(self, raw_results: Dict[str, Any], drawing_info: A4DrawingInfo, 
                            request: DrawingAnalysisRequest, template: Optional[DrawingTemplate]) -> AnalysisResult:
        """結果の後処理"""
        
        extracted_data = {}
        
        # 抽出データの変換
        for field_name, field_data in raw_results.get('extracted_data', {}).items():
            
            # ExtractionResult オブジェクトに変換
            extraction_result = ExtractionResult(
                field_name=field_name,
                value=field_data.get('value', ''),
                confidence=field_data.get('confidence', 0.0),
                position=field_data.get('position'),
                extraction_method=ExtractionMethod(field_data.get('extraction_method', 'ai_vision')),
                field_type=FieldType(field_data.get('field_type', 'text')),
                raw_value=field_data.get('raw_value')
            )
            
            # テンプレートによるバリデーション
            if template and field_name in template.fields:
                template_field = template.fields[field_name]
                is_valid, errors = template_field.validate_value(extraction_result.value)
                extraction_result.validation_status = "valid" if is_valid else "invalid"
                if errors:
                    extraction_result.notes = "; ".join(errors)
            
            extracted_data[field_name] = extraction_result
        
        # A4情報の追加
        a4_info = {
            'orientation': drawing_info.orientation,
            'is_valid_a4': drawing_info.is_valid_a4,
            'dpi': drawing_info.dpi,
            'scale_factor': drawing_info.scale_factor,
            'width': drawing_info.width,
            'height': drawing_info.height
        }
        
        # AnalysisResult オブジェクト作成
        analysis_result = AnalysisResult(
            drawing_path=request.drawing_info.file_path,
            extracted_data=extracted_data,
            template_id=template.template_id if template else None,
            product_type=request.product_type.value if request.product_type else None,
            a4_info=a4_info,
            metadata={
                'request_options': request.to_dict(),
                'raw_results': raw_results,
                'quality_assessment': raw_results.get('quality_assessment', {})
            }
        )
        
        return analysis_result
    
    def _save_analysis_result(self, analysis_result: AnalysisResult):
        """解析結果をデータベースに保存"""
        
        try:
            # データベース保存用の辞書に変換
            result_data = {
                'drawing_path': analysis_result.drawing_path,
                'template_id': analysis_result.template_id,
                'product_type': analysis_result.product_type,
                'extracted_data': {
                    name: result.to_dict() 
                    for name, result in analysis_result.extracted_data.items()
                },
                'confidence_score': analysis_result.confidence_score,
                'processing_time': analysis_result.processing_metrics.processing_time,
                'a4_info': analysis_result.a4_info
            }
            
            result_id = self.db_manager.save_analysis_result(result_data)
            analysis_result.result_id = result_id
            
            # テンプレート使用統計の更新
            if analysis_result.template_id:
                field_confidences = {
                    name: result.confidence
                    for name, result in analysis_result.extracted_data.items()
                }
                
                # テンプレート統計更新（簡略化）
                self.db_manager.record_system_metric(
                    'template_usage',
                    analysis_result.confidence_score,
                    {
                        'template_id': analysis_result.template_id,
                        'field_count': len(analysis_result.extracted_data),
                        'processing_time': analysis_result.processing_metrics.processing_time
                    }
                )
            
        except Exception as e:
            self.logger.error(f"解析結果保存エラー: {e}")
    
    def _encode_image(self, image_path: str) -> str:
        """画像をbase64エンコード"""
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def batch_analyze(self, image_paths: List[str], **options) -> List[AnalysisResult]:
        """複数図面の一括解析"""
        
        results = []
        
        for image_path in image_paths:
            try:
                result = self.analyze_drawing(image_path, **options)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"バッチ解析エラー ({image_path}): {e}")
                # エラー結果も含める
                error_result = AnalysisResult(
                    drawing_path=image_path,
                    extracted_data={},
                    metadata={'error': str(e)}
                )
                results.append(error_result)
        
        return results
    
    def get_analysis_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """解析履歴を取得"""
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT result_id, drawing_path, template_id, product_type,
                       confidence_score, processing_time, created_at
                FROM analysis_results
                ORDER BY created_at DESC
                LIMIT ?
                """, (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'result_id': row[0],
                        'drawing_path': row[1],
                        'template_id': row[2],
                        'product_type': row[3],
                        'confidence_score': row[4],
                        'processing_time': row[5],
                        'created_at': row[6]
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"履歴取得エラー: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """解析統計を取得"""
        
        return self.db_manager.get_analysis_statistics()


def create_agent_from_config(config) -> DrawingAnalysisAgent:
    """設定からエージェントを作成"""
    
    openai_config = config.get_openai_config()
    database_config = config.get_database_config()
    
    api_key = openai_config.get('api_key')
    if not api_key or api_key == 'your-openai-api-key-here':
        raise ValueError("OpenAI APIキーが設定されていません")
    
    return DrawingAnalysisAgent(
        api_key=api_key,
        database_path=database_config.get('path')
    )