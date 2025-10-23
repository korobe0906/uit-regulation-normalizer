# src/processing/preprocess/image_ops.py
import cv2
import numpy as np
from pathlib import Path
import os, platform
from typing import List, Optional
from PIL import Image
from paddle import crop
from pdf2image import convert_from_path
import pytesseract
import tempfile, subprocess, shutil, os

def _osd_angle_deg(bgr):
    try:
        bgr = ensure_3_channels(bgr)
        h, w = bgr.shape[:2]
        if min(h, w) < 200:  # crop quá nhỏ thì OSD hay sai
            return 0
        osd = pytesseract.image_to_osd(
            bgr,
            config="--psm 0 --oem 1 -c min_characters_to_try=50"
        )
        for line in osd.splitlines():
            if "Orientation in degrees" in line:
                return int(line.split(":")[1].strip())
    except Exception:
        pass
    return 0


# def _osd_angle_deg(bgr):
#     """
#     Dùng Tesseract OSD để ước lượng góc xoay của 1 crop.
#     Trả về 0, 90, 180, 270 (độ). Lỗi -> 0.
#     """
#     try:
#         osd = pytesseract.image_to_osd(bgr)
#         for line in osd.splitlines():
#             if "Orientation in degrees" in line:
#                 return int(line.split(":")[1].strip())
#     except Exception:
#         pass
#     return 0

def _rotate_to_upright(bgr, deg):
    if deg == 0:   return bgr
    if deg == 90:  return cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
    if deg == 180: return cv2.rotate(bgr, cv2.ROTATE_180)
    if deg == 270: return cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return bgr

def split_and_upright(bgr, mode: str = "horizontal", force_rotate_180: bool = False):
    """
    Không chia đôi nữa. Chỉ xoay toàn ảnh (ép 270 độ nếu cần).
    """
    # Nếu muốn bỏ OSD luôn và xoay cứng 270°
    crop_upright = cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Nếu vẫn muốn giữ flag ép 180° (tuỳ chọn)
    if force_rotate_180:
        crop_upright = cv2.rotate(crop_upright, cv2.ROTATE_180)

    return [(0, 0, crop_upright)]



def prep_for_tesseract_from_bgr(bgr):
    """Nhị phân hoá nhẹ cho Tesseract (dùng khi fallback)."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    black_ratio = (th < 128).mean()
    if black_ratio < 0.01:
        th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 35, 11)
    th = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
    return np.ascontiguousarray(th, dtype=np.uint8)


def _resize_max_side(bgr: np.ndarray, max_side: int = 3980) -> np.ndarray:
    h, w = bgr.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return bgr
    scale = max_side / float(m)
    new_w, new_h = int(w*scale), int(h*scale)
    return cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _detect_poppler_path() -> str | None:
    # Ưu tiên ENV
    env_path = os.getenv("POPPLER_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # Windows: thử vài vị trí phổ biến (chỉnh theo máy bạn nếu cần)
    if platform.system().lower() == "windows":
        candidates = [
            r"D:\DevTools\poppler-25.07.0\Library\bin",  # bạn đã cài ở đây
            r"C:\tools\poppler\bin",
            r"C:\poppler\bin",
            r"C:\Program Files\poppler\bin",
        ]
        for p in candidates:
            if Path(p).exists():
                return p
    return None



def pdf_to_images(pdf_path: str, dpi: int = 300, poppler_path: Optional[str] = None,
                  limit: Optional[int] = None, output_dir: Optional[str] = None) -> List[Image.Image]:
    pdf_abs = str(Path(pdf_path).resolve())
    if not os.path.exists(pdf_abs):
        raise FileNotFoundError(f"PDF not found: {pdf_abs}")

    # chọn nơi ghi ảnh
    out_dir = Path(output_dir).resolve() if output_dir else Path.cwd() / "render_tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = str((out_dir / "page").resolve())   # -> ...\b1-xxxx\render\page-001.png

    bin_dir = poppler_path or os.getenv("POPPLER_PATH") or ""
    pdftoppm = shutil.which("pdftoppm", path=bin_dir) or str(Path(bin_dir) / "pdftoppm.exe")
    if not (pdftoppm and os.path.exists(pdftoppm)):
        raise RuntimeError("pdftoppm.exe not found. Pass --poppler_path <...\\bin>")

    cmd = [pdftoppm, "-r", str(dpi), "-png"]
    if limit and limit > 0:
        cmd += ["-f", "1", "-l", str(limit)]     # 👈 chỉ render từ 1..limit
    cmd += [pdf_abs, prefix]

    print(f"[DEBUG:image_ops] run: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, timeout=180)

    files = sorted(out_dir.glob("page-*.png"))
    if limit:
        files = files[:limit]
    pages = [Image.open(f).convert("RGB") for f in files]
    print(f"[DEBUG:image_ops] rendered {len(pages)} page(s) -> {out_dir}")
    return pages

def ensure_3_channels(img: np.ndarray) -> np.ndarray:
    # img có thể là HxW (gray) hoặc HxWxC
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)  # giữ đúng thứ tự BGR cho OpenCV
    elif img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # 4 -> 3 kênh
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)
    return img

def preprocess_image(pil_img, mode: str = "paddle") -> np.ndarray:
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    bgr = cv2.fastNlMeansDenoisingColored(bgr, None, 3, 3, 7, 21)

    # Deskew ước lượng trên Otsu, sau đó áp lên BGR
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(th < 255))
    if coords.size >= 100:
        angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        h, w = gray.shape[:2]
        M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
        bgr = cv2.warpAffine(bgr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # Resize tránh >4000
    bgr = _resize_max_side(bgr, 3980)

    if mode == "paddle":
        return np.ascontiguousarray(bgr, dtype=np.uint8)

    # Tesseract: nhị phân / contrast cao
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    black_ratio = (th < 128).mean()
    if black_ratio < 0.01:
        th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 11)
    th = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
    return np.ascontiguousarray(th, dtype=np.uint8)

