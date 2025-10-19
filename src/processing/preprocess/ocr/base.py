from typing import Any, List, Tuple

class BaseOCREngine:
    name = "base"
    def extract(self, image) -> List[Any]:
        """Return engine-native results (words/lines with bbox, conf)."""
        raise NotImplementedError
