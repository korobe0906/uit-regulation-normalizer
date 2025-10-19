"""
Extractor for DOCX files using the python-docx library.
"""
import docx

from .base_extractor import BaseExtractor

class DocxExtractor(BaseExtractor):
    """Extracts text content from DOCX files."""

    def extract(self, file_path: str) -> str:
        """
        Opens a DOCX file and extracts all text from its paragraphs.

        Args:
            file_path: The path to the DOCX file.

        Returns:
            The concatenated text content of all paragraphs.
        """
        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"[ERROR] Failed to extract text from DOCX {file_path}: {e}")
            return "" # Return empty string on failure
