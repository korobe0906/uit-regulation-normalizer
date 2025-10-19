import hashlib
import json
import re
from urllib.parse import urlparse

import requests
import os
from datetime import datetime

from src.config import RAW_DATA_DIR, DOWNLOADABLE_EXTENSIONS, REQUEST_TIMEOUT

def should_exclude_node_url(url: str) -> bool:
    """Check if URL should be excluded (node/id format)."""
    return bool(re.search(r'/node/\d+', url))


def get_folder_name_from_url(url: str) -> str:
    """Convert URL to folder name by extracting path after domain and replacing / with -"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return 'root'
    return path.replace('/', '-')


def create_or_get_folder_for_url(url: str, base_dir: str) -> str:
    """
    Create or get a unique folder for a URL within its domain's subdirectory.
    e.g., https://daa.uit.edu.vn/thong-bao -> <base_dir>/daa.uit.edu.vn/thong-bao/
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if not domain:
        raise ValueError(f"Cannot determine domain from URL: {url}")

    domain_folder = os.path.join(base_dir, domain)
    page_folder_name = get_folder_name_from_url(url)
    full_path = os.path.join(domain_folder, page_folder_name)

    os.makedirs(full_path, exist_ok=True)
    return full_path


def generate_content_hash(content: str) -> str:
    """Generate SHA256 hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def save_crawled_data(url: str, title: str, content: str, source_urls: list = None):
    """
    Saves crawled data into an organized folder structure.
    A hash of the content is stored in metadata for future reference.
    """
    print(f"[INFO] Saving data for {url}")

    folder_path = create_or_get_folder_for_url(url, RAW_DATA_DIR)
    content_file = os.path.join(folder_path, 'content.md')
    with open(content_file, 'w', encoding='utf-8') as f:
        f.write(content)

    metadata = {
        "original_url": url,
        "title": title,
        "crawled_at": datetime.now().isoformat() + "Z",
        "content_hash": generate_content_hash(content),
        "source_urls": source_urls or [url]
    }

    metadata_file = os.path.join(folder_path, 'metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Data saved to: {folder_path}")
    return folder_path


def extract_title_from_content(content: str) -> str:
    """Extract the main title from cleaned content"""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return ""


def filter_downloadable_links(links: list) -> list:
    """Filter internal links to get only downloadable files (pdf, doc, xls, etc.)"""
    downloadable_links = []
    for link in links:
        href = link.get('href', '')
        if any(href.lower().endswith(ext) for ext in DOWNLOADABLE_EXTENSIONS):
            downloadable_links.append(href)
    return downloadable_links


def download_file(url: str, save_folder: str) -> bool:
    try:
        os.makedirs(save_folder, exist_ok=True)
        file_name = url.split('/')[-1]
        save_path = os.path.join(save_folder, file_name)

        print(f"[INFO] Downloading: {file_name} from {url}")
        response = requests.get(url, stream=True, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[SUCCESS] Downloaded file to: {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download {url}. Error: {e}")
        return False
