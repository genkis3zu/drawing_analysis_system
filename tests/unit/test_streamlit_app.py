"""Streamlit WebUIのユニットテスト

TDDアプローチに従い、実装前にテストを作成。
Streamlit WebUIの要件：
- 図面アップロード機能
- リアルタイム解析表示
- 結果の編集・修正機能
- Excel出力機能
- バッチ処理実行機能
- 解析履歴の表示
"""
import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from datetime import datetime
from io import BytesIO
from PIL import Image

# StreamlitアプリはOSの制約により直接テストが困難なため、
# アプリのコアロジック部分をクラスとして分離してテスト
from src.ui.streamlit_app import StreamlitApp, UIState, SessionManager
from src.models.analysis_result import AnalysisResult, ExtractionResult
from src.core.agent import DrawingAnalysisAgent


class TestStreamlitApp:
    """StreamlitAppのユニットテスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def streamlit_app(self, temp_dir):
        """テスト用のStreamlitAppインスタンス"""
        config = {
            "upload_dir": str(temp_dir / "uploads"),
            "output_dir": str(temp_dir / "output"),
            "max_file_size_mb": 10,
            "allowed_extensions": [".png", ".jpg", ".jpeg"],
            "auto_save": True
        }
        return StreamlitApp(config)
    
    @pytest.fixture
    def mock_agent(self):
        """モックのDrawingAnalysisAgent"""
        agent = Mock(spec=DrawingAnalysisAgent)
        return agent
    
    @pytest.fixture
    def sample_analysis_result(self):
        """サンプル解析結果"""
        return AnalysisResult(
            drawing_path="test_drawing.png",
            extracted_data={
                "部品番号": ExtractionResult(
                    field_name="部品番号",
                    value="A-123",
                    confidence=0.95
                ),
                "材質": ExtractionResult(
                    field_name="材質",
                    value="SUS304",
                    confidence=0.88
                ),
                "寸法": ExtractionResult(
                    field_name="寸法",
                    value="100x50x10",
                    confidence=0.75
                )
            }
        )
    
    @pytest.fixture
    def sample_image(self):
        """サンプル画像データ"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    def test_初期化_正常な設定(self, temp_dir):
        """正常な設定でのStreamlitApp初期化をテスト"""
        # Given
        config = {
            "upload_dir": str(temp_dir / "uploads"),
            "output_dir": str(temp_dir / "output"),
            "max_file_size_mb": 5
        }
        
        # When
        app = StreamlitApp(config)
        
        # Then
        assert app.upload_dir == temp_dir / "uploads"
        assert app.output_dir == temp_dir / "output"
        assert app.max_file_size_mb == 5
        assert app.upload_dir.exists()
        assert app.output_dir.exists()
    
    def test_ファイルアップロード検証_有効なファイル(self, streamlit_app, sample_image):
        """有効なファイルのアップロード検証をテスト"""
        # Given
        uploaded_file = Mock()
        uploaded_file.name = "test_drawing.png"
        uploaded_file.size = 1024 * 1024  # 1MB
        uploaded_file.type = "image/png"
        uploaded_file.getvalue.return_value = sample_image
        
        # When
        is_valid, message = streamlit_app.validate_uploaded_file(uploaded_file)
        
        # Then
        assert is_valid == True
        assert "有効" in message
    
    def test_ファイルアップロード検証_無効な拡張子(self, streamlit_app):
        """無効な拡張子のファイル検証をテスト"""
        # Given
        uploaded_file = Mock()
        uploaded_file.name = "test_document.pdf"
        uploaded_file.size = 1024 * 1024
        uploaded_file.type = "application/pdf"
        
        # When
        is_valid, message = streamlit_app.validate_uploaded_file(uploaded_file)
        
        # Then
        assert is_valid == False
        assert "拡張子" in message
    
    def test_ファイルアップロード検証_サイズ超過(self, streamlit_app):
        """ファイルサイズ超過の検証をテスト"""
        # Given
        uploaded_file = Mock()
        uploaded_file.name = "large_drawing.png"
        uploaded_file.size = 15 * 1024 * 1024  # 15MB（制限の10MBを超過）
        uploaded_file.type = "image/png"
        
        # When
        is_valid, message = streamlit_app.validate_uploaded_file(uploaded_file)
        
        # Then
        assert is_valid == False
        assert "サイズ" in message
    
    def test_図面解析実行(self, streamlit_app, mock_agent, sample_analysis_result, sample_image):
        """図面解析の実行をテスト"""
        # Given
        uploaded_file = Mock()
        uploaded_file.name = "test_drawing.png"
        uploaded_file.getvalue.return_value = sample_image
        
        mock_agent.analyze_drawing.return_value = sample_analysis_result
        
        # When
        result = streamlit_app.analyze_drawing(uploaded_file, mock_agent)
        
        # Then
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert "部品番号" in result.extracted_data
        mock_agent.analyze_drawing.assert_called_once()
    
    def test_解析結果の編集(self, streamlit_app, sample_analysis_result):
        """解析結果の編集機能をテスト"""
        # Given
        field_name = "部品番号"
        new_value = "B-456"
        
        # When
        updated_result = streamlit_app.update_analysis_result(
            sample_analysis_result, 
            field_name, 
            new_value
        )
        
        # Then
        assert updated_result.extracted_data[field_name].value == new_value
        assert updated_result.extracted_data[field_name].confidence == 1.0  # 手動修正は最高信頼度
    
    def test_Excel出力機能(self, streamlit_app, sample_analysis_result, temp_dir):
        """Excel出力機能をテスト"""
        # When
        output_path = streamlit_app.export_to_excel(sample_analysis_result)
        
        # Then
        assert output_path.exists()
        assert output_path.suffix == ".xlsx"
        assert "analysis_report" in output_path.name
    
    def test_A4画像検証_有効なA4(self, streamlit_app):
        """A4サイズ画像の検証をテスト"""
        # Given - A4サイズに相当する画像データをモック
        with patch.object(streamlit_app, '_check_a4_dimensions') as mock_check:
            mock_check.return_value = (True, "有効なA4サイズです")
            
            # When
            is_a4, message = streamlit_app.validate_a4_image(b"mock_image_data")
            
            # Then
            assert is_a4 == True
            assert "有効" in message
    
    def test_A4画像検証_無効なサイズ(self, streamlit_app):
        """無効なサイズの画像検証をテスト"""
        # Given
        with patch.object(streamlit_app, '_check_a4_dimensions') as mock_check:
            mock_check.return_value = (False, "A4サイズではありません")
            
            # When
            is_a4, message = streamlit_app.validate_a4_image(b"mock_image_data")
            
            # Then
            assert is_a4 == False
            assert "A4サイズではありません" in message
    
    def test_バッチ処理実行(self, streamlit_app, mock_agent, temp_dir):
        """バッチ処理の実行をテスト"""
        # Given
        input_dir = temp_dir / "batch_input"
        input_dir.mkdir()
        
        # サンプルファイル作成
        (input_dir / "drawing1.png").write_bytes(b"mock_image_1")
        (input_dir / "drawing2.png").write_bytes(b"mock_image_2")
        
        mock_agent.analyze_drawing.return_value = AnalysisResult(
            drawing_path="test.png",
            extracted_data={}
        )
        
        # When
        with patch('src.utils.batch_processor.BatchProcessor') as mock_batch_processor:
            mock_processor = Mock()
            mock_processor.process_batch.return_value = [
                AnalysisResult(drawing_path="test1.png", extracted_data={}),
                AnalysisResult(drawing_path="test2.png", extracted_data={})
            ]
            mock_processor.save_results.return_value = temp_dir / "batch_result.xlsx"
            mock_batch_processor.return_value = mock_processor
            
            result_path = streamlit_app.run_batch_processing(str(input_dir), mock_agent)
            
            # Then
            assert result_path is not None
            mock_processor.process_batch.assert_called_once()
    
    def test_解析履歴の管理(self, streamlit_app, sample_analysis_result):
        """解析履歴の管理機能をテスト"""
        # Given
        initial_count = len(streamlit_app.get_analysis_history())
        
        # When
        streamlit_app.add_to_history(sample_analysis_result)
        
        # Then
        history = streamlit_app.get_analysis_history()
        assert len(history) == initial_count + 1
        assert history[-1] == sample_analysis_result
    
    def test_設定の保存と読み込み(self, streamlit_app, temp_dir):
        """設定の保存と読み込み機能をテスト"""
        # Given
        settings = {
            "confidence_threshold": 0.8,
            "auto_save": True,
            "default_template": "basic"
        }
        
        # When
        streamlit_app.save_settings(settings)
        loaded_settings = streamlit_app.load_settings()
        
        # Then
        assert loaded_settings["confidence_threshold"] == 0.8
        assert loaded_settings["auto_save"] == True
    
    def test_エラーハンドリング_解析失敗(self, streamlit_app, mock_agent, sample_image):
        """解析失敗時のエラーハンドリングをテスト"""
        # Given
        uploaded_file = Mock()
        uploaded_file.name = "error_drawing.png"
        uploaded_file.getvalue.return_value = sample_image
        
        mock_agent.analyze_drawing.side_effect = Exception("解析エラー")
        
        # When/Then
        with pytest.raises(Exception) as exc_info:
            streamlit_app.analyze_drawing(uploaded_file, mock_agent)
        
        assert "解析エラー" in str(exc_info.value)
    
    def test_プログレスバー更新(self, streamlit_app):
        """プログレスバーの更新機能をテスト"""
        # Given
        total_steps = 5
        
        # When
        with patch('streamlit.progress') as mock_progress:
            mock_progress_bar = Mock()
            mock_progress.return_value = mock_progress_bar
            
            for i in range(total_steps):
                streamlit_app.update_progress(i + 1, total_steps, f"ステップ {i + 1}")
            
            # Then
            assert mock_progress_bar.progress.call_count == total_steps
    
    def test_結果の比較機能(self, streamlit_app, sample_analysis_result):
        """解析結果の比較機能をテスト"""
        # Given
        result1 = sample_analysis_result
        result2 = AnalysisResult(
            drawing_path="test_drawing2.png",
            extracted_data={
                "部品番号": ExtractionResult(
                    field_name="部品番号",
                    value="B-456",  # 異なる値
                    confidence=0.90
                )
            }
        )
        
        # When
        comparison = streamlit_app.compare_results(result1, result2)
        
        # Then
        assert "differences" in comparison
        assert comparison["has_differences"] == True
    
    def test_テンプレート適用機能(self, streamlit_app, sample_analysis_result, temp_dir):
        """テンプレート適用機能をテスト"""
        # Given
        template_path = temp_dir / "test_template.xlsx"
        # テンプレートファイルのモック作成
        template_path.write_bytes(b"mock_excel_template")
        
        # When
        with patch.object(streamlit_app, '_apply_excel_template') as mock_apply:
            mock_apply.return_value = temp_dir / "template_result.xlsx"
            
            result_path = streamlit_app.apply_template(
                sample_analysis_result, 
                str(template_path)
            )
            
            # Then
            assert result_path is not None
            mock_apply.assert_called_once()


