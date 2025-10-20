# src/processing/preprocess/writer.py
import json
import dataclasses
from dataclasses import asdict
from pathlib import Path
from typing import List, Tuple, Any, Dict, Iterable
from .page_schema import PageText, Line, Word

# ========== NEW: helpers nhận dạng dict từ paddlex/pipeline ==========
def _dict_get(d: Dict, *keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default

def _poly_to_bbox(poly: Iterable) -> Tuple[float, float, float, float]:
    try:
        xs, ys = [], []
        # poly có thể là [(x,y),...], hoặc {"points":[[x,y],...]}
        if isinstance(poly, dict):
            pts = _dict_get(poly, "points", "poly", "polygon", "quad", default=None)
            if pts is None:
                return (0.0, 0.0, 0.0, 0.0)
            for p in pts:
                xs.append(float(p[0])); ys.append(float(p[1]))
        else:
            for p in poly:
                xs.append(float(p[0])); ys.append(float(p[1]))
        return (min(xs), min(ys), max(xs), max(ys))
    except Exception:
        return (0.0, 0.0, 0.0, 0.0)

def _bbox_like(obj: Any) -> Tuple[float, float, float, float]:
    # hỗ trợ nhiều kiểu: (x0,y0,x1,y1) hoặc dict {"x0":..} / {"bbox":[x0,y0,x1,y1]} / {"rect":{...}} ...
    try:
        if isinstance(obj, (list, tuple)) and len(obj) == 4:
            return float(obj[0]), float(obj[1]), float(obj[2]), float(obj[3])
        if isinstance(obj, dict):
            if "bbox" in obj and isinstance(obj["bbox"], (list, tuple)) and len(obj["bbox"]) == 4:
                x0,y0,x1,y1 = obj["bbox"]; return float(x0), float(y0), float(x1), float(y1)
            if {"x0","y0","x1","y1"}.issubset(obj.keys()):
                return float(obj["x0"]), float(obj["y0"]), float(obj["x1"]), float(obj["y1"])
            # một số pipeline trả "poly"/"points"
            poly = _dict_get(obj, "points", "poly", "polygon", "quad", default=None)
            if poly is not None:
                return _poly_to_bbox(poly)
    except Exception:
        pass
    return (0.0, 0.0, 0.0, 0.0)

# ========== NEW: normalize mọi định dạng paddle_result về list of (bbox, text, conf) ==========
def _flatten_paddle_result(paddle_result: Any) -> List[Tuple[Tuple[float,float,float,float], str, float]]:
    """
    Trả về danh sách (bbox, text, conf) từ nhiều biến thể output:
      - Cổ điển: [ [poly, (text, conf)], ... ]
      - Paddlex dict: mỗi phần tử có thể là dict với keys: text/label, score/conf, bbox/poly/points
      - List 'per-page': [[...page0...], [...page1...]]
    """
    out: List[Tuple[Tuple[float,float,float,float], str, float]] = []

    if paddle_result is None:
        return out

    # case: per-page list [[...], [...]]
    if isinstance(paddle_result, list) and paddle_result and isinstance(paddle_result[0], list):
        # nối phẳng luôn — caller sẽ chọn page tương ứng nếu muốn
        items = []
        for page_items in paddle_result:
            items.extend(page_items or [])
    else:
        items = paddle_result if isinstance(paddle_result, list) else [paddle_result]

    for it in items:
        # (A) Cổ điển: [poly, (text, conf), ...]
        if isinstance(it, (list, tuple)) and len(it) >= 2:
            bbox_pts = it[0]
            text_info = it[1]
            text, conf = "", 0.0
            if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                text, conf = text_info[0], text_info[1]
            elif isinstance(text_info, dict):
                text = _dict_get(text_info, "text", "label", default="")
                conf = _dict_get(text_info, "score", "conf", "confidence", default=1.0) or 0.0
            bbox = _poly_to_bbox(bbox_pts)
            try:
                conf = float(conf)
            except Exception:
                conf = 0.0
            if text is None:
                text = ""
            out.append((bbox, str(text).strip(), conf))
            continue

        # (B) Dict-style (paddlex / structure / custom)
        if isinstance(it, dict):
            text = _dict_get(it, "text", "label", "value", default="")
            conf = _dict_get(it, "score", "conf", "confidence", default=1.0) or 0.0
            bbox = _bbox_like(it)
            try:
                conf = float(conf)
            except Exception:
                conf = 0.0

            # Nếu text là 1 đoạn nhiều dòng → tách thành từng dòng
            if isinstance(text, str):
                lines = [t.strip() for t in text.splitlines() if t.strip()]
                if lines:
                    for ln in lines:
                        out.append((bbox, ln, conf))
                else:
                    out.append((bbox, "", conf))
            else:
                out.append((bbox, str(text), conf))
            continue

        # (C) Fallback: chuỗi trơn
        if isinstance(it, str):
            out.append(((0.0,0.0,0.0,0.0), it.strip(), 1.0))

    return out

def _parse_paddle_line(line: Any) -> Tuple[Tuple[float, float, float, float], str, float]:
    """
    Hỗ trợ:
      - Paddle classic: [poly, (text, conf)]
      - Dict (tesseract/custom): {"text":..., "conf":..., "bbox":[x0,y0,x1,y1]}
    """
    # --- dict style (tesseract) ---
    if isinstance(line, dict):
        text = str(line.get("text", "") or "").strip()
        conf = line.get("conf", 0.0)
        try:
            conf = float(conf)
        except Exception:
            conf = 0.0
        # chuẩn hóa conf về 0..1
        if conf > 1.5 and conf <= 100.0:
            conf = conf / 100.0
        elif conf > 100.0:
            conf = min(1.0, conf / 3000.0)  # phòng trường hợp scale rất lớn như bạn gặp
        bbox = line.get("bbox", [0, 0, 0, 0])
        try:
            x0, y0, x1, y1 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        except Exception:
            x0 = y0 = x1 = y1 = 0.0
        return (x0, y0, x1, y1), text, conf

    # --- paddle classic ---
    if not isinstance(line, (list, tuple)) or len(line) < 2:
        return (0.0, 0.0, 0.0, 0.0), "", 0.0

    bbox_pts = line[0]
    text_info = line[1]

    # Extract text/conf
    if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
        text, conf = text_info[0], text_info[1]
    elif isinstance(text_info, dict):
        text = text_info.get("text", "")
        conf = text_info.get("conf", text_info.get("score", 0.0))
    else:
        text, conf = str(text_info), 1.0

    # poly -> bbox
    try:
        xs = [float(p[0]) for p in bbox_pts]
        ys = [float(p[1]) for p in bbox_pts]
        bbox = (min(xs), min(ys), max(xs), max(ys))
    except Exception:
        bbox = (0.0, 0.0, 0.0, 0.0)

    try:
        conf = float(conf)
        if conf > 1.5 and conf <= 100.0:
            conf = conf / 100.0  # nếu đến từ tesseract mà đi nhầm nhánh
    except Exception:
        conf = 0.0

    return bbox, str(text), conf


def paddle_to_page(
    doc_id: str,
    page_idx: int,
    w: int,
    h: int,
    paddle_result: Any,
    min_conf: float = 0.5
) -> PageText:
    # unwrap nếu là kiểu [[page0], [page1], ...]
    if isinstance(paddle_result, list) and paddle_result and isinstance(paddle_result[0], list):
        page_items = paddle_result[page_idx] if 0 <= page_idx < len(paddle_result) else []
    else:
        page_items = paddle_result or []

    lines: List[Line] = []
    for item in page_items:
        bbox, text, conf = _parse_paddle_line(item)
        # lọc bbox rỗng & text rỗng
        if (bbox[0] == bbox[2] and bbox[1] == bbox[3]) or (bbox[2] - bbox[0] < 1 or bbox[3] - bbox[1] < 1):
            continue
        if not text or not text.strip():
            continue
        if conf < min_conf:
            continue
        lines.append(Line(text=text.strip(), bbox=bbox, conf=float(conf), words=[]))

    # sắp xếp trên-dưới, trái-phải cho ổn định
    lines.sort(key=lambda L: (L.bbox[1], L.bbox[0]))

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
