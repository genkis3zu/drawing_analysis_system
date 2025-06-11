# src/utils/batch_processor.py

import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from ..core.agent import DrawingAnalysisAgent
from ..models.drawing import ProductType
from ..utils.file_handler import FileHandler

class BatchProcessor:
    """バッチ処理を管理するクラス"""
    
    def __init__(
        self,
        agent: DrawingAnalysisAgent,
        batch_size: int = 10,
        max_workers: int = 4,
        timeout_minutes: int = 5,
        retry_attempts: int = 2
    ):
        self.agent = agent
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.timeout_minutes = timeout_minutes
        self.retry_attempts = retry_attempts
        self.logger = logging.getLogger(__name__)
    
    def process_directory(
        self,
        input_directory: str,
        output_directory: str,
        auto_product_type: bool = True,
        default_product_type: Optional[str] = None,
        error_handling: str = "続行",
        output_formats: List[str] = ["JSON", "Excel"],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """ディレクトリ内の図面を一括処理"""
        
        start_time = time.time()
        
        try:
            # 入力ファイル取得
            input_files = self._get_input_files(input_directory)
            total_files = len(input_files)
            
            if total_files == 0:
                return {
                    'total_files': 0,
                    'successful_files': 0,
                    'error_files': 0,
                    'total_time': 0,
                    'file_results': []
                }
            
            # 出力ディレクトリ作成
            output_path = Path(output_directory)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 進捗情報初期化
            progress_info = {
                'total_files': total_files,
                'processed_files': 0,
                'successful': 0,
                'errors': 0,
                'start_time': time.time(),
                'current_file': None
            }
            
            # 結果格納用
            results = {
                'total_files': total_files,
                'successful_files': 0,
                'error_files': 0,
                'total_time': 0,
                'file_results': []
            }
            
            # バッチ処理実行
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for i in range(0, total_files, self.batch_size):
                    batch_files = input_files[i:i + self.batch_size]
                    
                    for file_path in batch_files:
                        future = executor.submit(
                            self._process_single_file,
                            file_path,
                            output_directory,
                            auto_product_type,
                            default_product_type
                        )
                        futures.append(future)
                
                # 結果取得
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=self.timeout_minutes * 60)
                        results['file_results'].append(result)
                        
                        if result['success']:
                            results['successful_files'] += 1
                        else:
                            results['error_files'] += 1
                        
                        # 進捗更新
                        progress_info['processed_files'] += 1
                        progress_info['successful'] = results['successful_files']
                        progress_info['errors'] = results['error_files']
                        progress_info['current_file'] = result['file_path']
                        
                        if progress_callback:
                            progress_callback(progress_info)
                        
                        # エラー処理
                        if not result['success'] and error_handling == "停止":
                            raise ValueError(f"処理エラー: {result['error']}")
                    
                    except Exception as e:
                        self.logger.error(f"処理エラー: {e}")
                        if error_handling == "停止":
                            raise
            
            # 結果出力
            if results['successful_files'] > 0:
                self._export_results(results, output_directory, output_formats)
            
            # 処理時間計算
            results['total_time'] = time.time() - start_time
            
            return results
        
        except Exception as e:
            self.logger.error(f"バッチ処理エラー: {e}")
            return {
                'total_files': total_files if 'total_files' in locals() else 0,
                'successful_files': results['successful_files'] if 'results' in locals() else 0,
                'error_files': results['error_files'] if 'results' in locals() else 0,
                'total_time': time.time() - start_time,
                'file_results': results.get('file_results', []) if 'results' in locals() else [],
                'error': str(e)
            }
    
    def _get_input_files(self, input_directory: str) -> List[str]:
        """入力ファイルのリストを取得"""
        
        input_path = Path(input_directory)
        if not input_path.exists():
            raise ValueError(f"入力ディレクトリが存在しません: {input_directory}")
        
        supported_formats = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff']
        files = []
        
        for ext in supported_formats:
            files.extend([str(f) for f in input_path.glob(f"*{ext}")])
            files.extend([str(f) for f in input_path.glob(f"*{ext.upper()}")])
        
        return sorted(files)
    
    def _process_single_file(
        self,
        file_path: str,
        output_directory: str,
        auto_product_type: bool,
        default_product_type: Optional[str]
    ) -> Dict[str, Any]:
        """単一ファイルを処理"""
        
        start_time = time.time()
        attempts = 0
        
        while attempts <= self.retry_attempts:
            try:
                # 製品タイプ判定
                if auto_product_type:
                    product_type = self._detect_product_type(file_path)
                else:
                    product_type = ProductType(default_product_type) if default_product_type else None
                
                # 解析実行
                results = self.agent.analyze_drawing(
                    file_path,
                    product_type=product_type,
                    high_precision_mode=True
                )
                
                # 結果保存
                output_path = Path(output_directory) / f"{Path(file_path).stem}_results.json"
                FileHandler.save_json(results.to_dict(), str(output_path))
                
                return {
                    'file_path': file_path,
                    'success': True,
                    'confidence_score': results.confidence_score,
                    'processing_time': time.time() - start_time
                }
            
            except Exception as e:
                attempts += 1
                if attempts > self.retry_attempts:
                    return {
                        'file_path': file_path,
                        'success': False,
                        'error': str(e),
                        'processing_time': time.time() - start_time
                    }
                time.sleep(1)  # リトライ前に待機
    
    def _detect_product_type(self, file_path: str) -> Optional[ProductType]:
        """ファイル名から製品タイプを推定"""
        
        filename = Path(file_path).stem.lower()
        
        if any(keyword in filename for keyword in ['機械', 'part', '部品']):
            return ProductType.MECHANICAL_PART
        elif any(keyword in filename for keyword in ['電気', 'electric']):
            return ProductType.ELECTRICAL_COMPONENT
        elif any(keyword in filename for keyword in ['組立', 'assembly']):
            return ProductType.ASSEMBLY_DRAWING
        elif any(keyword in filename for keyword in ['配線', 'wiring']):
            return ProductType.WIRING_DIAGRAM
        
        return None
    
    def _export_results(
        self,
        results: Dict[str, Any],
        output_directory: str,
        output_formats: List[str]
    ):
        """結果をエクスポート"""
        
        try:
            output_path = Path(output_directory)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if "JSON" in output_formats:
                json_path = output_path / f"batch_results_{timestamp}.json"
                FileHandler.save_json(results, str(json_path))
            
            if "Excel" in output_formats:
                excel_path = output_path / f"batch_results_{timestamp}.xlsx"
                FileHandler.save_excel(results, str(excel_path))
            
            if "CSV" in output_formats:
                csv_path = output_path / f"batch_results_{timestamp}.csv"
                FileHandler.save_csv(results, str(csv_path))
        
        except Exception as e:
            self.logger.error(f"結果エクスポートエラー: {e}")
            raise
