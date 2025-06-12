import unittest
import os
import tempfile
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

from src.utils.image_processor import A4ImageProcessor, is_valid_image, ensure_uint8, ensure_float32

class TestA4ImageProcessor(unittest.TestCase):
    """A4ImageProcessorのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.processor = A4ImageProcessor()
        
        # テスト用の一時ディレクトリ
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # テスト用のA4画像を作成（300DPI、A4サイズ）
        self.a4_portrait_path = os.path.join(self.temp_dir.name, "a4_portrait.png")
        self.a4_landscape_path = os.path.join(self.temp_dir.name, "a4_landscape.png")
        self.non_a4_path = os.path.join(self.temp_dir.name, "non_a4.png")
        
        # A4縦向き画像（300DPI、210×297mm）
        a4_portrait = np.ones((self.processor.A4_HEIGHT_PX, self.processor.A4_WIDTH_PX, 3), dtype=np.uint8) * 255
        cv2.imwrite(self.a4_portrait_path, a4_portrait)
        
        # A4横向き画像（300DPI、297×210mm）
        a4_landscape = np.ones((self.processor.A4_WIDTH_PX, self.processor.A4_HEIGHT_PX, 3), dtype=np.uint8) * 255
        cv2.imwrite(self.a4_landscape_path, a4_landscape)
        
        # 非A4画像
        non_a4 = np.ones((800, 600, 3), dtype=np.uint8) * 255
        cv2.imwrite(self.non_a4_path, non_a4)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.temp_dir.cleanup()
    
    def test_analyze_a4_drawing_portrait(self):
        """A4縦向き図面の解析テスト"""
        result = self.processor.analyze_a4_drawing(self.a4_portrait_path)
        
        self.assertEqual(result.width, self.processor.A4_WIDTH_PX)
        self.assertEqual(result.height, self.processor.A4_HEIGHT_PX)
        self.assertEqual(result.dpi, self.processor.STANDARD_DPI)
        self.assertEqual(result.orientation, "portrait")
        self.assertTrue(result.is_valid_a4)
        self.assertAlmostEqual(result.scale_factor, 1.0, places=2)
    
    def test_analyze_a4_drawing_landscape(self):
        """A4横向き図面の解析テスト"""
        result = self.processor.analyze_a4_drawing(self.a4_landscape_path)
        
        self.assertEqual(result.width, self.processor.A4_HEIGHT_PX)
        self.assertEqual(result.height, self.processor.A4_WIDTH_PX)
        self.assertEqual(result.dpi, self.processor.STANDARD_DPI)
        self.assertEqual(result.orientation, "landscape")
        self.assertTrue(result.is_valid_a4)
        self.assertAlmostEqual(result.scale_factor, 1.0, places=2)
    
    def test_analyze_non_a4_drawing(self):
        """非A4図面の解析テスト"""
        result = self.processor.analyze_a4_drawing(self.non_a4_path)
        
        self.assertEqual(result.width, 600)
        self.assertEqual(result.height, 800)
        self.assertEqual(result.dpi, self.processor.STANDARD_DPI)
        self.assertEqual(result.orientation, "portrait")
        self.assertFalse(result.is_valid_a4)
        self.assertNotEqual(result.scale_factor, 1.0)
    
    def test_optimize_a4_drawing(self):
        """A4図面の最適化テスト"""
        # A4図面の場合は最適化せずに元のパスを返す
        result_path = self.processor.optimize_a4_drawing(self.a4_portrait_path)
        self.assertEqual(result_path, self.a4_portrait_path)
        
        # 非A4図面の場合は最適化して新しいパスを返す
        result_path = self.processor.optimize_a4_drawing(self.non_a4_path)
        self.assertNotEqual(result_path, self.non_a4_path)
        self.assertTrue(os.path.exists(result_path))
        
        # 最適化された画像がA4サイズに近いことを確認
        optimized_image = cv2.imread(result_path)
        height, width = optimized_image.shape[:2]
        
        # 縦横比がA4に近いことを確認
        aspect_ratio = width / height
        a4_ratio = self.processor.A4_WIDTH_MM / self.processor.A4_HEIGHT_MM
        self.assertAlmostEqual(aspect_ratio, a4_ratio, places=1)
    
    def test_extract_layout_features(self):
        """レイアウト特徴抽出テスト"""
        # 簡単な図形を含む画像を作成
        test_image_path = os.path.join(self.temp_dir.name, "test_layout.png")
        image = np.ones((1000, 700, 3), dtype=np.uint8) * 255
        
        # 長方形を描画
        cv2.rectangle(image, (100, 100), (600, 900), (0, 0, 0), 2)
        
        # 水平線と垂直線を描画
        cv2.line(image, (100, 300), (600, 300), (0, 0, 0), 2)  # 水平線
        cv2.line(image, (350, 100), (350, 900), (0, 0, 0), 2)  # 垂直線
        
        # テキスト領域を模擬
        cv2.rectangle(image, (150, 150), (300, 200), (0, 0, 0), 1)
        cv2.rectangle(image, (400, 150), (550, 200), (0, 0, 0), 1)
        
        cv2.imwrite(test_image_path, image)
        
        # 特徴抽出
        features = self.processor.extract_layout_features(test_image_path)
        
        # 基本的な特徴が含まれていることを確認
        self.assertIn('contour_count', features)
        self.assertIn('horizontal_lines', features)
        self.assertIn('vertical_lines', features)
        self.assertIn('text_regions', features)
        self.assertIn('has_border', features)
        self.assertIn('complexity_score', features)
        
        # 水平線と垂直線が検出されていることを確認
        self.assertGreater(features['horizontal_lines'], 0)
        self.assertGreater(features['vertical_lines'], 0)
        
        # 複雑度スコアが0-1の範囲内であることを確認
        self.assertGreaterEqual(features['complexity_score'], 0.0)
        self.assertLessEqual(features['complexity_score'], 1.0)
    
    def test_is_valid_image(self):
        """画像の有効性確認テスト"""
        # 有効な画像
        valid_image = np.ones((100, 100, 3), dtype=np.uint8)
        self.assertTrue(is_valid_image(valid_image))
        
        # 無効な画像（None）
        self.assertFalse(is_valid_image(None))
        
        # 無効な画像（空の配列）
        empty_image = np.array([])
        self.assertFalse(is_valid_image(empty_image))
        
        # 無効な画像（サポートされていないデータ型）
        invalid_dtype_image = np.ones((100, 100, 3), dtype=np.int16)
        self.assertFalse(is_valid_image(invalid_dtype_image))
    
    def test_ensure_uint8(self):
        """uint8型変換テスト"""
        # float32画像（0-1）
        float_image = np.ones((100, 100, 3), dtype=np.float32) * 0.5
        uint8_image = ensure_uint8(float_image)
        
        self.assertEqual(uint8_image.dtype, np.uint8)
        self.assertEqual(uint8_image[0, 0, 0], 128)  # 0.5 * 255 = 127.5 ≈ 128
        
        # すでにuint8の画像
        original_uint8 = np.ones((100, 100, 3), dtype=np.uint8) * 100
        converted_uint8 = ensure_uint8(original_uint8)
        
        self.assertEqual(converted_uint8.dtype, np.uint8)
        self.assertEqual(converted_uint8[0, 0, 0], 100)
    
    def test_ensure_float32(self):
        """float32型変換テスト"""
        # uint8画像（0-255）
        uint8_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        float_image = ensure_float32(uint8_image)
        
        self.assertEqual(float_image.dtype, np.float32)
        self.assertAlmostEqual(float_image[0, 0, 0], 0.5, places=2)  # 128/255 = 0.5
        
        # すでにfloat32の画像
        original_float = np.ones((100, 100, 3), dtype=np.float32) * 0.5
        converted_float = ensure_float32(original_float)
        
        self.assertEqual(converted_float.dtype, np.float32)
        self.assertAlmostEqual(converted_float[0, 0, 0], 0.5, places=2)
    
    def test_calculate_quality_score(self):
        """画質スコア計算テスト"""
        # 高品質画像（白背景に黒い線）
        high_quality = np.ones((500, 500, 3), dtype=np.uint8) * 255
        cv2.line(high_quality, (100, 100), (400, 400), (0, 0, 0), 5)
        cv2.rectangle(high_quality, (200, 200), (300, 300), (0, 0, 0), 3)
        
        # CVImage型に変換
        high_quality_cv = ensure_uint8(high_quality)
        high_score = self.processor._calculate_quality_score(high_quality_cv)
        
        # 低品質画像（ノイズ多め）
        low_quality = np.ones((500, 500, 3), dtype=np.uint8) * 200
        noise = np.random.randint(0, 100, (500, 500, 3), dtype=np.uint8)
        low_quality = cv2.add(low_quality, noise)
        
        # CVImage型に変換
        low_quality_cv = ensure_uint8(low_quality)
        low_score = self.processor._calculate_quality_score(low_quality_cv)
        
        # 高品質画像のスコアが低品質画像より高いことを確認
        self.assertGreater(high_score, low_score)
        
        # スコアが0-1の範囲内であることを確認
        self.assertGreaterEqual(high_score, 0.0)
        self.assertLessEqual(high_score, 1.0)
        self.assertGreaterEqual(low_score, 0.0)
        self.assertLessEqual(low_score, 1.0)

if __name__ == '__main__':
    unittest.main()
