# src/processing/preprocess/ocr/paddle_engine.py
from typing import Any, List
import numpy as np

try:
    from paddleocr import PaddleOCR
except Exception as e:
    PaddleOCR = None

_LANG_FALLBACKS = {
    "vi": ["vi", "latin", "en"],
    "vn": ["vi", "latin", "en"],
    "en": ["en", "latin"],
}

class PaddleClassicEngine:
    def __init__(self, lang: str = "vi"):
        if PaddleOCR is None:
            raise RuntimeError("paddleocr chưa được cài. pip install paddleocr")
        langs = _LANG_FALLBACKS.get(lang, [lang, "latin", "en"])
        last_err = None
        for lg in langs:
            try:
                self.ocr = PaddleOCR(lang=lg)
                self.lang = lg
                break
            except Exception as e:
                last_err = e
                self.ocr = None
        if self.ocr is None:
            raise last_err or RuntimeError("Không khởi tạo được PaddleOCR")

    def extract(self, image: np.ndarray) -> List[Any]:
        # yêu cầu image uint8, BGR hoặc RGB đều được; paddle tự handle
        result = self.ocr.ocr(image)
        # PaddleOCR classic trả list theo batch: lấy phần tử đầu
        if isinstance(result, list) and result and isinstance(result[0], list):
            return result[0]
        return result or []
