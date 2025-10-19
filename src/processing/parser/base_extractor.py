"""
Defines the base interface for all file content extractors.
"""
from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    """
    Abstract base class for a file content extractor.
    Each subclass is responsible for implementing the extraction for a specific file type.
    """

    @abstractmethod
    def extract(self, file_path: str) -> str:
        """
        Extracts text content from a given file.

        Args:
            file_path: The absolute path to the file to be processed.

        Returns:
            A string containing the extracted text content.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
