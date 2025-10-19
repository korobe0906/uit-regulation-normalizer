"""
Base cleaner interface for different content sources
"""
import os
import json
from abc import ABC, abstractmethod
from datetime import datetime

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR


class BaseCleaner(ABC):
    """Abstract base class for content cleaners"""

    def __init__(self, raw_data_dir: str = None, processed_data_dir: str = None):
        """Initialize cleaner with data directories"""
        self.raw_data_dir = raw_data_dir or RAW_DATA_DIR
        self.processed_data_dir = processed_data_dir or PROCESSED_DATA_DIR

    @abstractmethod
    def clean(self, content: str) -> str:
        """Clean the raw content and return processed content"""
        pass

    @abstractmethod
    def extract_title(self, content: str) -> str:
        """Extract title from content"""
        pass

    def process_folder(self, folder_path: str) -> bool:
        """
        Process a raw folder and create corresponding processed folder
        Args:
            folder_path: Path to the raw folder (e.g., 'raw/daa.uit.edu.vn.uit.edu.vn/thong-bao-chung')
        Returns:
            bool: Success status
        """
        try:
            # Read raw content
            raw_content_file = os.path.join(folder_path, 'content.md')
            if not os.path.exists(raw_content_file):
                print(f"❌ No content.md found in {folder_path}")
                return False

            with open(raw_content_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            # Clean content
            cleaned_content = self.clean(raw_content)

            # Create processed folder path
            # Convert raw/daa.uit.edu.vn.uit.edu.vn/thong-bao-chung -> processed/daa.uit.edu.vn.uit.edu.vn/thong-bao-chung
            relative_path = os.path.relpath(folder_path, self.raw_data_dir)
            processed_folder_path = os.path.join(self.processed_data_dir, relative_path)
            os.makedirs(processed_folder_path, exist_ok=True)

            # Save cleaned content
            processed_content_file = os.path.join(processed_folder_path, 'content.md')
            with open(processed_content_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)

            # Copy metadata.json
            raw_metadata_file = os.path.join(folder_path, 'metadata.json')
            processed_metadata_file = os.path.join(processed_folder_path, 'metadata.json')

            if os.path.exists(raw_metadata_file):
                # Update metadata to indicate it's been processed
                with open(raw_metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                metadata['processed_at'] = datetime.now().isoformat()
                metadata['cleaned'] = True

                with open(processed_metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"✅ Processed: {folder_path} -> {processed_folder_path}")
            return True

        except Exception as e:
            print(f"❌ Error processing {folder_path}: {e}")
            return False

    def process_domain(self, domain: str) -> int:
        """
        Process all folders in a domain (e.g., 'daa.uit.edu.vn.uit.edu.vn', 'course')
        Returns: Number of successfully processed folders
        """
        domain_path = os.path.join(self.raw_data_dir, domain)
        if not os.path.exists(domain_path):
            print(f"❌ Domain path not found: {domain_path}")
            return 0

        processed_count = 0
        for folder_name in os.listdir(domain_path):
            folder_path = os.path.join(domain_path, folder_name)
            if os.path.isdir(folder_path):
                if self.process_folder(folder_path):
                    processed_count += 1

        print(f"🎉 Processed {processed_count} folders in domain '{domain}'")
        return processed_count
