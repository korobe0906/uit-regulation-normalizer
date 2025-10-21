# src/processing/preprocess/ocr/factory.py
from typing import Literal
from .paddle_engine import PaddleClassicEngine
from .tesseract_engine import TesseractEngine

# def build_engine(name: Literal["paddle","tesseract"], lang: str = "vi"):
#     if name == "paddle":
#         return PaddleClassicEngine(lang=lang)
#     if name == "tesseract":
#         return TesseractEngine(lang=lang)
#     raise ValueError(f"Unknown OCR engine: {name}")
def build_engine(name: str, lang: str = "vie+eng"):
    # Map ngôn ngữ ngắn → Tesseract lang
    lang = (lang or "").lower()
    if lang in ("vi", "vie", "vi-vn"):
        lang = "vie+eng"
    if name == "auto" or name == "tesseract":
        return TesseractEngine(lang=lang)
    if name == "paddle":
        return PaddleClassicEngine(lang=lang)  # giữ nguyên như bạn đang có
    raise ValueError(f"Unknown OCR engine: {name}")

