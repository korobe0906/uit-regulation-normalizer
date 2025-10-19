"""
Crawler configuration settings
"""

# A dictionary mapping each allowed domain to its single starting URL for crawling.
# The keys of this dictionary are the single source of truth for "allowed domains".
START_URLS = {
    "daa.uit.edu.vn": "https://daa.uit.edu.vn/",
    #"uit.edu.vn": "https://uit.edu.vn/",
    # "course.uit.edu.vn": "https://course.uit.edu.vn/",
    # "tuyensinh.uit.edu.vn": "https://tuyensinh.uit.edu.vn/"
}

# Crawler settings
MAX_PAGES_PER_DOMAIN = 1000
CRAWL_DELAY = 2.0
REQUEST_TIMEOUT = 30

# Supported file extensions for download
DOWNLOADABLE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']
