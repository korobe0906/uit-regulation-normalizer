from typing import Any, List
import numpy as np
import pytesseract
from pytesseract import Output

_LANG_MAP = {"vi": "vie+eng", "en": "eng"}

class TesseractEngine:
    def __init__(self, lang: str = "vi"):
        self.lang = _LANG_MAP.get(lang, "vie+eng")

    def extract(self, image: np.ndarray) -> List[Any]:
        config = "--psm 11"   # thử 4, 6, 11 để chọn tốt nhất
        data = pytesseract.image_to_data(image, output_type=Output.DICT, lang=self.lang, config=config)
        n = len(data["text"])
        out: List[dict] = []
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            conf = data["conf"][i]
            try:
                conf = float(conf)
            except:
                conf = -1.0
            if conf <= 0 or not txt:  # loại bỏ ô trống/không tin cậy
                continue
            x, y = int(data["left"][i]), int(data["top"][i])
            w, h = int(data["width"][i]), int(data["height"][i])
            out.append({
                "text": txt,
                "conf": conf,                 # 0..100 của tesseract
                "bbox": [x, y, x + w, y + h], # x0,y0,x1,y1
                "engine": "tesseract"
            })
        return out
