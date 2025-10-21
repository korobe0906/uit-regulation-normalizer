from typing import Any, List
import numpy as np
import pytesseract
from pytesseract import Output

_LANG_MAP = {"vi": "vie+eng", "en": "eng"}

class TesseractEngine:
    def __init__(self, lang: str = "vi"):
        self.lang = _LANG_MAP.get(lang, "vie+eng")

    def extract(self, image: np.ndarray) -> List[Any]:
        # Sử dụng cấu hình tối ưu cho văn bản tiếng Việt
        config = "--oem 1 --psm 3 -c preserve_interword_spaces=1"
        data = pytesseract.image_to_data(
            image,
            output_type=Output.DICT,
            lang=self.lang,
            config=config
        )

        n = len(data["text"])
        out: List[dict] = []
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            conf = data["conf"][i]
            try:
                conf = float(conf)
            except:
                conf = -1.0
            if conf <= 0 or not txt:
                continue
            x, y = int(data["left"][i]), int(data["top"][i])
            w, h = int(data["width"][i]), int(data["height"][i])
            out.append({
                "text": txt,
                "conf": conf,
                "bbox": [x, y, x + w, y + h],
                "engine": "tesseract"
            })
        return out
