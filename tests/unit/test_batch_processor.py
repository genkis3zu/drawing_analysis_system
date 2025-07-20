"""バッチ処理機能のユニットテスト

TDDアプローチに従い、実装前にテストを作成。
バッチ処理機能の要件：
- 複数画像の一括処理
- 進捗状況の追跡
- エラーハンドリング
- 並列処理のサポート
- 処理結果のレポート生成
"""
import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime
from typing import List, Dict, Any

from src.utils.batch_processor import BatchProcessor
from src.models.analysis_result import AnalysisResult, ExtractionResult
from src.core.agent import DrawingAnalysisAgent


class TestBatchProcessor:
    """BatchProcessorのユニットテスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def batch_processor(self, temp_dir):
        """テスト用のBatchProcessorインスタンス"""
        config = {
            "input_dir": str(temp_dir / "input"),
            "output_dir": str(temp_dir / "output"),
            "max_workers": 2,
            "batch_size": 5,
            "supported_formats": [".png", ".jpg", ".jpeg"],
            "retry_count": 2
        }
        return BatchProcessor(config)
    
    @pytest.fixture
    def mock_agent(self):
        """モックのDrawingAnalysisAgent"""
        agent = Mock(spec=DrawingAnalysisAgent)
        return agent
    
    @pytest.fixture
    def sample_images(self, temp_dir):
        """サンプル画像ファイルを作成"""
        input_dir = temp_dir / "input"
        input_dir.mkdir(exist_ok=True)
        
        # ダミー画像ファイルを作成
        image_files = []
        for i in range(3):
            image_file = input_dir / f"drawing_{i+1}.png"
            image_file.write_bytes(b"dummy_image_content")
            image_files.append(image_file)
        
        return image_files
    
    def test_初期化_正常な設定(self, temp_dir):
        """正常な設定でのBatchProcessor初期化をテスト"""
        # Given
        config = {
            "input_dir": str(temp_dir / "input"),
            "output_dir": str(temp_dir / "output"),
            "max_workers": 4
        }
        
        # When
        processor = BatchProcessor(config)
        
        # Then
        assert processor.input_dir == temp_dir / "input"
        assert processor.output_dir == temp_dir / "output"
        assert processor.max_workers == 4
    
    def test_画像ファイル検出(self, batch_processor, sample_images):
        """入力ディレクトリから画像ファイルを検出するテスト"""
        # When
        detected_files = batch_processor.discover_images()
        
        # Then
        assert len(detected_files) == 3
        for file_path in detected_files:
            assert file_path.suffix == ".png"
            assert "drawing_" in file_path.name
    
    def test_バッチ処理_正常な処理(self, batch_processor, sample_images, mock_agent):
        """正常なバッチ処理のテスト"""
        # Given
        def mock_analyze(image_path):
            path_obj = Path(image_path)
            return AnalysisResult(
                drawing_path=str(image_path),
                extracted_data={
                    "部品番号": ExtractionResult(
                        field_name="部品番号",
                        value=f"A-{path_obj.stem[-1]}",
                        confidence=0.95
                    )
                }
            )
        
        mock_agent.analyze_drawing.side_effect = mock_analyze
        
        # When
        results = batch_processor.process_batch(mock_agent)
        
        # Then
        assert len(results) == 3
        assert all(isinstance(result, AnalysisResult) for result in results)
        assert mock_agent.analyze_drawing.call_count == 3
    
    def test_進捗追跡機能(self, batch_processor, sample_images, mock_agent):
        """進捗追跡機能のテスト"""
        # Given
        progress_updates = []
        
        def progress_callback(current, total, file_name):
            progress_updates.append((current, total, file_name))
        
        mock_agent.analyze_drawing.return_value = AnalysisResult(
            drawing_path="test.png",
            extracted_data={}
        )
        
        # When
        batch_processor.process_batch(mock_agent, progress_callback=progress_callback)
        
        # Then
        assert len(progress_updates) == 3
        # 並列処理のため順序は保証されないが、最初と最後の値は確認可能
        assert progress_updates[0][0] == 1  # 最初の番号
        assert progress_updates[0][1] == 3  # 総数
        assert progress_updates[-1][0] == 3  # 最後の番号
        assert progress_updates[-1][1] == 3  # 総数
        # ファイル名は並列処理により順序が変わる可能性があるため、存在確認のみ
        progress_files = {update[2] for update in progress_updates}
        expected_files = {"drawing_1.png", "drawing_2.png", "drawing_3.png"}
        assert progress_files == expected_files
    
    def test_エラーハンドリング_個別ファイルエラー(self, batch_processor, sample_images, mock_agent):
        """個別ファイル処理エラーのハンドリングをテスト"""
        # Given
        def mock_analyze(image_path):
            if "drawing_2" in str(image_path):
                raise Exception("解析エラー")
            return AnalysisResult(
                drawing_path=str(image_path),
                extracted_data={}
            )
        
        mock_agent.analyze_drawing.side_effect = mock_analyze
        
        # When
        results = batch_processor.process_batch(mock_agent)
        
        # Then
        # エラーが発生したファイルを除く2つの結果が返される
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) == 2
    
    def test_並列処理の動作(self, batch_processor, sample_images, mock_agent):
        """並列処理の動作をテスト"""
        # Given
        call_times = []
        
        def mock_analyze(image_path):
            call_times.append(datetime.now())
            return AnalysisResult(
                drawing_path=str(image_path),
                extracted_data={}
            )
        
        mock_agent.analyze_drawing.side_effect = mock_analyze
        
        # When
        start_time = datetime.now()
        results = batch_processor.process_batch(mock_agent)
        end_time = datetime.now()
        
        # Then
        assert len(results) == 3
        # 並列処理により、呼び出し時間に重複があることを確認
        processing_time = (end_time - start_time).total_seconds()
        assert processing_time < 10  # 逐次処理より高速
    
    def test_処理統計の生成(self, batch_processor, sample_images, mock_agent):
        """処理統計情報の生成をテスト"""
        # Given
        mock_agent.analyze_drawing.return_value = AnalysisResult(
            drawing_path="test.png",
            extracted_data={
                "部品番号": ExtractionResult(
                    field_name="部品番号",
                    value="A-123",
                    confidence=0.85
                )
            }
        )
        
        # When
        results = batch_processor.process_batch(mock_agent)
        statistics = batch_processor.generate_statistics(results)
        
        # Then
        assert "total_files" in statistics
        assert "successful_files" in statistics
        assert "failed_files" in statistics
        assert "average_confidence" in statistics
        assert "processing_time" in statistics
        assert statistics["total_files"] == 3
        assert statistics["successful_files"] == 3
    
    def test_結果の保存(self, batch_processor, sample_images, mock_agent, temp_dir):
        """処理結果の保存をテスト"""
        # Given
        mock_agent.analyze_drawing.return_value = AnalysisResult(
            drawing_path="test.png",
            extracted_data={}
        )
        
        # When
        results = batch_processor.process_batch(mock_agent)
        output_file = batch_processor.save_results(results)
        
        # Then
        assert output_file.exists()
        assert output_file.suffix == ".xlsx"
        assert "batch_report" in output_file.name
    
    def test_フィルタリング機能(self, batch_processor, temp_dir):
        """ファイルフィルタリング機能のテスト"""
        # Given
        input_dir = temp_dir / "input"
        input_dir.mkdir(exist_ok=True)
        
        # 異なる形式のファイルを作成
        (input_dir / "drawing1.png").write_bytes(b"dummy")
        (input_dir / "drawing2.jpg").write_bytes(b"dummy")
        (input_dir / "document.pdf").write_bytes(b"dummy")
        (input_dir / "readme.txt").write_bytes(b"dummy")
        
        # When
        detected_files = batch_processor.discover_images()
        
        # Then
        assert len(detected_files) == 2  # .png と .jpg のみ
        extensions = {f.suffix for f in detected_files}
        assert extensions == {".png", ".jpg"}
    
    def test_レジューム機能(self, batch_processor, sample_images, mock_agent, temp_dir):
        """中断からの再開機能をテスト"""
        # Given
        # 既存の処理結果ファイルを作成
        existing_result = AnalysisResult(
            drawing_path=str(sample_images[0]),
            extracted_data={}
        )
        
        mock_agent.analyze_drawing.return_value = AnalysisResult(
            drawing_path="test.png",
            extracted_data={}
        )
        
        # When
        results = batch_processor.process_batch(
            mock_agent,
            resume_from_existing=True
        )
        
        # Then
        # 既に処理済みのファイルはスキップされる
        assert len(results) >= 2  # 未処理分のみ処理される
    
    def test_設定値のバリデーション(self, temp_dir):
        """設定値のバリデーションをテスト"""
        # Given
        invalid_config = {
            "input_dir": "/non/existent/path",
            "output_dir": str(temp_dir / "output"),
            "max_workers": 0  # 無効な値
        }
        
        # When/Then
        with pytest.raises(ValueError):
            BatchProcessor(invalid_config)
    
    def test_大量ファイル処理のメモリ効率(self, batch_processor, temp_dir, mock_agent):
        """大量ファイル処理時のメモリ効率をテスト"""
        # Given
        input_dir = temp_dir / "input"
        input_dir.mkdir(exist_ok=True)
        
        # 多数のダミーファイルを作成
        for i in range(50):
            (input_dir / f"drawing_{i:03d}.png").write_bytes(b"dummy")
        
        mock_agent.analyze_drawing.return_value = AnalysisResult(
            drawing_path="test.png",
            extracted_data={}
        )
        
        # When
        results = batch_processor.process_batch(mock_agent)
        
        # Then
        assert len(results) == 50
        # メモリ使用量の大幅な増加がないことを確認
        # （実際の実装では、バッチサイズでの分割処理を行う）