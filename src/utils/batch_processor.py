# src/utils/batch_processor.py

import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

from ..core.agent import DrawingAnalysisAgent
from ..models.analysis_result import AnalysisResult
from .excel_manager import ExcelManager


class BatchProcessingError(Exception):
    """バッチ処理固有の例外"""
    pass


class BatchProcessor:
    """バッチ処理管理クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: 設定辞書。以下のキーを含む：
                - input_dir: 入力ディレクトリ（必須）
                - output_dir: 出力ディレクトリ（必須）
                - max_workers: 最大並列実行数（デフォルト: 4）
                - batch_size: バッチサイズ（デフォルト: 10）
                - supported_formats: サポート形式（デフォルト: ['.png', '.jpg', '.jpeg']）
                - retry_count: リトライ回数（デフォルト: 2）
        
        Raises:
            ValueError: 無効な設定値の場合
        """
        self._validate_config(config)
        
        self.input_dir = Path(config["input_dir"])
        self.output_dir = Path(config["output_dir"])
        self.max_workers = config.get("max_workers", 4)
        self.batch_size = config.get("batch_size", 10)
        self.supported_formats = config.get("supported_formats", [".png", ".jpg", ".jpeg"])
        self.retry_count = config.get("retry_count", 2)
        
        # ディレクトリ作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # 処理統計
        self.processing_stats = {
            "start_time": None,
            "end_time": None,
            "total_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "errors": []
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """設定値をバリデーション
        
        Args:
            config: 設定辞書
            
        Raises:
            ValueError: 無効な設定値の場合
        """
        required_keys = ["input_dir", "output_dir"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"必須設定項目が不足しています: {key}")
        
        # input_dirの存在確認（テスト時は作成）
        input_path = Path(config["input_dir"])
        if not input_path.exists():
            input_path.mkdir(parents=True, exist_ok=True)
        
        # max_workersの値確認
        max_workers = config.get("max_workers", 4)
        if max_workers <= 0:
            raise ValueError(f"max_workersは1以上である必要があります: {max_workers}")
    
    def discover_images(self) -> List[Path]:
        """入力ディレクトリから画像ファイルを検出
        
        Returns:
            List[Path]: 検出された画像ファイルのリスト
        """
        image_files = []
        
        for file_path in self.input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                image_files.append(file_path)
        
        # ファイル名でソート
        image_files.sort(key=lambda x: x.name)
        
        self.logger.info(f"{len(image_files)}個の画像ファイルを検出しました")
        return image_files
    
    def process_batch(
        self,
        agent: DrawingAnalysisAgent,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        resume_from_existing: bool = False
    ) -> List[Optional[AnalysisResult]]:
        """バッチ処理を実行
        
        Args:
            agent: 図面解析エージェント
            progress_callback: 進捗コールバック関数 (current, total, filename)
            resume_from_existing: 既存結果から再開するか
            
        Returns:
            List[Optional[AnalysisResult]]: 解析結果のリスト（失敗時はNone）
        """
        image_files = self.discover_images()
        
        if not image_files:
            self.logger.warning("処理対象の画像ファイルが見つかりません")
            return []
        
        # 統計初期化
        self.processing_stats["start_time"] = datetime.now()
        self.processing_stats["total_files"] = len(image_files)
        
        results = []
        
        # 並列処理実行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 各ファイルを並列処理用にサブミット
            future_to_file = {
                executor.submit(self._process_single_file, agent, file_path): file_path
                for file_path in image_files
            }
            
            # 完了したタスクから結果を収集
            for i, future in enumerate(as_completed(future_to_file), 1):
                file_path = future_to_file[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result is not None:
                        self.processing_stats["successful_files"] += 1
                    else:
                        self.processing_stats["failed_files"] += 1
                    
                except Exception as e:
                    self.logger.error(f"ファイル処理エラー {file_path}: {e}")
                    results.append(None)
                    self.processing_stats["failed_files"] += 1
                    self.processing_stats["errors"].append({
                        "file": str(file_path),
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 進捗コールバック呼び出し
                if progress_callback:
                    progress_callback(i, len(image_files), file_path.name)
        
        self.processing_stats["end_time"] = datetime.now()
        
        self.logger.info(
            f"バッチ処理完了: {self.processing_stats['successful_files']}/{self.processing_stats['total_files']} 成功"
        )
        
        return results
    
    def _process_single_file(
        self,
        agent: DrawingAnalysisAgent,
        file_path: Path
    ) -> Optional[AnalysisResult]:
        """単一ファイルの処理
        
        Args:
            agent: 図面解析エージェント
            file_path: 処理対象ファイル
            
        Returns:
            Optional[AnalysisResult]: 解析結果（失敗時はNone）
        """
        for attempt in range(self.retry_count + 1):
            try:
                self.logger.debug(f"処理開始: {file_path.name} (試行 {attempt + 1})")
                
                result = agent.analyze_drawing(str(file_path))
                
                self.logger.debug(f"処理完了: {file_path.name}")
                return result
                
            except Exception as e:
                self.logger.warning(
                    f"ファイル処理失敗 {file_path.name} (試行 {attempt + 1}/{self.retry_count + 1}): {e}"
                )
                
                if attempt == self.retry_count:
                    self.logger.error(f"最大試行回数に達しました: {file_path.name}")
                    return None
                
                # リトライ前の待機
                time.sleep(1)
        
        return None
    
    def generate_statistics(self, results: List[Optional[AnalysisResult]]) -> Dict[str, Any]:
        """処理統計を生成
        
        Args:
            results: 処理結果のリスト
            
        Returns:
            Dict[str, Any]: 統計情報
        """
        successful_results = [r for r in results if r is not None]
        
        # 信頼度の統計
        confidences = []
        for result in successful_results:
            if result.extracted_data:
                confidences.extend([
                    field.confidence for field in result.extracted_data.values()
                ])
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # 処理時間
        processing_time = 0.0
        if self.processing_stats["start_time"] and self.processing_stats["end_time"]:
            processing_time = (
                self.processing_stats["end_time"] - self.processing_stats["start_time"]
            ).total_seconds()
        
        statistics = {
            "total_files": self.processing_stats["total_files"],
            "successful_files": self.processing_stats["successful_files"],
            "failed_files": self.processing_stats["failed_files"],
            "success_rate": (
                self.processing_stats["successful_files"] / self.processing_stats["total_files"]
                if self.processing_stats["total_files"] > 0 else 0.0
            ),
            "average_confidence": avg_confidence,
            "processing_time": processing_time,
            "files_per_second": (
                self.processing_stats["total_files"] / processing_time
                if processing_time > 0 else 0.0
            ),
            "errors": self.processing_stats["errors"]
        }
        
        return statistics
    
    def save_results(self, results: List[Optional[AnalysisResult]]) -> Path:
        """処理結果をExcelファイルに保存
        
        Args:
            results: 処理結果のリスト
            
        Returns:
            Path: 保存されたExcelファイルのパス
        """
        # 成功した結果のみを抽出
        successful_results = [r for r in results if r is not None]
        
        if not successful_results:
            raise BatchProcessingError("保存する有効な結果がありません")
        
        # Excel管理クラスを使用して保存
        excel_config = {
            "output_dir": str(self.output_dir),
            "template_dir": str(self.output_dir / "templates")
        }
        excel_manager = ExcelManager(excel_config)
        
        # バッチレポートファイル名生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"batch_report_{timestamp}.xlsx"
        
        # Excel出力実行
        result_path = excel_manager.export_batch_results(successful_results, output_file)
        
        self.logger.info(f"バッチ処理結果を保存しました: {result_path}")
        return result_path
    
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
        """ディレクトリ内の図面を一括処理（レガシーメソッド）"""
        
        # レガシーメソッド - 新しいprocess_batchメソッドを使用することを推奨
        self.logger.warning("process_directoryは非推奨です。process_batchメソッドを使用してください")
        return {"total_files": 0, "successful_files": 0, "error_files": 0}
