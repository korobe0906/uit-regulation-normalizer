# src/processing/preprocess/ocr/factory.py
from typing import Literal
from .paddle_engine import PaddleClassicEngine
from .tesseract_engine import TesseractEngine

def build_engine(name: Literal["paddle","tesseract"], lang: str = "vi"):
    if name == "paddle":
        return PaddleClassicEngine(lang=lang)
    if name == "tesseract":
        return TesseractEngine(lang=lang)
    raise ValueError(f"Unknown OCR engine: {name}")

