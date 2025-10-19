"""
URL utility functions
"""
from urllib.parse import urlparse


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs belong to the same domain"""
    return get_domain_from_url(url1) == get_domain_from_url(url2)


def make_absolute_url(relative_url: str, base_url: str) -> str:
    """Convert relative URL to absolute URL"""
    if relative_url.startswith('http'):
        return relative_url

    base_domain = f"https://{get_domain_from_url(base_url)}"

    if relative_url.startswith('/'):
        return base_domain + relative_url
    else:
        return base_domain + '/' + relative_url
