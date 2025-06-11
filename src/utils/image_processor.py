# src/utils/image_processor.py

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import logging
from dataclasses import dataclass
from PIL import Image
import pdf2image

@dataclass
class A4DrawingInfo:
    """A4図面の情報"""
    width: int
    height: int
    dpi: int
    orientation: str
    is_valid_a4: bool
    scale_factor: float = 1.0
    quality_score: float = 0.0

class A4ImageProcessor:
    """A4図面の画像処理を行うクラス"""
    
    # A4サイズの定数（mm）
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    
    # 標準DPI
    STANDARD_DPI = 300
    
    # A4サイズのピクセル数（300DPI）
    A4_WIDTH_PX = int(A4_WIDTH_MM * STANDARD_DPI / 25.4)
    A4_HEIGHT_PX = int(A4_HEIGHT_MM * STANDARD_DPI / 25.4)
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_a4_drawing(self, file_path: str) -> A4DrawingInfo:
        """A4図面を解析"""
        
        try:
            # 画像読み込み
            image = self._load_image(file_path)
            if image is None:
                raise ValueError("画像の読み込みに失敗しました")
            
            # 画像サイズ取得
            height, width = image.shape[:2]
            
            # DPI取得
            dpi = self._get_image_dpi(file_path)
            
            # 向き判定
            orientation = "portrait" if height > width else "landscape"
            
            # A4サイズ判定
            is_valid_a4, scale_factor = self._check_a4_size(width, height, dpi)
            
            # 品質スコア計算
            quality_score = self._calculate_quality_score(image)
            
            return A4DrawingInfo(
                width=width,
                height=height,
                dpi=dpi,
                orientation=orientation,
                is_valid_a4=is_valid_a4,
                scale_factor=scale_factor,
                quality_score=quality_score
            )
        
        except Exception as e:
            self.logger.error(f"図面解析エラー: {e}")
            raise
    
    def optimize_a4_drawing(self, file_path: str) -> str:
        """A4図面を最適化"""
        
        try:
            # 画像読み込み
            image = self._load_image(file_path)
            if image is None:
                raise ValueError("画像の読み込みに失敗しました")
            
            # 画像サイズ取得
            height, width = image.shape[:2]
            
            # DPI取得
            dpi = self._get_image_dpi(file_path)
            
            # A4サイズ判定
            is_valid_a4, scale_factor = self._check_a4_size(width, height, dpi)
            
            if is_valid_a4:
                return file_path
            
            # サイズ調整
            target_width = self.A4_WIDTH_PX
            target_height = self.A4_HEIGHT_PX
            
            if height > width:  # 縦向き
                if width / height > self.A4_WIDTH_MM / self.A4_HEIGHT_MM:
                    target_height = int(target_width * height / width)
                else:
                    target_width = int(target_height * width / height)
            else:  # 横向き
                target_width, target_height = target_height, target_width
                if width / height > self.A4_HEIGHT_MM / self.A4_WIDTH_MM:
                    target_height = int(target_width * height / width)
                else:
                    target_width = int(target_height * width / height)
            
            # リサイズ
            resized = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
            
            # 画質改善
            enhanced = self._enhance_image(resized)
            
            # 保存
            output_path = str(Path(file_path).parent / f"optimized_{Path(file_path).name}")
            cv2.imwrite(output_path, enhanced)
            
            self.logger.info(f"図面最適化完了: {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"図面最適化エラー: {e}")
            raise
    
    def _load_image(self, file_path: str) -> Optional[np.ndarray]:
        """画像を読み込み"""
        
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.pdf':
                # PDFの場合は最初のページを画像として読み込み
                pages = pdf2image.convert_from_path(file_path, dpi=self.STANDARD_DPI)
                if not pages:
                    raise ValueError("PDFの変換に失敗しました")
                
                # PIL ImageをOpenCV形式に変換
                image = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
            else:
                # 画像ファイルを直接読み込み
                image = cv2.imread(str(file_path))
            
            if image is None:
                raise ValueError("画像の読み込みに失敗しました")
            
            return image
        
        except Exception as e:
            self.logger.error(f"画像読み込みエラー: {e}")
            return None
    
    def _get_image_dpi(self, file_path: str) -> int:
        """画像のDPIを取得"""
        
        try:
            with Image.open(file_path) as img:
                dpi = img.info.get('dpi')
                if dpi:
                    return int(dpi[0])
            
            # DPI情報がない場合は標準DPIを使用
            return self.STANDARD_DPI
        
        except Exception:
            return self.STANDARD_DPI
    
    def _check_a4_size(self, width: int, height: int, dpi: int) -> Tuple[bool, float]:
        """A4サイズかどうかを判定"""
        
        # 実際のサイズ（mm）
        actual_width_mm = width * 25.4 / dpi
        actual_height_mm = height * 25.4 / dpi
        
        # 許容誤差（±5mm）
        tolerance = 5
        
        # 縦向きと横向きの両方でチェック
        is_portrait_a4 = (
            abs(actual_width_mm - self.A4_WIDTH_MM) <= tolerance and
            abs(actual_height_mm - self.A4_HEIGHT_MM) <= tolerance
        )
        
        is_landscape_a4 = (
            abs(actual_width_mm - self.A4_HEIGHT_MM) <= tolerance and
            abs(actual_height_mm - self.A4_WIDTH_MM) <= tolerance
        )
        
        is_valid_a4 = is_portrait_a4 or is_landscape_a4
        
        # スケール係数計算
        if is_portrait_a4:
            scale_factor = self.A4_WIDTH_MM / actual_width_mm
        elif is_landscape_a4:
            scale_factor = self.A4_HEIGHT_MM / actual_width_mm
        else:
            # 近い方のアスペクト比に合わせる
            portrait_ratio = actual_width_mm / actual_height_mm
            landscape_ratio = actual_height_mm / actual_width_mm
            a4_ratio = self.A4_WIDTH_MM / self.A4_HEIGHT_MM
            
            if abs(portrait_ratio - a4_ratio) < abs(landscape_ratio - a4_ratio):
                scale_factor = self.A4_WIDTH_MM / actual_width_mm
            else:
                scale_factor = self.A4_HEIGHT_MM / actual_width_mm
        
        return is_valid_a4, scale_factor
    
    def _calculate_quality_score(self, image: np.ndarray) -> float:
        """画質スコアを計算"""
        
        try:
            # グレースケール変換
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # コントラストスコア
            contrast_score = np.std(gray) / 128
            
            # シャープネススコア
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness_score = np.std(laplacian) / 128
            
            # ノイズスコア（低いほど良い）
            noise_score = 1.0 - (cv2.meanStdDev(gray)[1][0][0] / 128)
            
            # 最終スコア（0-1）
            quality_score = (contrast_score + sharpness_score + noise_score) / 3
            return min(max(quality_score, 0.0), 1.0)
        
        except Exception:
            return 0.5
    
    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """画質を改善"""
        
        try:
            # グレースケール変換
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # コントラスト調整
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # ノイズ除去
            enhanced = cv2.fastNlMeansDenoising(enhanced)
            
            # シャープネス強調
            kernel = np.array([[-1,-1,-1],
                             [-1, 9,-1],
                             [-1,-1,-1]])
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            
            if len(image.shape) == 3:
                # カラー画像の場合は元の色を復元
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            return enhanced
        
        except Exception:
            return image
    
    def extract_layout_features(self, file_path: str) -> Dict[str, Any]:
        """レイアウト特徴を抽出"""
        
        try:
            # 画像読み込み
            image = self._load_image(file_path)
            if image is None:
                raise ValueError("画像の読み込みに失敗しました")
            
            # グレースケール変換
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # 二値化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 輪郭検出
            contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # 直線検出
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
            
            # 水平・垂直線のカウント
            horizontal_lines = 0
            vertical_lines = 0
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                    
                    if angle < 10 or angle > 170:
                        horizontal_lines += 1
                    elif 80 < angle < 100:
                        vertical_lines += 1
            
            # レイアウト複雑度（0-1）
            layout_complexity = min(len(contours) / 1000, 1.0)
            
            return {
                'contour_count': len(contours),
                'horizontal_lines': horizontal_lines,
                'vertical_lines': vertical_lines,
                'layout_complexity': layout_complexity,
                'image_size': image.shape[:2],
                'aspect_ratio': image.shape[1] / image.shape[0]
            }
        
        except Exception as e:
            self.logger.error(f"レイアウト特徴抽出エラー: {e}")
            raise
