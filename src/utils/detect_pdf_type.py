import fitz  # PyMuPDF

def is_text_pdf(path:str)->bool:
    doc = fitz.open(path)
    try:
        for p in doc:
            if p.get_text("text").strip():
                return True
        return False
    finally:
        doc.close()
