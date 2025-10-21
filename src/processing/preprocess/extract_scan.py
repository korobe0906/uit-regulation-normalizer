# extract_scan.py
import cv2
import pytesseract
from pytesseract import Output
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import List

def ocr_page_to_lines(image: np.ndarray, lang="vie+eng") -> List[str]:
    config = "--oem 1 --psm 3 -c preserve_interword_spaces=1"
    # phương án nhanh: image_to_string cho fulltext theo dòng
    txt = pytesseract.image_to_string(image, lang=lang, config=config)
    return [s for s in txt.splitlines() if s.strip()]

def detect_tables_csv(image: np.ndarray) -> List[List[List[str]]]:
    """
    Heuristic cho bảng có đường kẻ (bordered tables):
    - Tìm line ngang/dọc bằng morphology
    - Cắt ô theo lưới -> OCR từng cell -> rows (CSV)
    Trả về: List[table] -> List[row] -> List[cell_text]
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim==3 else image.copy()
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 15, 10)

    # line ngang
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40,1))
    h_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, h_kernel, iterations=1)

    # line dọc
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,40))
    v_lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, v_kernel, iterations=1)

    table_mask = cv2.add(h_lines, v_lines)
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    tables = []
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        if w*h < 5000:  # bỏ nhiễu nhỏ
            continue
        roi = image[y:y+h, x:x+w]

        # tìm ô bằng intersect lưới (đơn giản: chia theo proj profile)
        # 1) cột
        colproj = np.sum(v_lines[y:y+h, x:x+w] > 0, axis=0)
        cols = np.where(colproj>0)[0]
        # 2) hàng
        rowproj = np.sum(h_lines[y:y+h, x:x+w] > 0, axis=1)
        rows = np.where(rowproj>0)[0]

        # nếu không đủ lưới, bỏ qua (table không có khung)
        if len(cols)<2 or len(rows)<2: 
            continue

        # tìm ranh giới cell từ peaks (nhóm liên tiếp)
        def split_bound(idxs):
            bounds=[]
            start=idxs[0]
            for i in range(1,len(idxs)):
                if idxs[i]!=idxs[i-1]+1:
                    bounds.append((start, idxs[i-1]))
                    start=idxs[i]
            bounds.append((start, idxs[-1]))
            # lấy tâm các line làm ranh giới
            return [int((a+b)/2) for a,b in bounds]

        col_bounds = split_bound(cols)
        row_bounds = split_bound(rows)

        # dựng grid (cell bằng khoảng giữa 2 đường)
        cells = []
        for r in range(len(row_bounds)-1):
            row_cells=[]
            y0 = row_bounds[r]
            y1 = row_bounds[r+1]
            for c in range(len(col_bounds)-1):
                x0 = col_bounds[c]
                x1 = col_bounds[c+1]
                cell = roi[y0:y1, x0:x1]
                text = pytesseract.image_to_string(
                    cell, lang="vie+eng",
                    config="--oem 1 --psm 7 -c preserve_interword_spaces=1"
                )
                row_cells.append(text.strip())
            cells.append(row_cells)
        tables.append(cells)
    return tables

def save_scan_tables(processed_dir: Path, page_idx: int, tables: List[List[List[str]]]):
    out_dir = processed_dir / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    for ti, rows in enumerate(tables, 1):
        with (out_dir / f"page-{page_idx+1}-table-{ti}.csv").open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
