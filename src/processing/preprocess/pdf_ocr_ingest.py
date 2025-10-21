# src/processing/preprocess/pdf_ocr_ingest.py
import argparse, hashlib, re, sys, os
from pathlib import Path
from typing import List
import numpy as np
import cv2
import pytesseract

from .utils_text import write_fulltext_files
from .extract_digital import extract_digital_pdf, save_tables_to_csv
from .extract_scan import ocr_page_to_lines, detect_tables_csv, save_scan_tables
from .image_ops import pdf_to_images, preprocess_image, split_and_upright
from src.processing.preprocess.writer import paddle_to_page, save_page_json
from src.processing.preprocess.ocr.factory import build_engine as ocr_build_engine

# PyMuPDF (optional) để phát hiện/trích text với PDF số
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except Exception:
    HAS_FITZ = False

# Chỉ cần khi dùng engine tesseract
pytesseract.pytesseract.tesseract_cmd = os.getenv(
    "TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()

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
    ap.add_argument("--processed_dir", default="data/processed",
                    help="Base output dir; a doc_id subfolder will be created")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--poppler_path", default=os.getenv("POPPLER_PATH", None),
                    help="Path tới poppler/bin (Windows). Nếu bỏ trống sẽ auto-detect.")
    ap.add_argument("--fallback", action="store_true",
                    help="Bật fallback Tesseract khi không nhận được chữ với Paddle.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Chỉ OCR số trang đầu (để test nhanh)")
    ap.add_argument("--force_rotate_270", action="store_true",
                    help="Ép xoay toàn bộ các trang 270° (ví dụ trang nằm ngang).")
    ap.add_argument("--rotate_pages", default="",
                    help='Xoay theo số trang, ví dụ: "1:270,3:180"')
    ap.add_argument("--engine", default="auto",
                    choices=["auto", "paddle", "tesseract", "hybrid"],
                    help="auto: PDF số→text layer, PDF scan→tesseract; hybrid: paddle + fallback tesseract")
    ap.add_argument("--tables", action="store_true",
                    help="Trích bảng ra CSV nếu phát hiện được")
    ap.add_argument("--norm_loose", action="store_true",
                help="Chuẩn hoá nhẹ tay: không xoá header/footer lặp và hạn chế dọn rác.")
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

    # Render PDF -> images (dù PDF số vẫn render để thống nhất debug)
    pages = pdf_to_images(str(pdf), dpi=args.dpi, poppler_path=args.poppler_path)
    if not pages:
        print("[ERROR] No pages rendered from PDF. (Thiếu Poppler trên Windows?)", file=sys.stderr)
        print("=> Cài Poppler và truyền --poppler_path C:\\path\\to\\poppler\\bin", file=sys.stderr)
        sys.exit(3)
    else:
        print(f"[INFO] Rendered {len(pages)} page image(s)")

    # hybrid = paddle + fallback tesseract
    effective_engine = args.engine
    if args.engine == "hybrid":
        effective_engine = "paddle"
        args.fallback = True
    engine = ocr_build_engine(effective_engine, lang="vie+eng")

    # Bảng từ PDF số (làm một lần nếu bật --tables)
    if args.tables and HAS_FITZ:
        try:
            _, tables = extract_digital_pdf(pdf)
            save_tables_to_csv(out_dir, tables)
        except Exception as e:
            print(f"[WARN] table extract (digital) failed: {e}")

    rotate_map = _parse_rotate_pages(args.rotate_pages)
    fitz_doc = fitz.open(str(pdf)) if HAS_FITZ else None
    total_pages = len(pages)

    # Thu thập text theo từng trang để xuất RAW/NORM
    paged_lines_raw: List[List[str]] = []
    # Giữ lại file cũ để so sánh
    all_txt_chunks: List[str] = []

    for i, pil in enumerate(pages, start=0):
        if args.limit is not None and i >= args.limit:
            print(f"[INFO] Dừng sớm sau {args.limit} trang (test).")
            break

        # ---- Nhánh A: PDF số → bỏ OCR, trích trực tiếp bằng PyMuPDF ----
        has_text = False
        if HAS_FITZ and fitz_doc is not None:
            try:
                page = fitz_doc[i]
                words = page.get_text("words")
                has_text = bool(words and len(words) > 5)
            except Exception:
                has_text = False

        if args.engine in ("auto",) and has_text:
            w, h = int(page.rect.width), int(page.rect.height)
            blocks = page.get_text("blocks", flags=fitz.TEXTFLAGS_TEXT)
            lines = []
            for b in blocks or []:
                if len(b) >= 5:
                    x0, y0, x1, y1, txt = b[0], b[1], b[2], b[3], (b[4] or "").strip()
                    if txt:
                        for ln in [t.strip() for t in txt.splitlines() if t.strip()]:
                            lines.append({"bbox":[int(x0),int(y0),int(x1),int(y1)],
                                          "text":ln,"conf_avg":1.0,"words":[]})
            data_dict = {
                "document_id": doc_id,
                "page_index": i,
                "width": w, "height": h,
                "engine": "pdf_text",
                "meta": None,
                "lines": lines
            }
            out_file = save_page_json(out_dir, data_dict)
            print(f"[OK] Page {i+1}/{total_pages} -> {out_file.name} (lines={len(lines)}) [pdf_text]")

            page_lines = [L["text"] for L in lines]
            paged_lines_raw.append(page_lines)
            all_txt_chunks.append("\n".join(page_lines))
            continue

        # ---- Nhánh B: PDF scan → OCR (Paddle/Tesseract) ----
        mode = "paddle" if effective_engine == "paddle" else "tesseract"
        bgr_base = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        page_no = i + 1  # 1-based
        if page_no in rotate_map:
            bgr_base = _rotate_bgr_by_deg(bgr_base, rotate_map[page_no])
        if args.force_rotate_270:
            bgr_base = _rotate_bgr_by_deg(bgr_base, 270)

        h, w = bgr_base.shape[:2]
        #regions = split_and_upright(bgr_base)  # -> [(0, 0, bgr_rot)]
        regions = [(0, 0, bgr_base)]

        for r_idx, (x_off, y_off, bgr_rot) in enumerate(regions, start=1):
            #cv2.imwrite(str(out_dir / f"debug_pre_{i+1:03d}_{args.engine}_part{r_idx}.png"), bgr_rot)
            # ngay sau render từ pdf_to_images, trước preprocess:
            cv2.imwrite(str(out_dir / f"debug_render_{i+1:03d}.png"), cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR))
            # ngay sau preprocess_image:
            #cv2.imwrite(str(out_dir / f"debug_preprocess_{i+1:03d}.png"), bgr_base)

        merged = []
        def _to_dict_items(items):
            out = []
            for it in (items or []):
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
                if args.engine == "auto":
                    from .image_ops import prep_for_tesseract_from_bgr
                    bgr_tess = prep_for_tesseract_from_bgr(bgr_rot)
                    tess_engine = ocr_build_engine("tesseract", lang="vie+eng")
                    items = tess_engine.extract(bgr_tess)
                else:
                    items = engine.extract(bgr_rot)
            except Exception as e:
                print(f"[WARN] Page {i+1}: {args.engine} exception(part) -> {type(e).__name__}: {e}")

            weak = (items is None) or (not isinstance(items, list)) or (len(items) <= 3)
            if not weak:
                try:
                    avg_conf = sum(float(getattr(x, "conf", 0) if not isinstance(x, dict) else x.get("conf", 0))
                                   for x in items) / max(len(items), 1)
                    if avg_conf < 0.35:
                        weak = True
                except Exception:
                    pass
            if weak and args.engine == "paddle" and args.fallback:
                print(f"[WARN] Page {i+1}: Paddle weak on a region → try Tesseract fallback")
                tess_engine = ocr_build_engine("tesseract", lang="vie+eng")
                from .image_ops import prep_for_tesseract_from_bgr
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

        # ====== GHÉP DÒNG CHO RAW/NORM (scan) ======
        # Ưu tiên image_to_string để có layout theo dòng ổn định
        try:
            config = "--oem 1 --psm 3 -c preserve_interword_spaces=1"
            line_text = pytesseract.image_to_string(bgr_base, lang="vie+eng", config=config)
            page_lines = [s for s in line_text.splitlines() if s.strip()]
        except Exception:
            page_lines = [getattr(l, "text", "") for l in getattr(page, "lines", []) if getattr(l, "text", "")]
        paged_lines_raw.append(page_lines)

        # Giữ file fulltext cũ để so sánh
        if getattr(page, "lines", None):
            all_txt_chunks.append("\n".join(getattr(l, "text", "") for l in page.lines if getattr(l, "text", "")))
        else:
            all_txt_chunks.append("\n".join(page_lines))

        # Bảng (scan) nếu bật --tables
        if args.tables:
            try:
                tables = detect_tables_csv(bgr_base)
                if tables:
                    save_scan_tables(out_dir, i, tables)
            except Exception as e:
                print(f"[WARN] table detect (scan) failed on page {i+1}: {e}")

    # ====== Xuất 2 phiên bản RAW / NORM ======
    write_fulltext_files(out_dir, paged_lines_raw, loose=args.norm_loose)

    # (Tuỳ chọn) giữ file cũ để so sánh
    fulltext_path = out_dir / "fulltext.txt"
    fulltext_path.write_text("\n\n".join(all_txt_chunks), encoding="utf-8")

    if HAS_FITZ and 'fitz_doc' in locals() and fitz_doc is not None:
        fitz_doc.close()

    print(f"[DONE] OCR done: {out_dir}")
    print(f"[INFO] Full text (legacy): {fulltext_path.name}")
    print(f"[INFO] RAW/NORM written: fulltext_raw.txt, fulltext_norm.txt")

if __name__ == "__main__":
    main()
