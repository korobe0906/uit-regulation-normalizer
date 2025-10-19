from .base import BaseOCREngine
from paddleocr import PaddleOCR

class PaddleEngine(BaseOCREngine):
    name = "paddle"
    def __init__(self, lang="vi"):
        self.ocr = PaddleOCR(lang=lang)
    def extract(self, image):
        # image: numpy array (H, W) or BGR; PaddleOCR nhận path hoặc ndarray
        return self.ocr.ocr(image)  # list[ [ [bbox], (text, conf) ], ... ]
