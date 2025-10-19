"""
UIT (University announcements) content cleaner
"""
from .base_cleaner import BaseCleaner


class UitCleaner(BaseCleaner):
    """Cleaner specifically for UIT (uit.edu.vn) content"""

    def __init__(self):
        super().__init__()
        # Patterns to skip at the beginning (before main content)
        self.skip_patterns_start = [
            'Skip to content', 'Skip to navigation', 'Navigation menu',
            'Tìm kiếm', 'Đăng Nhập', 'Liên kết', 'Back to top',
            'Website trường', 'Webmail', 'Portal', 'Sinh viên',
            'Giảng viên', 'Cán bộ', 'Thư viện', 'E-learning',
            'Microsoft Azure', 'Office 365'
        ]

        # Navigation menu indicators
        self.nav_indicators = [
            '* [Trang chủ]', '* [Giới thiệu]', '* [Tin tức]',
            '* [Thông báo]', '* [Đào tạo]', '* [Nghiên cứu]',
            '* [Hợp tác]', '* [Sinh viên]', '* [Tuyển sinh]'
        ]

        # End patterns (where we stop collecting content)
        self.end_patterns = [
            'Tin liên quan',
            'Bài viết liên quan',
            'Tin khác',
            'Xem thêm',
            'Trang',  # Pagination
            'TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN',
            'Back to top',
            'Footer',
            'Copyright'
        ]

    def clean(self, content: str) -> str:
        """Clean UIT content to extract only useful information"""
        if not content:
            return ""

        lines = content.split('\n')
        cleaned_lines = []
        content_started = False

        for line in lines:
            line = line.strip()

            # Skip empty lines at the beginning
            if not line and not content_started:
                continue

            # Check for end patterns - stop processing
            if any(pattern in line for pattern in self.end_patterns):
                break

            # Skip navigation and header content before main content starts
            if not content_started:
                # Skip navigation patterns
                if any(pattern in line for pattern in self.skip_patterns_start):
                    continue
                if any(nav in line for nav in self.nav_indicators):
                    continue

                # Start content when we find the first heading (H1)
                if line.startswith('# '):
                    content_started = True
                    cleaned_lines.append(line)
                    continue

            # Once content has started, add all lines until we hit end patterns
            if content_started and line:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def extract_title(self, content: str) -> str:
        """Extract the main title from UIT content"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return ""  # Return empty string instead of None
