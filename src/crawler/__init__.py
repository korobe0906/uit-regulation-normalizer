"""
This package contains all modules related to web crawling.

It follows a class-based, factory-driven architecture to easily support
multiple domains.

Key components:
- BaseCrawler: The abstract base class that all specific crawlers must inherit from.
- DaaCrawler, UitCrawler: Concrete implementations for specific domains.
- CrawlerFactory: A factory for creating crawler instances based on domain.
- crawl_all: The main entry point function to start crawling all configured domains.
"""

from .base_crawler import BaseCrawler
from .crawler_factory import CrawlerFactory
from .daa_crawler import DaaCrawler
from .uit_crawler import UitCrawler
from .crawler_core import crawl_all

# Explicitly define the public API of the crawler package
__all__ = [
    "BaseCrawler",
    "CrawlerFactory",
    "DaaCrawler",
    "UitCrawler",
    "crawl_all",
]
