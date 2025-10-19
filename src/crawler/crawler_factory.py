"""
Factory for creating appropriate crawler instances based on domain.
"""
from typing import Type, Dict
from .base_crawler import BaseCrawler
from .daa_crawler import DaaCrawler
from .uit_crawler import UitCrawler

class CrawlerFactory:
    """A factory to create the correct crawler for a given domain."""

    # This dictionary maps a domain string to a crawler CLASS (a blueprint).
    _crawlers: Dict[str, Type[BaseCrawler]] = {
        "daa.uit.edu.vn": DaaCrawler,
        #"uit.edu.vn": UitCrawler,
    }

    @classmethod
    def register_crawler(cls, domain: str, crawler_class: Type[BaseCrawler]):
        """
        Dynamically registers a new crawler class for a specific domain.
        This allows for extending the factory without modifying its source code.

        Args:
            domain: The domain name to associate with the crawler.
            crawler_class: The crawler class to register (must be a subclass of BaseCrawler).
        """
        if not issubclass(crawler_class, BaseCrawler):
            raise TypeError("crawler_class must be a subclass of BaseCrawler")
        print(f"[INFO] Registering crawler for domain '{domain}': {crawler_class.__name__}")
        cls._crawlers[domain] = crawler_class

    @classmethod
    def get_crawler(cls, domain: str, start_url: str) -> BaseCrawler:
        """
        Instantiates and returns the appropriate crawler for the given domain.

        Args:
            domain: The domain name (e.g., 'daa.uit.edu.vn').
            start_url: The starting URL for the crawl.

        Returns:
            An instance of a BaseCrawler subclass.

        Raises:
            ValueError: If no crawler is registered for the specified domain.
        """
        crawler_class = cls._crawlers.get(domain)

        if not crawler_class:
            raise ValueError(f"No crawler registered for domain: '{domain}'")

        # Return an instance of the class, passing constructor arguments.
        return crawler_class(domain=domain, start_url=start_url)
