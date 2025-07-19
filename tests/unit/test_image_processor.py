"""A4ImageProcessorのユニットテスト"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import cv2

from src.utils.image_processor import A4ImageProcessor


class TestA4ImageProcessor:
    """A4ImageProcessorのテストクラス"""
    
    @pytest.fixture
    def processor(self):
        """テスト用のプロセッサインスタンス"""
        return A4ImageProcessor()
    
    @pytest.fixture
    def mock_a4_image(self):
        """A4サイズのモック画像（300DPI）"""
        # A4サイズ: 210x297mm at 300DPI = 2480x3508 pixels
        return np.zeros((3508, 2480, 3), dtype=np.uint8)
    
    def test_初期化(self, processor):
        """プロセッサの初期化をテスト"""
        assert processor.A4_WIDTH_MM == 210
        assert processor.A4_HEIGHT_MM == 297
        assert processor.STANDARD_DPI == 300
        assert processor.SIZE_TOLERANCE_MM == 2
    
    def test_a4サイズ検出_正常なA4縦向き(self, processor):
        """正常なA4縦向き図面のサイズ検出をテスト"""
        # Given: A4縦向きのサイズ（300DPI）
        width = 2480  # 210mm at 300DPI
        height = 3508  # 297mm at 300DPI
        dpi = 300
        
        # When
        is_valid, scale_factor = processor._check_a4_size(width, height, dpi)
        
        # Then
        assert is_valid == True
        assert abs(scale_factor - 1.0) < 0.01  # スケール係数は1.0に近い
    
    def test_a4サイズ検出_正常なA4横向き(self, processor):
        """正常なA4横向き図面のサイズ検出をテスト"""
        # Given: A4横向きのサイズ（300DPI）
        width = 3508  # 297mm at 300DPI
        height = 2480  # 210mm at 300DPI
        dpi = 300
        
        # When
        is_valid, scale_factor = processor._check_a4_size(width, height, dpi)
        
        # Then
        assert is_valid == True
        assert abs(scale_factor - 1.0) < 0.01
    
    def test_a4サイズ検出_許容誤差内(self, processor):
        """許容誤差内のA4サイズ検出をテスト"""
        # Given: わずかに小さいA4サイズ（208x295mm）
        width = 2457  # 208mm at 300DPI
        height = 3484  # 295mm at 300DPI
        dpi = 300
        
        # When
        is_valid, scale_factor = processor._check_a4_size(width, height, dpi)
        
        # Then
        assert is_valid == True
    
    def test_a4サイズ検出_許容誤差外(self, processor):
        """許容誤差外のサイズ検出をテスト"""
        # Given: A3サイズ（297x420mm）
        width = 3508  # 297mm at 300DPI
        height = 4961  # 420mm at 300DPI
        dpi = 300
        
        # When
        is_valid, scale_factor = processor._check_a4_size(width, height, dpi)
        
        # Then
        assert is_valid == False
    
    def test_dpi検出_正常値(self, processor, mock_a4_image):
        """正常なDPI値の検出をテスト"""
        # Given
        with patch('cv2.imread', return_value=mock_a4_image):
            with patch.object(processor, '_extract_dpi_from_metadata', return_value=300):
                # When
                dpi = processor._detect_dpi('test.png')
                
                # Then
                assert dpi == 300
    
    def test_dpi検出_メタデータなし(self, processor, mock_a4_image):
        """メタデータがない場合のDPI検出をテスト"""
        # Given
        with patch('cv2.imread', return_value=mock_a4_image):
            with patch.object(processor, '_extract_dpi_from_metadata', return_value=None):
                # When
                dpi = processor._detect_dpi('test.png')
                
                # Then
                assert dpi == 300  # デフォルト値
    
    @patch('cv2.imread')
    def test_画像読み込みエラー(self, mock_imread, processor):
        """画像読み込みエラーのテスト"""
        # Given
        mock_imread.return_value = None
        
        # When/Then
        with pytest.raises(ValueError, match="画像を読み込めませんでした"):
            processor.analyze_a4_drawing('nonexistent.png')
    
    def test_画質評価_高品質(self, processor):
        """高品質画像の品質評価をテスト"""
        # Given: 高コントラストな画像
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # When
        with patch.object(processor, '_calculate_contrast', return_value=0.8):
            with patch.object(processor, '_calculate_sharpness', return_value=0.9):
                with patch.object(processor, '_calculate_noise_level', return_value=0.1):
                    quality_score = processor._evaluate_quality(image)
        
        # Then
        assert quality_score > 0.7
    
    def test_画質評価_低品質(self, processor):
        """低品質画像の品質評価をテスト"""
        # Given: 低コントラストな画像
        image = np.full((100, 100, 3), 128, dtype=np.uint8)
        
        # When
        with patch.object(processor, '_calculate_contrast', return_value=0.2):
            with patch.object(processor, '_calculate_sharpness', return_value=0.3):
                with patch.object(processor, '_calculate_noise_level', return_value=0.7):
                    quality_score = processor._evaluate_quality(image)
        
        # Then
        assert quality_score < 0.5
    
    def test_画像強調処理(self, processor):
        """画像強調処理のテスト"""
        # Given: グレースケール画像
        image = np.random.randint(50, 200, (100, 100), dtype=np.uint8)
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        
        # When
        enhanced = processor._enhance_image(image)
        
        # Then
        assert enhanced.shape == image.shape
        assert enhanced.dtype == np.uint8
        # 強調後の画像は元画像と異なるはず
        assert not np.array_equal(enhanced, image)