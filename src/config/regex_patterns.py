import re
import unicodedata

def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()

# Bản có dấu (giữ nguyên cho đẹp)
CHUONG_RE = re.compile(r'(?im)^\s*Chương\s+([IVXLC\d]+)(?:\s*[-–]\s*(.+))?\s*$')
DIEU_RE   = re.compile(r'(?im)^\s*Điều\s+(\d+)\s*[\.:]?\s*(.*)$')
KHOAN_RE  = re.compile(r'(?m)^\s*(\d+)\.\s+(.*)$')
DIEM_RE   = re.compile(r'(?m)^\s*([a-zA-Z])\)\s+(.*)$')

# Bản “folded” không dấu (chuong/dieu/khoan/diem)
CHUONG_FOLD_RE = re.compile(r'(?im)^\s*chuong\s+([ivxlcd\d]+)(?:\s*[-–]\s*(.+))?\s*$')
DIEU_FOLD_RE   = re.compile(r'(?im)^\s*dieu\s+(\d+)\s*[\.:]?\s*(.*)$')

PAGE_MARK_RE = re.compile(r'^\s*<{2,}PAGE\s+\d+>{2,}\s*$', re.IGNORECASE)
NOI_NHAN_START_RE = re.compile(r'(?im)^\s*Nơi nhận\s*:\s*$')
KY_TEN_RE = re.compile(r'(?im)^\s*(HIỆU TRƯỞNG|PHÓ HIỆU TRƯỞNG|(đã ký)|\(đã ký\))\s*$')
