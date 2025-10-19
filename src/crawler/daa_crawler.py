"""
Crawler implementation for daa.uit.edu.vn.
"""
import os
import re

from crawl4ai import (
    AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig,
    BestFirstCrawlingStrategy, KeywordRelevanceScorer, FilterChain, DomainFilter
)

from src.config import RAW_DATA_DIR, MAX_PAGES_PER_DOMAIN
from src.crawler.base_crawler import BaseCrawler
from src.crawler.crawler_helper import (
    create_or_get_folder_for_url, download_file, extract_title_from_content,
    filter_downloadable_links, save_crawled_data, should_exclude_node_url
)
from src.utils.url_utils import make_absolute_url


class DaaCrawler(BaseCrawler):
    """Crawler specifically for 'daa.uit.edu.vn'."""

    async def crawl(self):
        """Executes the crawling logic for DAA website."""
        print(f"Initializing DAA crawler for domain: {self.domain}")

        scorer = KeywordRelevanceScorer(
            keywords=[
                "thong-bao", "page", "trang", "lich-thi", "quy-dinh", "tot-nghiep",
                "hoc-tap", "ke-hoach", "ban-hanh", "cap-nhat", "ky-thi", "khao-sat",
                "2022", "2023", "2024", "2025"
            ],
            weight=0.8
        )

        filter_chain = FilterChain([
            DomainFilter(allowed_domains=[self.domain]),
        ])

        strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            url_scorer=scorer,
            max_pages=MAX_PAGES_PER_DOMAIN,
            filter_chain=filter_chain,
        )

        browser_config = BrowserConfig(verbose=True)
        run_config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            word_count_threshold=10,
            excluded_tags=['form', 'header', 'nav', 'footer', 'aside', 'menu'],
            exclude_external_links=True,
            process_iframes=True,
            remove_overlay_elements=True,
            cache_mode=CacheMode.ENABLED,
            delay_before_return_html=2.0,
        )

        crawled_pages = []
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun(url=self.start_url, config=run_config)
            print(f"Deep crawl completed! Found {len(results)} pages.")

            for i, result in enumerate(results):
                if not result.success:
                    print(f"[ERROR] Failed to crawl: {result.url} - {result.error_message}")
                    continue
                if should_exclude_node_url(result.url):
                    print(f"[INFO] Skipped node url: {result.url}")
                    continue
                if not (result.markdown and result.markdown.strip()):
                    print(f"[INFO] No content found: {result.url}")
                    continue

                title = extract_title_from_content(result.markdown) or f"Page {i + 1}"
                folder_saved = save_crawled_data(
                    url=result.url,
                    title=title,
                    content=result.markdown,
                    source_urls=[self.start_url, result.url]
                )

                downloaded_files_count = 0
                if folder_saved:
                    page_folder = create_or_get_folder_for_url(result.url, RAW_DATA_DIR)
                    downloadable_links = filter_downloadable_links(result.links["internal"])
                    for file_url in downloadable_links:
                        absolute_file_url = make_absolute_url(file_url, result.url)
                        if download_file(absolute_file_url, page_folder):
                            downloaded_files_count += 1

                crawled_pages.append({
                    'url': result.url, 'title': title, 'downloaded_files': downloaded_files_count,
                    'was_updated': folder_saved is not None
                })
                status_text = "[SAVED]" if folder_saved else "[SKIPPED]"
                print(f"{status_text} Processed page: {title[:50]}... (Downloaded {downloaded_files_count} files)")

        print(f"\n--- DAA Crawl Summary: Total pages processed: {len(crawled_pages)} ---\n")
        return crawled_pages
