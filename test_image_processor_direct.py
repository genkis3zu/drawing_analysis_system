"""
A4ImageProcessorの直接テスト用スクリプト

このスクリプトは、A4ImageProcessorクラスの機能を直接テストするためのものです。
ユニットテストフレームワークを使用せず、直接メソッドを呼び出してテストします。
開発者が簡単にクラスの機能を試すために使用できます。
"""

import os
import sys
import tempfile
import numpy as np
import cv2
from pathlib import Path
import time
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# A4ImageProcessorをインポート
from src.utils.image_processor import A4ImageProcessor, ensure_uint8, ensure_float32

def create_test_images(temp_dir):
    """テスト用の画像を作成"""
    processor = A4ImageProcessor()
    
    # A4縦向き画像（300DPI、210×297mm）
    a4_portrait_path = os.path.join(temp_dir, "a4_portrait.png")
    a4_portrait = np.ones((processor.A4_HEIGHT_PX, processor.A4_WIDTH_PX, 3), dtype=np.uint8) * 255
    cv2.imwrite(a4_portrait_path, a4_portrait)
    
    # A4横向き画像（300DPI、297×210mm）
    a4_landscape_path = os.path.join(temp_dir, "a4_landscape.png")
    a4_landscape = np.ones((processor.A4_WIDTH_PX, processor.A4_HEIGHT_PX, 3), dtype=np.uint8) * 255
    cv2.imwrite(a4_landscape_path, a4_landscape)
    
    # 非A4画像
    non_a4_path = os.path.join(temp_dir, "non_a4.png")
    non_a4 = np.ones((800, 600, 3), dtype=np.uint8) * 255
    cv2.imwrite(non_a4_path, non_a4)
    
    # テスト用の図面画像（線や図形を含む）
    drawing_path = os.path.join(temp_dir, "test_drawing.png")
    drawing = np.ones((processor.A4_HEIGHT_PX, processor.A4_WIDTH_PX, 3), dtype=np.uint8) * 255
    
    # 枠線
    cv2.rectangle(drawing, (50, 50), (processor.A4_WIDTH_PX - 50, processor.A4_HEIGHT_PX - 50), (0, 0, 0), 2)
    
    # 水平線と垂直線
    cv2.line(drawing, (50, 300), (processor.A4_WIDTH_PX - 50, 300), (0, 0, 0), 1)
    cv2.line(drawing, (processor.A4_WIDTH_PX // 2, 50), (processor.A4_WIDTH_PX // 2, processor.A4_HEIGHT_PX - 50), (0, 0, 0), 1)
    
    # 円と長方形
    cv2.circle(drawing, (processor.A4_WIDTH_PX // 4, processor.A4_HEIGHT_PX // 4), 100, (0, 0, 0), 2)
    cv2.rectangle(drawing, (processor.A4_WIDTH_PX // 2 + 100, processor.A4_HEIGHT_PX // 4 - 50),
                 (processor.A4_WIDTH_PX // 2 + 300, processor.A4_HEIGHT_PX // 4 + 50), (0, 0, 0), 2)
    
    # テキスト領域を模擬
    cv2.rectangle(drawing, (100, processor.A4_HEIGHT_PX - 200), (400, processor.A4_HEIGHT_PX - 100), (0, 0, 0), 1)
    cv2.rectangle(drawing, (processor.A4_WIDTH_PX - 400, processor.A4_HEIGHT_PX - 200),
                 (processor.A4_WIDTH_PX - 100, processor.A4_HEIGHT_PX - 100), (0, 0, 0), 1)
    
    cv2.imwrite(drawing_path, drawing)
    
    return {
        'a4_portrait': a4_portrait_path,
        'a4_landscape': a4_landscape_path,
        'non_a4': non_a4_path,
        'drawing': drawing_path
    }

def test_analyze_a4_drawing(processor, image_paths):
    """A4図面解析のテスト"""
    logger.info("=== A4図面解析テスト ===")
    
    for name, path in image_paths.items():
        logger.info(f"画像: {name}")
        
        start_time = time.time()
        result = processor.analyze_a4_drawing(path)
        elapsed_time = time.time() - start_time
        
        logger.info(f"  サイズ: {result.width}x{result.height}")
        logger.info(f"  DPI: {result.dpi}")
        logger.info(f"  向き: {result.orientation}")
        logger.info(f"  A4サイズ: {'はい' if result.is_valid_a4 else 'いいえ'}")
        logger.info(f"  スケール係数: {result.scale_factor:.2f}")
        logger.info(f"  品質スコア: {result.quality_score:.2f}")
        logger.info(f"  処理時間: {elapsed_time:.3f}秒")
        logger.info("")

def test_optimize_a4_drawing(processor, image_paths):
    """A4図面最適化のテスト"""
    logger.info("=== A4図面最適化テスト ===")
    
    for name, path in image_paths.items():
        logger.info(f"画像: {name}")
        
        start_time = time.time()
        result_path = processor.optimize_a4_drawing(path)
        elapsed_time = time.time() - start_time
        
        is_optimized = result_path != path
        logger.info(f"  最適化: {'はい' if is_optimized else 'いいえ'}")
        
        if is_optimized:
            logger.info(f"  最適化パス: {result_path}")
            
            # 最適化された画像の情報
            optimized_image = cv2.imread(result_path)
            height, width = optimized_image.shape[:2]
            logger.info(f"  最適化サイズ: {width}x{height}")
            
            # 縦横比
            aspect_ratio = width / height
            a4_ratio = processor.A4_WIDTH_MM / processor.A4_HEIGHT_MM
            logger.info(f"  アスペクト比: {aspect_ratio:.3f} (A4: {a4_ratio:.3f})")
        
        logger.info(f"  処理時間: {elapsed_time:.3f}秒")
        logger.info("")

def test_extract_layout_features(processor, image_paths):
    """レイアウト特徴抽出のテスト"""
    logger.info("=== レイアウト特徴抽出テスト ===")
    
    for name, path in image_paths.items():
        logger.info(f"画像: {name}")
        
        start_time = time.time()
        features = processor.extract_layout_features(path)
        elapsed_time = time.time() - start_time
        
        logger.info(f"  輪郭数: {features['contour_count']}")
        logger.info(f"  階層深度: {features['hierarchy_depth']}")
        logger.info(f"  水平線数: {features['horizontal_lines']}")
        logger.info(f"  垂直線数: {features['vertical_lines']}")
        logger.info(f"  斜線数: {features['diagonal_lines']}")
        logger.info(f"  テキスト領域数: {features['text_regions']}")
        logger.info(f"  枠線検出: {'あり' if features['has_border'] else 'なし'}")
        logger.info(f"  対称性スコア: {features['symmetry_score']:.2f}")
        logger.info(f"  レイアウト規則性: {features['layout_regularity']:.2f}")
        logger.info(f"  複雑度スコア: {features['complexity_score']:.2f}")
        logger.info(f"  処理時間: {elapsed_time:.3f}秒")
        logger.info("")

def test_image_enhancement(processor, image_paths):
    """画像強調のテスト"""
    logger.info("=== 画像強調テスト ===")
    
    # テスト用の低品質画像を作成
    with tempfile.TemporaryDirectory() as temp_dir:
        # ノイズ画像
        noisy_path = os.path.join(temp_dir, "noisy.png")
        noisy_image = np.ones((1000, 700, 3), dtype=np.uint8) * 200
        noise = np.random.randint(0, 50, (1000, 700, 3), dtype=np.uint8)
        noisy_image = cv2.add(noisy_image, noise)
        
        # 線を追加
        cv2.line(noisy_image, (100, 100), (600, 600), (100, 100, 100), 3)
        cv2.rectangle(noisy_image, (200, 200), (500, 400), (100, 100, 100), 2)
        
        cv2.imwrite(noisy_path, noisy_image)
        
        # 画像強調
        enhanced_image = processor._enhance_image(ensure_uint8(noisy_image))
        enhanced_path = os.path.join(temp_dir, "enhanced.png")
        cv2.imwrite(enhanced_path, enhanced_image)
        
        logger.info(f"ノイズ画像: {noisy_path}")
        logger.info(f"強調画像: {enhanced_path}")
        
        # 品質スコア計算
        noisy_score = processor._calculate_quality_score(ensure_uint8(noisy_image))
        enhanced_score = processor._calculate_quality_score(enhanced_image)
        
        logger.info(f"ノイズ画像品質スコア: {noisy_score:.2f}")
        logger.info(f"強調画像品質スコア: {enhanced_score:.2f}")
        logger.info(f"品質向上: {enhanced_score - noisy_score:.2f}")
        logger.info("")

def main():
    """メイン関数"""
    logger.info("A4ImageProcessor直接テスト開始")
    
    # 一時ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"一時ディレクトリ: {temp_dir}")
        
        # テスト用画像作成
        image_paths = create_test_images(temp_dir)
        
        # A4ImageProcessorインスタンス作成
        processor = A4ImageProcessor()
        
        # 各機能のテスト
        test_analyze_a4_drawing(processor, image_paths)
        test_optimize_a4_drawing(processor, image_paths)
        test_extract_layout_features(processor, image_paths)
        test_image_enhancement(processor, image_paths)
    
    logger.info("A4ImageProcessor直接テスト終了")

if __name__ == "__main__":
    main()
