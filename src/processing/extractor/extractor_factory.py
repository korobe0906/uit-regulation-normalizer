"""
Factory for creating appropriate file content extractors.
"""
import os
from typing import Type, Dict

from .base_extractor import BaseExtractor
from .pdf_extractor import PdfExtractor
from .docx_extractor import DocxExtractor
from .xlsx_extractor import XlsxExtractor

class ExtractorFactory:
    """A factory to create the correct extractor for a given file type."""

    _extractors: Dict[str, Type[BaseExtractor]] = {
        ".pdf": PdfExtractor,
        ".docx": DocxExtractor,
        ".xlsx": XlsxExtractor,
    }

    @classmethod
    def register_extractor(cls, extension: str, extractor_class: Type[BaseExtractor]):
        """
        Dynamically registers a new extractor class for a specific file extension.
        """
        if not extension.startswith('.'):
            raise ValueError("Extension must start with a dot (e.g., '.pdf')")
        if not issubclass(extractor_class, BaseExtractor):
            raise TypeError("extractor_class must be a subclass of BaseExtractor")
        
        print(f"[INFO] Registering extractor for extension '{extension}': {extractor_class.__name__}")
        cls._extractors[extension] = extractor_class

    @classmethod
    def get_extractor(cls, file_path: str) -> BaseExtractor:
        """
        Instantiates and returns the appropriate extractor for the given file path.

        Raises:
            ValueError: If the file extension is not supported.
        """
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        extractor_class = cls._extractors.get(extension)

        if extractor_class:
            return extractor_class()
        else:
            raise ValueError(f"Unsupported file extension: '{extension}'")
