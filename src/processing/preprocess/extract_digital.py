# extract_digital.py
import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import Tuple, List

def extract_digital_pdf(pdf_path: Path) -> Tuple[List[List[str]], List[Tuple[int, int, List[List[str]]]]]:
    """
    Trả về:
      - paged_lines_raw: List[page] -> List[str]
      - tables: list các bảng dạng (page_idx, table_idx, rows)
    """
    paged_lines_raw = []

    # Text theo thứ tự đọc (PyMuPDF blocks -> lines)
    with fitz.open(pdf_path) as doc:
        for page in doc:
            lines = []
            # dùng page.get_text("text") là nhanh nhất & đủ tốt
            txt = page.get_text("text")  # đã theo dòng
            lines = [s for s in txt.splitlines()]
            paged_lines_raw.append(lines)

    # Bảng (pdfplumber) -> CSV rows
    tables = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for pi, page in enumerate(pdf.pages):
            try:
                tbs = page.extract_tables() or []
            except Exception:
                tbs = []
            for ti, tb in enumerate(tbs):
                # tb: List[List[str]]
                tables.append((pi, ti, [[(c or "").strip() for c in row] for row in tb]))
    return paged_lines_raw, tables

def save_tables_to_csv(processed_dir: Path, tables):
    tables_dir = processed_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    for (pi, ti, rows) in tables:
        out = tables_dir / f"page-{pi+1}-table-{ti+1}.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
