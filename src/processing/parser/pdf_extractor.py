"""
Extractor for PDF files using PyMuPDF, with an OCR fallback using Tesseract.
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

from .base_extractor import BaseExtractor

class PdfExtractor(BaseExtractor):
    """Extracts text from PDF files, automatically using OCR for image-based PDFs."""

    def _is_text_meaningful(self, text: str, min_length: int = 100) -> bool:
        """Check if the extracted text is substantial enough."""
        return len(text.strip()) >= min_length

    def _perform_ocr(self, doc: fitz.Document) -> str:
        """
        Performs OCR on each page of the PDF document.
        """
        print("[INFO] PDF appears to be image-based. Falling back to OCR...")
        full_text = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Render page to a high-resolution image for better OCR accuracy
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            # Use Tesseract to extract text, specifying Vietnamese language
            try:
                page_text = pytesseract.image_to_string(img, lang='vie')
                if page_text:
                    full_text.append(page_text)
                print(f"[INFO] OCR processed page {page_num + 1}/{len(doc)}")
            except pytesseract.TesseractNotFoundError:
                print("[ERROR] Tesseract is not installed or not in your PATH. OCR failed.")
                return "" # Stop if Tesseract is not available
            except Exception as ocr_error:
                print(f"[ERROR] An error occurred during OCR on page {page_num + 1}: {ocr_error}")

        return "\n\n---\n\n".join(full_text)

    def extract(self, file_path: str) -> str:
        """
        Opens a PDF and attempts to extract text directly.
        If direct extraction yields little or no text, it falls back to OCR.
        """
        try:
            doc = fitz.open(file_path)
            
            # 1. Try direct text extraction first (fast method)
            direct_text_content = []
            for page in doc:
                direct_text_content.append(page.get_text())
            
            direct_text = "\n".join(direct_text_content)

            # 2. Check if the direct text is meaningful
            if self._is_text_meaningful(direct_text):
                print("[INFO] Successfully extracted text directly from PDF.")
                doc.close()
                return direct_text
            
            # 3. If not, fall back to OCR (slower but more powerful method)
            ocr_text = self._perform_ocr(doc)
            doc.close()
            return ocr_text

        except Exception as e:
            print(f"[ERROR] Failed to process PDF {file_path}: {e}")
            return ""  # Return empty string on failure
