# Export các engine OCR
from .paddle_engine import PaddleClassicEngine
from .tesseract_engine import TesseractEngine

# Giữ alias tên cũ để tương thích nếu nơi khác còn import PaddleEngine
PaddleEngine = PaddleClassicEngine

__all__ = ["PaddleClassicEngine", "TesseractEngine", "PaddleEngine"]
