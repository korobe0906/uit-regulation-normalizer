"""
This package contains modules for extracting text content from various file formats.

Key components:
- BaseExtractor: The abstract base class for all file extractors.
- ExtractorFactory: A factory for creating extractor instances based on file extension.
- extract_all, extract_domain, extract_folder: Core functions to run the extraction process.
"""

from .base_extractor import BaseExtractor
from .extractor_factory import ExtractorFactory
from .extractor_core import extract_all, extract_domain, extract_folder

__all__ = [
    "BaseExtractor",
    "ExtractorFactory",
    "extract_all",
    "extract_domain",
    "extract_folder",
]
