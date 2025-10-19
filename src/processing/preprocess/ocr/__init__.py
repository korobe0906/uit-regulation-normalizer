"""
preprocess.ocr
==============

OCR engines used in the UIT Regulation Normalizer pipeline.

This subpackage exposes:
- BaseOCREngine: common interface for OCR engines
- PaddleEngine:  PaddleOCR-based engine (recommended for Vietnamese)
- TesseractEngine: (optional) pytesseract-based engine, if available
- build_engine:  factory function to construct an engine by name
"""

from typing import Optional, TYPE_CHECKING

from .base import BaseOCREngine
from .paddle_engine import PaddleEngine

# Tesseract is optional; keep import safe so the package still works without it.
try:
    from .tesseract_engine import TesseractEngine  # type: ignore
except Exception:  # ImportError or runtime deps missing
    TesseractEngine = None  # type: ignore[assignment]

from .factory import build_engine

if TYPE_CHECKING:
    # For type-checkers only (won't import at runtime)
    from .tesseract_engine import TesseractEngine as _TesseractEngine  # noqa: F401

__all__ = [
    "BaseOCREngine",
    "PaddleEngine",
    "TesseractEngine",  # may be None if not installed; caller should check
    "build_engine",
]


def has_tesseract() -> bool:
    """
    Return True if TesseractEngine is importable (deps present), else False.
    Helpful for feature flags or graceful fallbacks.
    """
    return TesseractEngine is not None
