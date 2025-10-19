"""
This package groups all data processing modules, including cleaning and extraction.
"""

# Expose key components from the cleaner submodule
from .cleaner import (
    BaseCleaner,
    CleanerFactory,
    clean_all,
    clean_domain,
    clean_folder
)

# Expose key components from the extractor submodule
from .extractor import (
    BaseExtractor,
    ExtractorFactory,
    extract_all,
    extract_domain,
    extract_folder
)

__all__ = [
    # Cleaner components
    "BaseCleaner",
    "CleanerFactory",
    "clean_all",
    "clean_domain",
    "clean_folder",
    
    # Extractor components
    "BaseExtractor",
    "ExtractorFactory",
    "extract_all",
    "extract_domain",
    "extract_folder",
]
