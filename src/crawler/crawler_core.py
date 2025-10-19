"""
Core module for the data crawling process, offering multiple scopes of control.
"""
import asyncio
import argparse

from src.config import START_URLS
from src.crawler.crawler_factory import CrawlerFactory

async def crawl_domain(domain: str):
    """
    Crawls a single, specific domain.

    Args:
        domain: The domain to crawl (e.g., 'daa.uit.edu.vn').
    """
    print(f"\n--- Initiating crawl for domain: {domain} ---")
    try:
        start_url = START_URLS.get(domain)
        if not start_url:
            raise ValueError(f"Domain '{domain}' not found in START_URLS configuration.")

        # Use the factory to get the correct crawler instance
        crawler_instance = CrawlerFactory.get_crawler(domain=domain, start_url=start_url)
        print(f"[INFO] Successfully instantiated crawler: {crawler_instance}")
        await crawler_instance.crawl()

    except ValueError as ve:
        print(f"[ERROR] Configuration error for domain '{domain}': {ve}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while crawling '{domain}': {e}")
    finally:
        print(f"--- Finished crawl for domain: {domain} ---")

async def crawl_all():
    """
    Iterates through all configured domains and crawls them one by one.
    """
    print("\n" + "="*50)
    print("🚀 STARTING FULL CRAWLING PROCESS")
    print("="*50)

    for domain in START_URLS.keys():
        await crawl_domain(domain)

    print("\n" + "="*50)
    print(f"✅ FULL CRAWLING PROCESS COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the data crawling process with various scopes.')
    parser.add_argument('--domain', '-d', type=str, help='Crawl a specific domain (e.g., daa.uit.edu.vn).')

    args = parser.parse_args()

    # Logic to decide which function to run
    if args.domain:
        # Ensure the requested domain is valid
        if args.domain not in START_URLS:
            print(f"[ERROR] Domain '{args.domain}' is not configured in START_URLS.")
        else:
            asyncio.run(crawl_domain(args.domain))
    else:
        # If no arguments are provided, run the full crawling process
        asyncio.run(crawl_all())
