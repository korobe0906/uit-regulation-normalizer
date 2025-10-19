
from .paddle_engine import PaddleEngine
try:
    from .tesseract_engine import TesseractEngine
except Exception:
    TesseractEngine = None

def build_engine(name: str, **kw):
    if name == "paddle": return PaddleEngine(**kw)
    if name == "tesseract" and TesseractEngine: return TesseractEngine(**kw)
    raise ValueError(f"Unknown OCR engine: {name}")
