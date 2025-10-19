# image_ops.py
import os
import cv2
import numpy as np
from pdf2image import convert_from_path

POPPLER_PATH = r"D:\DevTools\poppler-25.07.0\Library\bin"  # sửa đúng nơi có pdfinfo.exe, pdftoppm.exe

def pdf_to_images(pdf_path, dpi=300):
    if not os.path.isdir(POPPLER_PATH):
        raise RuntimeError(f"Poppler path not found: {POPPLER_PATH}")
    return convert_from_path(pdf_path, dpi=dpi, poppler_path=POPPLER_PATH)

def ensure_3_channels(img: np.ndarray) -> np.ndarray:
    # img có thể là HxW (gray) hoặc HxWxC
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)  # 3 kênh RGB
    elif img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # 4 -> 3 kênh
    # ép uint8
    if img.dtype != np.uint8:
        img = img.astype(np.uint8)
    return img

def preprocess_image(pil_img) -> np.ndarray:
    # PIL RGB -> numpy BGR để dùng OpenCV
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # denoise nhẹ
    img = cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 7, 21)

    # to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold (Otsu)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # deskew an toàn
    coords = np.column_stack(np.where(th < 255))
    if coords.size >= 6:  # cần đủ điểm để ước lượng
        angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        h, w = th.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        th = cv2.warpAffine(th, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # mở rộng 1 kênh -> 3 kênh
    npimg = ensure_3_channels(th)  # HxWx3, uint8
    return npimg
