# utils_text.py
import re, csv
from pathlib import Path

_DOTS_LEADER = re.compile(r"\.{3,}")
_MULTI_SPACE = re.compile(r"[ \t\u00A0]{2,}")

_WHITELIST_STARTS = (
    "QUYẾT ĐỊNH", "QUY DINH", "QUY CHE", "Căn cứ", "Can cu",
    "Nơi nhận", "Noi nhan", "Ký tên", "Ky ten", "KT.", "TM.", "HIỆU TRƯỞNG", "HIEU TRUONG"
)

def _looks_like_header_footer(line: str) -> bool:
    # Heuristic rất nhẹ: những thứ hay là header/footer của trường
    s = line.upper().strip()
    if not s: return False
    toks = ("ĐẠI HỌC QUỐC GIA", "DHQG", "TRƯỜNG ĐH", "TRUONG DAI HOC",
            "CỘNG HÒA XÃ HỘI", "CONG HOA XA HOI", "Trang ", "Page ")
    return any(t in s for t in toks)

def _normalize_line(s: str) -> str:
    s = s.rstrip()
    s = _DOTS_LEADER.sub("", s)                     # bỏ ........
    s = s.replace("./.", ".")                       # ./.
    s = re.sub(r"(\w)-\s+\b", r"\1", s)             # Hạnh- phúc -> Hạnh phúc
    s = _MULTI_SPACE.sub(" ", s)                    # co space
    s = re.sub(r"^\|\s*", "", s)                    # bỏ '|' đầu dòng
    return s.strip()

def drop_repeating_headers_footers(paged_lines, loose=False):
    """
    Xoá header/footer lặp theo trang. Nếu loose=True → rất nhẹ tay.
    Với tài liệu có <= 3 trang, tránh xoá mạnh (dễ mất nội dung).
    """
    if loose or len(paged_lines) <= 3:
        # chỉ bỏ dòng “rõ ràng” là header/footer
        out = []
        for L in paged_lines:
            kept = []
            for s in L:
                if _looks_like_header_footer(s):
                    continue
                kept.append(s)
            out.append(kept)
        return out

    # Mặc định (tài liệu dài): thống kê lặp lại >=60% số trang
    from collections import Counter
    head_cand, foot_cand = Counter(), Counter()
    for L in paged_lines:
        if L:
            head_cand[L[0]] += 1
            foot_cand[L[-1]] += 1
        if len(L) >= 2:
            head_cand[" ".join(L[:2])] += 1
            foot_cand[" ".join(L[-2:])] += 1

    th = max(2, int(0.6 * len(paged_lines)))
    heads = {k for k, v in head_cand.items() if v >= th}
    foots = {k for k, v in foot_cand.items() if v >= th}

    out = []
    for L in paged_lines:
        joined = " ".join(L)
        for token in sorted(heads | foots, key=len, reverse=True):
            joined = joined.replace(token, "")
        # tách lại thành dòng “thô”
        tmp = [x.strip() for x in joined.split("  ") if x.strip()]
        out.append(tmp)
    return out

def write_fulltext_files(processed_dir: Path, paged_lines_raw, loose=False):
    raw_path  = processed_dir / "fulltext_raw.txt"
    norm_path = processed_dir / "fulltext_norm.txt"

    # RAW
    with raw_path.open("w", encoding="utf-8") as f:
        for p, L in enumerate(paged_lines_raw, 1):
            f.write(f"<<<PAGE {p}>>>\n")
            for s in L:
                f.write(_normalize_line(s) + "\n")

    # Clean header/footer
    cleaned_pages = drop_repeating_headers_footers(paged_lines_raw, loose=loose)

    # NORM
    norm_lines = []
    for p, L in enumerate(cleaned_pages, 1):
        # giữ whitelisted lines bất kể có giống header/footer
        kept = []
        for s in L:
            ss = _normalize_line(s)
            if not ss:
                continue
            if any(ss.upper().startswith(w.upper()) for w in _WHITELIST_STARTS):
                kept.append(ss)
            else:
                kept.append(ss)
        if kept:
            norm_lines.append(f"<<<PAGE {p}>>>")
            # bỏ dòng trống liên tiếp
            prev_blank = False
            for line in kept:
                blank = (line.strip() == "")
                if blank and prev_blank:
                    continue
                norm_lines.append(line)
                prev_blank = blank

    norm_path.write_text("\n".join(norm_lines), encoding="utf-8")
