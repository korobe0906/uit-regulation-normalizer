"""
Core module for the file content extraction process.
This module is the main entry point and contains the core logic for orchestrating the extraction.
"""
import asyncio
import argparse
import os

from src.config import START_URLS, RAW_DATA_DIR, PROCESSED_DATA_DIR
from .extractor_factory import ExtractorFactory

async def extract_folder(raw_folder_path: str):
    """
    Extracts content from all supported files in a single raw data folder.
    It calculates the corresponding processed folder path and creates it if it doesn't exist.

    Args:
        raw_folder_path: The absolute path to the raw data folder.
    """
    print(f"--- Extracting attachments for folder: {raw_folder_path} ---")
    
    # 1. Calculate and create the destination processed folder.
    try:
        relative_path = os.path.relpath(raw_folder_path, RAW_DATA_DIR)
        processed_folder_path = os.path.join(PROCESSED_DATA_DIR, relative_path)
        os.makedirs(processed_folder_path, exist_ok=True)
    except ValueError:
        print(f"[ERROR] Invalid path: '{raw_folder_path}' is not in '{RAW_DATA_DIR}'.")
        return

    if not os.path.isdir(raw_folder_path):
        print(f"[WARNING] Raw folder not found, skipping: {raw_folder_path}")
        return

    extracted_count = 0
    for filename in os.listdir(raw_folder_path):
        # Ignore web content files, which are handled by the Cleaner.
        if filename in ['content.md', 'metadata.json']:
            continue

        raw_file_path = os.path.join(raw_folder_path, filename)
        
        try:
            # 2. Get the appropriate extractor. This will raise ValueError if not supported.
            extractor = ExtractorFactory.get_extractor(raw_file_path)
            
            print(f"[INFO] Found supported file, extracting: {filename}")
            content = extractor.extract(raw_file_path)
            
            if content:
                # 3. Save the extracted content as a new .md file.
                output_filename = f"{filename}.md"
                output_filepath = os.path.join(processed_folder_path, output_filename)
                
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"[SUCCESS] Saved extracted content to: {output_filepath}")
                extracted_count += 1
            else:
                print(f"[WARNING] Extractor produced no content for: {filename}")

        except ValueError as e:
            # This catches the error from the factory for unsupported file types.
            print(f"[INFO] Skipping file '{filename}': {e}")
        except Exception as e:
            # This catches any other errors during the extraction process itself.
            print(f"[ERROR] Failed during extraction of {filename}: {e}")
    
    print(f"--- Finished extraction for folder. Extracted {extracted_count} files. ---")

async def extract_domain(domain: str):
    """
    Extracts attachments for all raw folders within a specific domain.
    """
    print(f"\n--- Extracting all attachments for domain: {domain} ---")
    domain_raw_path = os.path.join(RAW_DATA_DIR, domain)

    if not os.path.isdir(domain_raw_path):
        print(f"[WARNING] No raw directory found for domain '{domain}'. Skipping.")
        return

    for folder_name in os.listdir(domain_raw_path):
        folder_path = os.path.join(domain_raw_path, folder_name)
        if os.path.isdir(folder_path):
            await extract_folder(folder_path)

async def extract_all():
    """
    Iterates through all configured domains and extracts attachments for them.
    """
    print("\n" + "="*50)
    print("🔬 STARTING FULL EXTRACTION PROCESS")
    print("="*50)

    for domain in START_URLS.keys():
        await extract_domain(domain)

    print("\n" + "="*50)
    print(f"✅ FULL EXTRACTION PROCESS COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the file content extraction process.')
    parser.add_argument('--domain', '-d', type=str, help='Extract for a specific domain (e.g., daa.uit.edu.vn).')
    parser.add_argument('--folder', '-f', type=str, help='Extract for a single specific RAW folder path.')

    args = parser.parse_args()

    if args.folder:
        # When a specific folder is given, domain is not needed.
        asyncio.run(extract_folder(args.folder))
    elif args.domain:
        if args.domain not in START_URLS:
            print(f"[ERROR] Domain '{args.domain}' is not configured in START_URLS.")
        else:
            asyncio.run(extract_domain(args.domain))
    else:
        asyncio.run(extract_all())
