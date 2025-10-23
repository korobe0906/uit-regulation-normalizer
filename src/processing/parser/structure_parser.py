#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bước 4 – Structure Parsing:
- Input : 1 file text đã normalize (fulltext_norm.txt)
- Output: JSON cấu trúc Chương → Điều → Khoản → Điểm
Usage:
  python src/parser/structure_parser.py \
    --input data/processed/<doc-id>/fulltext_norm.txt \
    --output data/processed/parsed/<doc-id>.json
"""
from src.config.regex_patterns import (
    CHUONG_RE, DIEU_RE, KHOAN_RE, DIEM_RE,
    CHUONG_FOLD_RE, DIEU_FOLD_RE,
    PAGE_MARK_RE, NOI_NHAN_START_RE, KY_TEN_RE, strip_accents
)

import argparse, json, re
from pathlib import Path

from src.config.regex_patterns import (
    CHUONG_RE, DIEU_RE, KHOAN_RE, DIEM_RE,
    PAGE_MARK_RE, NOI_NHAN_START_RE, KY_TEN_RE
)

def read_text(fp: Path) -> list[str]:
    text = fp.read_text(encoding="utf-8", errors="ignore")
    # Chuẩn hoá \r\n -> \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    return lines

def prefilter(lines: list[str]) -> list[str]:
    """
    - Bỏ marker <<<PAGE n>>>
    - Cắt bỏ block 'Nơi nhận:' đến hết 'khối ký tên'/hết trang
    - Gộp dòng lẻ (nếu dòng trước không kết thúc câu và dòng sau viết thường)
      -> chỉ hỗ trợ nhẹ để parser ổn định
    """
    kept = []
    skipping_noi_nhan = False

    for ln in lines:
        if PAGE_MARK_RE.match(ln.strip()):
            skipping_noi_nhan = False
            continue

        if skipping_noi_nhan:
            # kết thúc khi gặp dòng ký tên hoặc dòng trống dài
            if KY_TEN_RE.match(ln) or ln.strip() == "":
                skipping_noi_nhan = False
            continue

        if NOI_NHAN_START_RE.match(ln):
            skipping_noi_nhan = True
            continue

        kept.append(ln)

    # gộp dòng mềm
    merged = []
    for i, ln in enumerate(kept):
        if not merged:
            merged.append(ln)
            continue
        prev = merged[-1]
        # nếu prev không kết thúc câu và ln bắt đầu chữ thường → nối
        if prev and not re.search(r'[.;:)\]]\s*$', prev.strip()) and ln.strip() and ln.lstrip()[0:1].islower():
            merged[-1] = (prev.rstrip() + " " + ln.lstrip())
        else:
            merged.append(ln)
    return merged

def flush_current_article(current_article, bucket):
    if current_article:
        # Nếu article chưa có text tổng hợp, build từ clauses khi trống
        if 'text' not in current_article or current_article['text'] is None:
            current_article['text'] = current_article.get('text', "").strip()
        bucket.append(current_article)

def parse_structure(lines: list[str]) -> dict:
    content = []
    current_chapter = None
    current_article = None

    for raw in lines:
        line = raw.rstrip()
        folded = strip_accents(line).strip()

        # Skip rỗng
        if not line.strip():
            continue

        # ==== Match Chương ====
        mch = CHUONG_RE.match(line) or CHUONG_FOLD_RE.match(folded)
        if mch:
            # flush article trước khi sang chương mới
            if current_article:
                flush_current_article(current_article, current_chapter['articles'])
                current_article = None
            # tạo chương mới
            roman_or_num = mch.group(1).strip()
            title = (mch.group(2) or "").strip()
            current_chapter = {
                "chapter": f"Chương {roman_or_num}",
                "title": title if title else None,
                "articles": []
            }
            content.append(current_chapter)
            continue

        # ==== Match Điều ====
        md = DIEU_RE.match(line) or DIEU_FOLD_RE.match(folded)
        if md:
            # flush điều cũ
            if current_article:
                flush_current_article(current_article, current_chapter['articles'] if current_chapter else content)
            article_id = int(md.group(1))
            article_title = md.group(2).strip() if md.group(2) else None
            current_article = {
                "id": article_id,
                "title": article_title if article_title else None,
                "text": "",
                "clauses": []
            }
            # Nếu chưa có chương nào, ta giả lập chapter=None (đẩy trực tiếp vào content)
            if current_chapter is None:
                # dùng một 'chapter' ảo để giữ Articles nếu văn bản không có 'Chương'
                current_chapter = {"chapter": None, "title": None, "articles": []}
                content.append(current_chapter)
            continue

        # ==== Match Khoản ====
        mk = KHOAN_RE.match(line)
        if mk and current_article:
            idx = int(mk.group(1))
            text = mk.group(2).strip()
            current_article["clauses"].append({"idx": idx, "text": text, "points": []})
            continue

        # ==== Match Điểm ====
        mp = DIEM_RE.match(line)
        if mp and current_article:
            label = mp.group(1)
            text = mp.group(2).strip()
            # gắn vào khoản gần nhất nếu có, nếu không thì tạo khoản ảo
            if current_article["clauses"]:
                current_article["clauses"][-1]["points"].append({"label": label, "text": text})
            else:
                current_article["clauses"].append({"idx": None, "text": "", "points": [{"label": label, "text": text}]})
            continue

        # ==== Mặc định: nối vào 'text' của Điều hiện tại ====
        if current_article:
            if current_article["text"]:
                current_article["text"] += "\n" + line
            else:
                current_article["text"] = line

    # flush cuối cùng
    if current_article:
        flush_current_article(current_article, current_chapter["articles"] if current_chapter else content)

    return {
        "metadata": {
            "schema": "uit-regulation-structure@v1",
            "levels": ["chapter", "article", "clause", "point"]
        },
        "content": content
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path tới fulltext_norm.txt")
    ap.add_argument("--output", required=False, help="Đường dẫn file JSON xuất ra")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(in_path)

    if args.output:
        out_path = Path(args.output)
    else:
        # data/processed/<doc-id>/fulltext_norm.txt -> data/processed/parsed/<doc-id>.json
        doc_id = in_path.parent.name
        out_path = Path("data/processed/parsed") / f"{doc_id}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = read_text(in_path)
    lines = prefilter(lines)
    parsed = parse_structure(lines)

    # Gọn JSON (giữ Unicode để đọc dễ)
    out_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Parsed structure → {out_path}")

if __name__ == "__main__":
    main()
