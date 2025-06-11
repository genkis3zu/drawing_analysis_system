# src/utils/image_processor.py

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union, cast, TypeVar, List, Iterator, Generator
from typing import Protocol, runtime_checkable
from typing_extensions import TypeGuard
import logging
from dataclasses import dataclass
from PIL import Image
from numpy.typing import NDArray
import tempfile
import os
import contextlib

# PDFサポートの確認と型インポート
try:
    import pdf2image
    from pdf2image.exceptions import PDFPageCountError
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    PDFPageCountError = Exception  # Type alias for error handling
    logging.warning("pdf2image is not installed. PDF support will be disabled.")

# OpenCV型のエイリアス
NDImageType = NDArray[np.uint8]
NDFloatType = NDArray[np.float32]
NDDoubleType = NDArray[np.float64]
NDIntType = NDArray[np.int32]

# OpenCV画像型
CVImage = NDArray[Union[np.uint8, np.float32, np.float64]]
ImageType = NDArray[np.uint8]
GrayImageType = NDArray[np.uint8]
FloatArray = NDArray[np.float64]
ContourType = NDArray[np.int32]

# 型変数
T = TypeVar('T', bound=np.generic)
ImageLike = TypeVar('ImageLike', NDImageType, NDFloatType, NDDoubleType)

def ensure_uint8(image: NDArray[Any]) -> NDImageType:
    """画像をuint8型に変換"""
    if image.dtype != np.uint8:
        return np.clip(image * 255 if image.dtype == np.float32 or image.dtype == np.float64 else image, 0, 255).astype(np.uint8)
    return image

def ensure_float32(image: NDArray[Any]) -> NDFloatType:
    """画像をfloat32型に変換"""
    if image.dtype != np.float32:
        return (image / 255.0 if image.dtype == np.uint8 else image).astype(np.float32)
    return image

