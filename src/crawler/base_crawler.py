"""
Base class for all crawlers, defining a common interface.
"""
from abc import ABC, abstractmethod

class BaseCrawler(ABC):
    """Abstract base class for a domain-specific crawler."""

    def __init__(self, domain: str, start_url: str):
        """
        Initializes the crawler with its target domain and starting URL.

        Args:
            domain: The domain this crawler is responsible for (e.g., 'daa.uit.edu.vn').
            start_url: The entry point URL for crawling.
        """
        if not domain or not start_url:
            raise ValueError("Domain and start_url cannot be empty.")
        self.domain = domain
        self.start_url = start_url

    @abstractmethod
    async def crawl(self):
        """
        The main method to start the crawling process for the specific domain.
        This must be implemented by all subclasses.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(domain='{self.domain}', start_url='{self.start_url}')>"