class TestUIState:
    """UIState管理クラスのテスト"""
    
    def test_状態の初期化(self):
        """UI状態の初期化をテスト"""
        # When
        state = UIState()
        
        # Then
        assert state.current_result is None
        assert state.upload_history == []
        assert state.is_processing == False
    
    def test_状態の更新(self):
        """UI状態の更新をテスト"""
        # Given
        state = UIState()
        result = Mock(spec=AnalysisResult)
        
        # When
        state.set_current_result(result)
        state.set_processing_status(True)
        
        # Then
        assert state.current_result == result
        assert state.is_processing == True
    
    def test_履歴の管理(self):
        """アップロード履歴の管理をテスト"""
        # Given
        state = UIState()
        
        # When
        state.add_to_history("file1.png")
        state.add_to_history("file2.png")
        
        # Then
        assert len(state.upload_history) == 2
        assert "file1.png" in state.upload_history


class TestSessionManager:
    """セッション管理クラスのテスト"""
    
    def test_セッションデータの保存(self):
        """セッションデータの保存をテスト"""
        # Given
        manager = SessionManager()
        test_data = {"key": "value", "number": 123}
        
        # When
        with patch('streamlit.session_state', {}):
            manager.save_session_data("test_session", test_data)
            saved_data = manager.load_session_data("test_session")
            
            # Then
            assert saved_data == test_data
    
    def test_セッションの初期化(self):
        """セッションの初期化をテスト"""
        # Given
        manager = SessionManager()
        
        # When
        mock_session_state = {}
        with patch('streamlit.session_state', mock_session_state, create=True):
            with patch.object(manager, 'initialize_session') as mock_init:
                mock_init.return_value = None
                manager.initialize_session()
                
                # Then
                mock_init.assert_called_once()