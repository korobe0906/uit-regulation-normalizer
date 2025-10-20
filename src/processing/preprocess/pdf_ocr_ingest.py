# src/processing/preprocess/pdf_ocr_ingest.py
import argparse, hashlib, re, sys, os
from pathlib import Path

import numpy as np
import cv2

# PyMuPDF (optional) để phát hiện/trích text với PDF số
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except Exception:
    HAS_FITZ = False

from .image_ops import pdf_to_images, preprocess_image, split_and_upright
from src.processing.preprocess.writer import paddle_to_page, save_page_json
import pytesseract
from src.processing.preprocess.ocr.factory import build_engine as ocr_build_engine

# Chỉ cần khi dùng engine tesseract
pytesseract.pytesseract.tesseract_cmd = os.getenv(
    "TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()

# ---------- PyMuPDF helpers (PDF số) ----------
def page_has_text(pdf_path: str, page_index: int) -> bool:
    if not HAS_FITZ:
        return False
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_index]
        words = page.get_text("words")
        doc.close()
        return bool(words and len(words) > 5)
    except Exception:
        return False

def extract_text_page(pdf_path: str, page_index: int):
    """Trả về (width, height, lines[list{bbox,text,conf_avg,words[]}]) cho PDF số."""
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    w, h = int(page.rect.width), int(page.rect.height)

    lines = []
    # Lấy theo blocks để giữ thứ tự đọc trái->phải, trên->dưới
    blocks = page.get_text("blocks", flags=fitz.TEXTFLAGS_TEXT)  # [(x0,y0,x1,y1,text,...)]
    for b in blocks:
        if len(b) < 5:
            continue
        x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], (b[4] or "").strip()
        if not txt:
            continue
        for ln in [t.strip() for t in txt.splitlines() if t.strip()]:
            lines.append({
                "bbox": [int(x0), int(y0), int(x1), int(y1)],
                "text": ln,
                "conf_avg": 1.0,
                "words": []
            })
    doc.close()
    return w, h, lines

# ---------- Helpers cho xoay theo số trang ----------
def _parse_rotate_pages(spec: str):
    """'1:270,3:180' -> {1:270, 3:180} (chỉ chấp nhận 0/90/180/270)."""
    m = {}
    for item in (spec or "").split(","):
        item = item.strip()
        if not item:
            continue
        try:
            p, d = item.split(":")
            page = int(p.strip())
            deg = int(d.strip())
            if deg in (0, 90, 180, 270):
                m[page] = deg
        except Exception:
            pass
    return m

