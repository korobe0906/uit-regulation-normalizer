# src/processing/preprocess/writer.py
"""
Writer utilities for OCR preprocessing pipeline.
- Convert Paddle OCR raw output to PageText dataclass
- Save PageText as JSON
"""

import json
import dataclasses
from dataclasses import asdict
from pathlib import Path
from typing import List, Tuple, Any
from .page_schema import PageText, Line, Word


# ------------------------------
# 1. Parse PaddleOCR line format
# ------------------------------
def _parse_paddle_line(line: Any) -> Tuple[Tuple[float, float, float, float], str, float]:
    """
    Parse a single PaddleOCR line.
    Supports both:
      - [bbox, (text, conf)]
      - [bbox, (text, conf), ...extra]
    Returns: (bbox, text, conf)
    """
    if not isinstance(line, (list, tuple)) or len(line) < 2:
        return (0.0, 0.0, 0.0, 0.0), "", 0.0

    bbox_pts = line[0]
    text_info = line[1]

    # Extract text/conf
    if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
        text, conf = text_info[0], text_info[1]
    else:
        text, conf = str(text_info), 1.0

    # Convert bbox from 4 points to (x_min, y_min, x_max, y_max)
    try:
        xs = [float(p[0]) for p in bbox_pts]
        ys = [float(p[1]) for p in bbox_pts]
        bbox = (min(xs), min(ys), max(xs), max(ys))
    except Exception:
        bbox = (0.0, 0.0, 0.0, 0.0)

    try:
        conf = float(conf)
    except Exception:
        conf = 0.0

    return bbox, str(text), conf


# ------------------------------
# 2. Build PageText from Paddle
# ------------------------------
def paddle_to_page(
    doc_id: str,
    page_idx: int,
    w: int,
    h: int,
    paddle_result: Any,
    min_conf: float = 0.5
) -> PageText:
    """
    Convert PaddleOCR raw output to PageText dataclass.

    Args:
        doc_id: unique document id
        page_idx: zero-based page index
        w, h: image dimensions
        paddle_result: raw output from paddle engine
        min_conf: confidence threshold
    """
    # Handle format [[lines_page0], [lines_page1], ...] or flat [lines_page]
    if isinstance(paddle_result, list) and paddle_result and isinstance(paddle_result[0], list):
        page_items = paddle_result[page_idx] if 0 <= page_idx < len(paddle_result) else []
    else:
        page_items = paddle_result or []

    lines: List[Line] = []
    for line in page_items:
        bbox, text, conf = _parse_paddle_line(line)
        if conf < min_conf:
            continue
        lines.append(Line(text=text, bbox=bbox, conf=float(conf), words=[]))

    return PageText(
        document_id=doc_id,
        page_index=page_idx,
        width=w,
        height=h,
        lines=lines,
        engine="paddle",
    )


# ------------------------------
# 3. JSON Serialization Helpers
# ------------------------------
def _json_default(o):
    """Handle numpy types & dataclasses."""
    try:
        import numpy as np
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, (np.ndarray,)): return o.tolist()
    except Exception:
        pass
    if dataclasses.is_dataclass(o):
        return asdict(o)
    return getattr(o, "__dict__", str(o))


def _to_dict(obj):
    """Generic to-dict converter for dataclass, pydantic, or dict."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "model_dump"):   # pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):         # pydantic v1
        return obj.dict()
    if dataclasses.is_dataclass(obj):
        return asdict(obj)
    return getattr(obj, "__dict__", obj)


# ------------------------------
# 4. Save PageText as JSON file
# ------------------------------
def save_page_json(out_dir: Path, page: PageText):
    """
    Save one OCR page result to JSON file.

    Args:
        out_dir: output directory
        page: PageText or dict
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    data = _to_dict(page)
    page_index = (
        data.get("page_index", None)
        if isinstance(data, dict)
        else getattr(page, "page_index", None)
    )

    if page_index is None:
        raise ValueError("save_page_json: missing page_index")

    # page_0001.json, page_0002.json, ...
    file_name = f"page_{int(page_index) + 1:04d}.json"
    out_file = out_dir / file_name

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)

    return out_file
