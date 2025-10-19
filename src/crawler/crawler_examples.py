import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, BFSDeepCrawlStrategy, \
    LXMLWebScrapingStrategy, BestFirstCrawlingStrategy, KeywordRelevanceScorer, AdaptiveCrawler, AsyncUrlSeeder, \
    SeedingConfig

# --- Configuration Paths ---
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
RAW_DATA_DIR = os.path.join(ROOT_DIR, 'data', 'raw', 'daa.uit.edu.vn.uit.edu.vn')
URL = "https://daa.uit.edu.vn"

os.makedirs(RAW_DATA_DIR, exist_ok=True)


async def simple_crawl_daa():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        # Content filtering
        word_count_threshold=10,
        excluded_tags=['form', 'header'],
        exclude_external_links=True,

        # Content processing
        process_iframes=True,
        remove_overlay_elements=True,

        # Cache control
        cache_mode=CacheMode.ENABLED  # Use cache if available
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=URL,
            config=run_config
        )

        if result.success:
            # Print clean content
            print("Content:", result.markdown[:1000])  # First 500 chars

            # Process images
            for image in result.media["images"]:
                print(f"Found image: {image['src']}")

            # Process links
            for link in result.links["internal"]:
                print(f"Internal link: {link['href']}")

        else:
            print(f"Crawl failed: {result.error_message}")

async def deep_crawl_daa():
    # Create a scorer
    scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    # Configure the strategy
    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        include_external=False,
        url_scorer=scorer,
        max_pages=25,  # Maximum number of pages to crawl (optional)
    )

    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=URL, config=config)

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        for result in results[:3]:  # Show first 3 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}"

                  )
async def scorer_crawl():
    # Create a keyword relevance scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7  # Importance of this scorer (0.0 to 1.0)
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            url_scorer=keyword_scorer
        ),
        stream=True  # Recommended with BestFirstCrawling
    )

    # Results will come in order of relevance score
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://example.com", config=config):
            score = result.metadata.get("score", 0)
            print(f"Score: {score:.2f} | {result.url}")


async def basic_adaptive_crawl():
    async with AsyncWebCrawler() as crawler:
        # Create an adaptive crawler (config is optional)
        adaptive = AdaptiveCrawler(crawler)

        # Start crawling with a query
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/",
            query="how to define a function in python"
        )

        # View statistics
        adaptive.print_stats()

        # Get the most relevant content
        relevant_pages = adaptive.get_relevant_content(top_k=5)
        for page in relevant_pages:
            print(f"- {page['url']} (score: {page['score']:.2f})")

async def smart_blog_crawler():
    # Step 1: Create our URL discoverer
    seeder = AsyncUrlSeeder()

    # Step 2: Configure discovery - let's find all blog posts
    config = SeedingConfig(
        source="sitemap+cc",      # Use the website's sitemap+cc
        extract_head=True,          # Get page metadata
        max_urls=10000               # Limit for this example
    )

    # Step 3: Discover URLs from the Python blog
    print("🔍 Discovering course posts...")
    urls = await seeder.urls("daa.uit.edu.vn.uit.edu.vn.uit.edu.vn", config)
    print(f"✅ Found {len(urls)} course posts")

    # Step 4: Filter for Python tutorials (using metadata!)
    tutorials = [
        url for url in urls
        # if url["status"] == "valid" and
        # any(keyword in str(url["head_data"]).lower()
        #     for keyword in ["quydinh", "quy-dinh", "thong-bao", "page", "trang"])
    ]
    print(f"📚 Filtered to {len(tutorials)} tutorials")

    # Step 5: Show what we found
    print("\n🎯 Found these tutorials:")
    for tutorial in tutorials[:5]:  # First 5
        title = tutorial["head_data"].get("title", "No title")
        print(f"  - {title}")
        print(f"    {tutorial['url']}")

    # Step 6: Now crawl ONLY these relevant pages
    print("\n🚀 Crawling tutorials...")
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            only_text=True,
            word_count_threshold=300,  # Only substantial articles
            stream=True
        )

        # Extract URLs and crawl them
        tutorial_urls = [t["url"] for t in tutorials[:10]]
        results = await crawler.arun_many(tutorial_urls, config=config)

        successful = 0
        async for result in results:
            if result.success:
                successful += 1
                print(f"✓ Crawled: {result.url[:60]}...")

        print(f"\n✨ Successfully crawled {successful} tutorials!")