def _rotate_bgr_by_deg(bgr, deg: int):
    if deg == 90:
        return cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
    if deg == 180:
        return cv2.rotate(bgr, cv2.ROTATE_180)
    if deg == 270:
        return cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return bgr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="PDF path")
    ap.add_argument("--engine", default="paddle", choices=["paddle", "tesseract"])
    ap.add_argument("--processed_dir", default="data/processed",
                    help="Base output dir; a doc_id subfolder will be created")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--poppler_path", default=os.getenv("POPPLER_PATH", None),
                    help="Path tới poppler/bin (Windows). Nếu bỏ trống sẽ auto-detect.")
    ap.add_argument("--fallback", action="store_true",
                    help="Bật fallback Tesseract khi không nhận được chữ với Paddle.")
    ap.add_argument("--limit", type=int, default=None, help="Chỉ OCR số trang đầu (để test nhanh)")
    ap.add_argument("--force_rotate_270", action="store_true",
                    help="Ép xoay toàn bộ các trang 270° (ví dụ trang bị nằm ngang).")
    ap.add_argument("--rotate_pages", default="",
                    help='Xoay theo số trang, ví dụ: "1:270,3:180" (trang 1 xoay 270°, trang 3 xoay 180°)')
    args = ap.parse_args()

    pdf = Path(args.input)
    if not pdf.exists():
        print(f"[ERROR] Input not found: {pdf}", file=sys.stderr)
        sys.exit(2)

    # Tạo doc_id ổn định theo tên file + md5
    doc_id = f"{slugify(pdf.stem)}-{hashlib.md5(pdf.read_bytes()).hexdigest()[:8]}"
    out_dir = Path(args.processed_dir) / doc_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Saving OCR result to: {out_dir.resolve()}")

    # Render PDF -> images
    pages = pdf_to_images(str(pdf), dpi=args.dpi, poppler_path=args.poppler_path)
    if not pages:
        print("[ERROR] No pages rendered from PDF. (Thiếu Poppler trên Windows?)", file=sys.stderr)
        print("=> Cách khắc phục: cài Poppler và truyền --poppler_path C:\\path\\to\\poppler\\bin", file=sys.stderr)
        sys.exit(3)
    else:
        print(f"[INFO] Rendered {len(pages)} page image(s)")

    engine = ocr_build_engine(args.engine, lang="vi")
    pdf_path_str = str(pdf)

    # parse map xoay theo số trang (1-based)
    rotate_map = _parse_rotate_pages(args.rotate_pages)

    # Thu thập fulltext
    all_txt_chunks = []

    for i, pil in enumerate(pages, start=0):
        # Dừng sớm khi limit
        if args.limit is not None and i >= args.limit:
            print(f"[INFO] Dừng sớm sau {args.limit} trang (chế độ test).")
            break

        # ---- Nhánh A: PDF số → bỏ OCR, trích trực tiếp bằng PyMuPDF ----
        if HAS_FITZ and page_has_text(pdf_path_str, i):
            w, h, lines = extract_text_page(pdf_path_str, i)
            data_dict = {
                "document_id": doc_id,
                "page_index": i,
                "width": w,
                "height": h,
                "engine": "pdf_text",
                "meta": None,
                "lines": lines
            }
            out_file = save_page_json(out_dir, data_dict)
            print(f"[OK] Page {i+1}/{len(pages)} -> {out_file.name} (lines={len(lines)}) [pdf_text]")
            if lines:
                all_txt_chunks.append("\n".join(L["text"] for L in lines))
            continue

        # ---- Nhánh B: PDF scan → OCR (Paddle/Tesseract) ----
        # preprocess cơ bản (deskew/denoise và resize < 4000), giữ BGR cho Paddle
        bgr_base = preprocess_image(pil, mode="paddle")

        # Xoay theo số trang nếu được chỉ định
        page_no = i + 1  # 1-based
        if page_no in rotate_map:
            bgr_base = _rotate_bgr_by_deg(bgr_base, rotate_map[page_no])

        # Ép xoay toàn ảnh 270° nếu yêu cầu (tác dụng cho mọi trang)
        if args.force_rotate_270:
            bgr_base = _rotate_bgr_by_deg(bgr_base, 270)

        h, w = bgr_base.shape[:2]

        # Không chia ảnh: split_and_upright() của bạn đang trả về 1 region duy nhất (OSD upright)
        from .image_ops import split_and_upright, prep_for_tesseract_from_bgr
        regions = split_and_upright(bgr_base)  # -> [(0, 0, bgr_rot)]

        # Lưu debug từng phần (1 phần)
        for r_idx, (x_off, y_off, bgr_rot) in enumerate(regions, start=1):
            cv2.imwrite(str(out_dir / f"debug_pre_{i+1:03d}_{args.engine}_part{r_idx}.png"), bgr_rot)

        # OCR từng phần và gộp kết quả
        merged = []
        def _to_dict_items(items):
            out = []
            for it in (items or []):
                # paddle classic: [poly, (text, conf)]
                if isinstance(it, (list, tuple)) and len(it) >= 2 and isinstance(it[0], (list, tuple)):
                    poly = it[0]
                    try:
                        xs = [float(p[0]) for p in poly]; ys = [float(p[1]) for p in poly]
                        bbox = [min(xs), min(ys), max(xs), max(ys)]
                    except Exception:
                        bbox = [0,0,0,0]
                    ti = it[1]
                    if isinstance(ti, (list, tuple)) and len(ti) >= 2:
                        txt, cf = str(ti[0] or ""), float(ti[1])
                    elif isinstance(ti, dict):
                        txt, cf = str(ti.get("text","") or ""), float(ti.get("conf", ti.get("score", 0.0)) or 0.0)
                    else:
                        txt, cf = str(ti or ""), 1.0
                    out.append({"text": txt, "conf": cf, "bbox": bbox})
                elif isinstance(it, dict):
                    out.append({"text": str(it.get("text","") or ""), "conf": float(it.get("conf", it.get("score", 0.0)) or 0.0),
                                "bbox": list(it.get("bbox", [0,0,0,0]))})
            return out

        for r_idx, (x_off, y_off, bgr_rot) in enumerate(regions, start=1):
            items = None
            try:
                items = engine.extract(bgr_rot)
            except Exception as e:
                print(f"[WARN] Page {i+1}: {args.engine} exception(part) -> {type(e).__name__}: {e}")

            weak = (items is None) or (not isinstance(items, list)) or (len(items) <= 4)

            # fallback nếu cần
            if weak and args.engine == "paddle" and args.fallback:
                print(f"[WARN] Page {i+1}: Paddle weak on a region → try Tesseract fallback")
                tess_engine = ocr_build_engine("tesseract", lang="vi")
                bgr_tess = prep_for_tesseract_from_bgr(bgr_rot)
                cv2.imwrite(str(out_dir / f"debug_pre_{i+1:03d}_tesseract_part{r_idx}.png"), bgr_tess)
                try:
                    items = tess_engine.extract(bgr_tess)
                except Exception as e:
                    print(f"[ERROR] Page {i+1}: Tesseract exception(part) -> {type(e).__name__}: {e}")
                    items = []

            for obj in _to_dict_items(items):
                x0, y0, x1, y1 = obj["bbox"]
                obj["bbox"] = [x0 + x_off, y0 + y_off, x1 + x_off, y1 + y_off]
                merged.append(obj)

        print(f"[DEBUG] Page {i+1}: regions={len(regions)}, merged_items={len(merged)}")

        page = paddle_to_page(doc_id, i, w, h, merged, min_conf=0.2)
        out_file = save_page_json(out_dir, page)
        print(f"[OK] Page {i+1}/{len(pages)} -> {out_file.name} (lines={len(page.lines) if hasattr(page,'lines') else 0})")

        if getattr(page, "lines", None):
            all_txt_chunks.append("\n".join(getattr(l, "text", "") for l in page.lines if getattr(l, "text", "")))

    # Xuất fulltext.txt
    fulltext_path = out_dir / "fulltext.txt"
    fulltext_path.write_text("\n\n".join(all_txt_chunks), encoding="utf-8")
    print(f"[DONE] OCR done: {out_dir}")
    print(f"[INFO] Full text: {fulltext_path.name}")

if __name__ == "__main__":
    main()
