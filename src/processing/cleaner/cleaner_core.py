"""
Core module for the data cleaning process, offering multiple scopes of control.
"""
import asyncio
import argparse

from src.config import START_URLS
from src.processing.cleaner.cleaner_factory import CleanerFactory

async def clean_folder(folder_path: str, domain: str):
    """
    Cleans a single, specific folder using the appropriate cleaner for the domain.

    Args:
        folder_path: The absolute path to the raw data folder to be cleaned.
        domain: The domain name (e.g., 'daa.uit.edu.vn') to select the correct cleaner.
    """
    print(f"--- Cleaning specific folder: {folder_path} for domain: {domain} ---")
    try:
        # Directly get the cleaner using the domain name.
        cleaner = CleanerFactory.get_cleaner(domain)
        print(f"[INFO] Using cleaner: {cleaner.__class__.__name__}")
        success = cleaner.process_folder(folder_path)
        if success:
            print(f"[SUCCESS] Successfully cleaned folder: {folder_path}")
        else:
            print(f"[ERROR] Failed to clean folder: {folder_path}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while cleaning folder '{folder_path}': {e}")

async def clean_domain(domain: str):
    """
    Cleans all raw data folders for a single specified domain.

    Args:
        domain: The domain to clean (e.g., 'daa.uit.edu.vn').
    """
    print(f"\n--- Cleaning all data for domain: {domain} ---")
    try:
        # Directly get the cleaner using the domain name.
        cleaner = CleanerFactory.get_cleaner(domain)
        print(f"[INFO] Using cleaner: {cleaner.__class__.__name__}")
        cleaner.process_domain(domain)
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while cleaning domain '{domain}': {e}")

async def clean_all():
    """
    Iterates through all configured domains and cleans them one by one.
    """
    print("\n" + "="*50)
    print("✨ STARTING FULL CLEANING PROCESS")
    print("="*50)

    # Use START_URLS keys as the list of domains to process.
    for domain in START_URLS.keys():
        await clean_domain(domain)

    print("\n" + "="*50)
    print(f"✅ FULL CLEANING PROCESS COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the data cleaning process with various scopes.')
    parser.add_argument('--domain', '-d', type=str, help='Clean a specific domain (e.g., daa.uit.edu.vn).')
    parser.add_argument('--folder', '-f', type=str, help='Clean a single specific folder path.')

    args = parser.parse_args()

    # Logic to decide which function to run
    if args.folder:
        if not args.domain:
            print("[ERROR] You must specify a --domain when cleaning a specific --folder.")
        else:
            asyncio.run(clean_folder(args.folder, args.domain))
    elif args.domain:
        asyncio.run(clean_domain(args.domain))
    else:
        # If no arguments are provided, run the full cleaning process
        asyncio.run(clean_all())