@contextlib.contextmanager
def temporary_path(suffix: str = '') -> Generator[Path, None, None]:
    """一時ファイルを安全に管理するコンテキストマネージャー"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp_file.close()
        yield Path(temp_file.name)
    finally:
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

def is_valid_image(image: Optional[NDArray[Any]]) -> TypeGuard[CVImage]:
    """画像の有効性を確認"""
    return (
        image is not None and
        isinstance(image, np.ndarray) and
        image.size > 0 and
        len(image.shape) in (2, 3) and
        image.dtype in (np.uint8, np.float32, np.float64)
    )

# PDFサポートの確認
try:
    import pdf2image
    from pdf2image.exceptions import PDFPageCountError
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("pdf2image is not installed. PDF support will be disabled.")

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
    MIN_DPI = 150
    MAX_DPI = 600
    
    # A4サイズのピクセル数（300DPI）
    A4_WIDTH_PX = int(A4_WIDTH_MM * STANDARD_DPI / 25.4)
    A4_HEIGHT_PX = int(A4_HEIGHT_MM * STANDARD_DPI / 25.4)
    
    # A4サイズの許容誤差（mm）
    SIZE_TOLERANCE_MM = 2  # より厳密な±2mm
    
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
            if not is_valid_image(image):
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
            
            # 型変換して画質改善
            resized_uint8 = ensure_uint8(resized)
            enhanced = self._enhance_image(resized_uint8)
            
            # 一時ファイルに保存
            with temporary_path(suffix=Path(file_path).suffix) as temp_path:
                cv2.imwrite(str(temp_path), enhanced)
                
                # 元のファイルと同じディレクトリに最適化ファイルをコピー
                output_path = str(Path(file_path).parent / f"optimized_{Path(file_path).name}")
                temp_path.rename(output_path)
                
                self.logger.info(f"図面最適化完了: {output_path}")
                return output_path
            
        except Exception as e:
            self.logger.error(f"図面最適化エラー: {e}")
            raise
    
    def _load_image(self, file_path: str) -> Optional[CVImage]:
        """画像を読み込み"""
        
        try:
            file_path_obj = Path(str(file_path))
            
            if file_path_obj.suffix.lower() == '.pdf':
                if not PDF_SUPPORT:
                    raise ValueError("PDF support is not available. Please install pdf2image package.")
                
                # PDFの一時変換用ディレクトリを作成
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        # PDFの場合は最初のページを画像として読み込み
                        pages = pdf2image.convert_from_path(
                            str(file_path_obj),
                            dpi=self.STANDARD_DPI,
                            output_folder=temp_dir,
                            first_page=1,
                            last_page=1
                        )
                        if not pages:
                            raise ValueError("PDFの変換に失敗しました")
                        
                        # PIL ImageをOpenCV形式に変換
                        image = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
                        if not is_valid_image(image):
                            raise ValueError("PDF画像の変換に失敗しました")
                        return cast(ImageType, image)
                        
                    except PDFPageCountError:
                        raise ValueError("PDFページの読み込みに失敗しました")
                    except Exception as e:
                        raise ValueError(f"PDF処理エラー: {str(e)}")
            else:
                # 画像ファイルを直接読み込み
                image = cv2.imread(str(file_path_obj))
                if is_valid_image(image):
                    return cast(ImageType, image)
            
            raise ValueError("画像の読み込みに失敗しました")
        
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
        
        # DPIの妥当性チェック
        if not self.MIN_DPI <= dpi <= self.MAX_DPI:
            self.logger.warning(f"不適切なDPI値: {dpi}. 標準DPIを使用します。")
            dpi = self.STANDARD_DPI
        
        # 実際のサイズ（mm）
        actual_width_mm = width * 25.4 / dpi
        actual_height_mm = height * 25.4 / dpi
        
        # アスペクト比チェック
        actual_ratio = actual_width_mm / actual_height_mm
        a4_ratio = self.A4_WIDTH_MM / self.A4_HEIGHT_MM
        ratio_tolerance = 0.01  # 1%の許容誤差
        
        ratio_valid = abs(actual_ratio - a4_ratio) <= ratio_tolerance
        
        # 縦向きと横向きの両方でチェック
        is_portrait_a4 = (
            abs(actual_width_mm - self.A4_WIDTH_MM) <= self.SIZE_TOLERANCE_MM and
            abs(actual_height_mm - self.A4_HEIGHT_MM) <= self.SIZE_TOLERANCE_MM and
            ratio_valid
        )
        
        is_landscape_a4 = (
            abs(actual_width_mm - self.A4_HEIGHT_MM) <= self.SIZE_TOLERANCE_MM and
            abs(actual_height_mm - self.A4_WIDTH_MM) <= self.SIZE_TOLERANCE_MM and
            ratio_valid
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
    
    def _calculate_quality_score(self, image: CVImage) -> float:
        """画質スコアを計算"""
        
        try:
            # グレースケール変換
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # コントラストスコア
            contrast_score = float(np.std(gray) / 128)
            
            # シャープネススコア
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness_score = float(np.std(laplacian) / 128)
            
            # ノイズスコア（低いほど良い）
            noise_score = 1.0 - float(cv2.meanStdDev(gray)[1][0][0] / 128)
            
            # 最終スコア（0-1）
            quality_score = (contrast_score + sharpness_score + noise_score) / 3
            return min(max(quality_score, 0.0), 1.0)
        
        except Exception:
            return 0.5
    
    def _enhance_image(self, image: CVImage) -> CVImage:
        """画質を改善"""
        
        try:
            # uint8型に変換
            if image.dtype != np.uint8:
                image = ensure_uint8(image)
            
            # 元画像のコピーを作成
            enhanced = image.copy()
            
            # カラー画像の場合
            if len(image.shape) == 3:
                # YUV色空間に変換してY成分のみを処理
                yuv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2YUV)
                y = yuv[:,:,0]
                
                # 適応的ヒストグラム平坦化
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                y = clahe.apply(y)
                
                # バイラテラルフィルタでノイズ除去（エッジ保持）
                y = cv2.bilateralFilter(y, 9, 75, 75)
                
                # アンシャープマスクでシャープネス強調
                gaussian = cv2.GaussianBlur(y, (0, 0), 3.0)
                y = cv2.addWeighted(y, 1.5, gaussian, -0.5, 0)
                
                # 処理したY成分を戻す
                yuv[:,:,0] = y
                enhanced = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
                
            else:  # グレースケール画像の場合
                # 適応的ヒストグラム平坦化
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(enhanced)
                
                # バイラテラルフィルタでノイズ除去（エッジ保持）
                enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
                
                # アンシャープマスクでシャープネス強調
                gaussian = cv2.GaussianBlur(enhanced, (0, 0), 3.0)
                enhanced = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)
            
            # ガンマ補正
            gamma = 1.2
            look_up_table = np.empty((1, 256), np.uint8)
            for i in range(256):
                look_up_table[0,i] = np.clip(pow(i / 255.0, 1.0 / gamma) * 255.0, 0, 255)
            enhanced = cv2.LUT(enhanced, look_up_table)
            
            return cast(CVImage, enhanced)
        
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
            
            # 適応的二値化
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # ノイズ除去
            kernel = np.ones((3,3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 輪郭検出（階層構造を保持）
            contours, hierarchy = cv2.findContours(
                binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # 直線検出（確率的ハフ変換）
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(
                edges, 1, np.pi/180, 50, 
                minLineLength=50, maxLineGap=5
            )
            
            # 線の分類と特徴抽出
            horizontal_lines = []
            vertical_lines = []
            diagonal_lines = []
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    angle = abs(np.arctan2(y2-y1, x2-x1) * 180 / np.pi)
                    
                    if angle < 10 or angle > 170:
                        horizontal_lines.append((length, (x1,y1,x2,y2)))
                    elif 80 < angle < 100:
                        vertical_lines.append((length, (x1,y1,x2,y2)))
                    else:
                        diagonal_lines.append((length, (x1,y1,x2,y2)))
            
            # 図面枠の検出
            border_rect = None
            if contours:
                # 面積でソート
                sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
                for contour in sorted_contours[:3]:  # 上位3つの輪郭を確認
                    rect = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rect)
                    box = np.array(box, dtype=np.int32)
                    # 図面枠の条件をチェック
                    if self._is_valid_border(box, image.shape):
                        border_rect = rect
                        break
            
            # テキストブロックの検出
            text_regions = []
            if hierarchy is not None:
                for i, contour in enumerate(contours):
                    if hierarchy[0][i][3] == -1:  # 外部輪郭のみ
                        area = cv2.contourArea(contour)
                        if 100 < area < 10000:  # テキストブロックの想定サイズ
                            rect = cv2.minAreaRect(contour)
                            text_regions.append(rect)
            
            # レイアウト複雑度の計算
            layout_features = {
                'contour_count': len(contours),
                'hierarchy_depth': self._calculate_hierarchy_depth(hierarchy),
                'horizontal_lines': len(horizontal_lines),
                'vertical_lines': len(vertical_lines),
                'diagonal_lines': len(diagonal_lines),
                'text_regions': len(text_regions),
                'has_border': border_rect is not None,
                'symmetry_score': float(self._calculate_symmetry_score(binary)),
                'density_distribution': self._calculate_density_distribution(binary),
                'layout_regularity': self._calculate_layout_regularity(
                    horizontal_lines, vertical_lines, text_regions
                ),
                'image_size': image.shape[:2],
                'aspect_ratio': float(image.shape[1] / image.shape[0])
            }
            
            # 全体的な複雑度スコア（0-1）
            layout_features['complexity_score'] = self._calculate_complexity_score(layout_features)
            
            return layout_features
            
        except Exception as e:
            self.logger.error(f"レイアウト特徴抽出エラー: {e}")
            raise
    
    def _is_valid_border(self, box: ContourType, image_shape: tuple) -> bool:
        """図面枠として有効かどうかを判定"""
        h, w = image_shape[:2]
        area = cv2.contourArea(box)
        image_area = h * w
        
        # 面積比チェック
        area_ratio = area / image_area
        if not (0.7 < area_ratio < 0.95):  # 図面枠は画像の70-95%を占めるはず
            return False
        
        # 矩形度チェック
        rect_ratio = cv2.contourArea(box) / (cv2.arcLength(box, True) ** 2)
        if rect_ratio < 0.85:  # 完全な矩形なら0.95程度
            return False
        
        return True
    
    def _calculate_hierarchy_depth(self, hierarchy: Optional[np.ndarray]) -> int:
        """輪郭の階層の深さを計算"""
        if hierarchy is None:
            return 0
        
        max_depth = 0
        for i in range(len(hierarchy[0])):
            depth = 0
            parent = hierarchy[0][i][3]
            while parent != -1:
                depth += 1
                parent = hierarchy[0][parent][3]
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_symmetry_score(self, binary: GrayImageType) -> float:
        """対称性スコアを計算"""
        h, w = binary.shape
        
        # 水平方向の対称性
        left = binary[:, :w//2]
        right = cv2.flip(binary[:, w//2:], 1)
        if left.shape[1] > right.shape[1]:
            left = left[:, :right.shape[1]]
        elif right.shape[1] > left.shape[1]:
            right = right[:, :left.shape[1]]
        h_symmetry = float(np.sum(left == right)) / float(left.size)
        
        # 垂直方向の対称性
        top = binary[:h//2, :]
        bottom = cv2.flip(binary[h//2:, :], 0)
        if top.shape[0] > bottom.shape[0]:
            top = top[:bottom.shape[0], :]
        elif bottom.shape[0] > top.shape[0]:
            bottom = bottom[:top.shape[0], :]
        v_symmetry = float(np.sum(top == bottom)) / float(top.size)
        
        return (h_symmetry + v_symmetry) / 2
    
    def _calculate_density_distribution(self, binary: GrayImageType) -> Dict[str, float]:
        """密度分布を計算"""
        h, w = binary.shape
        h_mid = h // 2
        w_mid = w // 2
        
        # 4分割して各領域の密度を計算
        top_left = np.sum(binary[:h_mid, :w_mid]) / (h_mid * w_mid)
        top_right = np.sum(binary[:h_mid, w_mid:]) / (h_mid * (w - w_mid))
        bottom_left = np.sum(binary[h_mid:, :w_mid]) / ((h - h_mid) * w_mid)
        bottom_right = np.sum(binary[h_mid:, w_mid:]) / ((h - h_mid) * (w - w_mid))
        
        return {
            'top_left': float(top_left / 255),
            'top_right': float(top_right / 255),
            'bottom_left': float(bottom_left / 255),
            'bottom_right': float(bottom_right / 255)
        }
    
    def _calculate_layout_regularity(self, horizontal_lines: List[Tuple[float, Tuple[int, int, int, int]]], 
                                   vertical_lines: List[Tuple[float, Tuple[int, int, int, int]]], 
                                   text_regions: List[Any]) -> float:
        """レイアウトの規則性を計算"""
        
        # 水平・垂直線の間隔の規則性
        h_spacing = []
        for i in range(len(horizontal_lines)-1):
            y1 = horizontal_lines[i][1][1]
            y2 = horizontal_lines[i+1][1][1]
            h_spacing.append(abs(y2 - y1))
        
        v_spacing = []
        for i in range(len(vertical_lines)-1):
            x1 = vertical_lines[i][1][0]
            x2 = vertical_lines[i+1][1][0]
            v_spacing.append(abs(x2 - x1))
        
        # 間隔の標準偏差（小さいほど規則的）
        h_std = float(np.std(h_spacing)) if h_spacing else 0
        v_std = float(np.std(v_spacing)) if v_spacing else 0
        
        # テキストブロックの配置規則性
        text_y_coords = [rect[0][1] for rect in text_regions]
        text_std = float(np.std(text_y_coords)) if text_y_coords else 0
        
        # スコアの正規化（0-1、1が最も規則的）
        regularity_score = 1.0
        if h_std > 0:
            regularity_score *= 1.0 / (1.0 + h_std/100)
        if v_std > 0:
            regularity_score *= 1.0 / (1.0 + v_std/100)
        if text_std > 0:
            regularity_score *= 1.0 / (1.0 + text_std/100)
        
        return regularity_score
    
    def _calculate_complexity_score(self, features: Dict[str, Any]) -> float:
        """複雑度スコアを計算"""
        
        # 各要素の重み付け
        weights = {
            'contour_count': 0.15,
            'hierarchy_depth': 0.1,
            'horizontal_lines': 0.15,
            'vertical_lines': 0.15,
            'diagonal_lines': 0.1,
            'text_regions': 0.2,
            'layout_regularity': -0.15  # 規則性は複雑度を下げる
        }
        
        # スコア計算
        score = 0.0
        max_counts = {
            'contour_count': 1000,
            'hierarchy_depth': 10,
            'horizontal_lines': 50,
            'vertical_lines': 50,
            'diagonal_lines': 30,
            'text_regions': 100
        }
        
        for feature, weight in weights.items():
            if feature == 'layout_regularity':
                # 規則性は逆数を取る（規則的なほど複雑度は下がる）
                score += (1.0 - features[feature]) * abs(weight)
            else:
                # その他の特徴は正規化して加算
                value = min(features[feature] / max_counts[feature], 1.0)
                score += value * weight
        
        return min(max(score, 0.0), 1.0)
