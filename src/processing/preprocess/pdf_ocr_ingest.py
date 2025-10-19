# src/processing/preprocess/pdf_ocr_ingest.py
import argparse, hashlib, re, sys
from pathlib import Path
from .image_ops import pdf_to_images, preprocess_image
from src.processing.preprocess.ocr.factory import build_engine
from src.processing.preprocess.writer import paddle_to_page, save_page_json
import pytesseract

# Chỉ cần khi dùng engine tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="PDF path")
    ap.add_argument("--engine", default="paddle", choices=["paddle", "tesseract"])
    ap.add_argument("--processed_dir", default="data/processed",
                    help="Base output dir; a doc_id subfolder will be created")
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
    pages = pdf_to_images(str(pdf))
    if not pages:
        print("[ERROR] No pages rendered from PDF.", file=sys.stderr)
        sys.exit(3)

    # Build OCR engine
    engine = build_engine(args.engine, lang="vi")

    # Thu thập fulltext
    all_txt_chunks = []

    # 0-based index để khớp writer.PageText.page_index
    for i, pil in enumerate(pages, start=0):
        npimg = preprocess_image(pil)
        h, w = npimg.shape[:2]
        result = engine.extract(npimg)

        # PageText(page_index=i)
        page = paddle_to_page(doc_id, i, w, h, result, min_conf=0.5)

        # Ghi JSON (trả về đường dẫn)
        out_file = save_page_json(out_dir, page)
        print(f"[OK] Page {i+1}/{len(pages)} -> {out_file.name}")

        # Gom text: mỗi dòng một dòng
        if page.lines:
            all_txt_chunks.append("\n".join(l.text for l in page.lines if getattr(l, "text", "")))

    # Xuất fulltext.txt
    fulltext_path = out_dir / "fulltext.txt"
    fulltext_path.write_text("\n\n".join(all_txt_chunks), encoding="utf-8")
    print(f"[DONE] OCR done: {out_dir}")
    print(f"[INFO] Full text: {fulltext_path.name}")

if __name__ == "__main__":
    main()
