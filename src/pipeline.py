"""
Main data processing pipeline that chains crawling, cleaning, and extraction.
"""
import asyncio

from src.crawler import crawl_all
from src.processing.cleaner import clean_all
from src.processing.extractor import extract_all

async def run_pipeline():
    """
    Executes the full data pipeline:
    1. Crawls all configured websites to fetch raw data.
    2. Cleans the raw web page content (content.md).
    3. Extracts text from attachments (PDF, DOCX, etc.) into .md files.
    """
    # --- STEP 1: CRAWLING ---
    await crawl_all()

    # --- STEP 2: CLEANING ---
    await clean_all()

    # --- STEP 3: EXTRACTION ---
    await extract_all()

if __name__ == "__main__":
    print("="*60)
    print("  RUNNING FULL DATA PROCESSING PIPELINE (CRAWL -> CLEAN -> EXTRACT)  ")
    print("="*60)
    asyncio.run(run_pipeline())
    print("\n" + "="*60)
    print("  PIPELINE EXECUTION COMPLETE  ".center(60))
    print("="*60)
