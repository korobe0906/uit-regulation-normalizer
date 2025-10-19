from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional

BBox = Tuple[float, float, float, float]  # x0, y0, x1, y1

@dataclass
class Word:
    text: str
    bbox: BBox
    conf: float

@dataclass
class Line:
    text: str
    bbox: BBox
    conf: float
    words: List[Word]

@dataclass
class PageText:
    document_id: str
    page_index: int
    width: int
    height: int
    lines: List[Line]
    engine: str
    meta: Optional[dict] = None

    def to_dict(self): return asdict(self)
