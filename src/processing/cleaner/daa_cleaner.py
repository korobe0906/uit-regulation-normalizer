"""
DAA (Đào tạo) content cleaner
"""
from .base_cleaner import BaseCleaner


class DaaCleaner(BaseCleaner):
    """Cleaner specifically for DAA (daa.uit.edu.vn.uit.edu.vn.uit.edu.vn) content"""

    def __init__(self):
        # Patterns to skip at the beginning (before main content)
        super().__init__()
        self.skip_patterns_start = [
            'Skip to content', 'Skip to navigation', 'Navigation menu',
            'Tìm kiếm', 'Đăng Nhập', 'Liên kết', 'Back to top',
            '--------- Liên kết website -------', 'Website trường',
            'Webmail', 'Website môn học', 'Tài khoản chứng thực',
            'Diễn đàn sinh viên', 'Microsoft Azure', 'Khoa Công Nghệ',
            'Khoa Hệ Thống', 'Khoa Kỹ Thuật', 'Khoa Mạng Máy Tính',
            'Khoa Khoa Học Máy Tính'
        ]

        # Navigation menu indicators
        self.nav_indicators = [
            '* [Home]', '* [Giới thiệu]', '* [Thông báo]',
            '* [Quy định - Hướng dẫn]', '* [Kế hoạch năm]',
            '* [Chương trình đào tạo]', '* [Lịch]'
        ]

        # End patterns (where we stop collecting content)
        self.end_patterns = [
            'Bài viết liên quan',  # Stop immediately when we see related articles
            'Trang',  # Pagination starts here
            'PHÒNG ĐÀO TẠO ĐẠI HỌC',
            'Back to top'
        ]

    def clean(self, content: str) -> str:
        """
        Dọn dẹp content DAA một cách đơn giản và hiệu quả.
        Bắt đầu từ H1 ('# ') đầu tiên, kết thúc trước các end_patterns.
        """
        if not content:
            return ""

        lines = content.split('\n')
        cleaned_lines = []
        collecting = False  # Dùng một cái tên rõ ràng hơn

        for line in lines:
            line = line.strip()

            # --- Logic của Người Sưu Tầm Thông Minh ---

            if not collecting:
                # 1. TÌM ĐIỂM BẮT ĐẦU: Chỉ cần thấy '# ' là bắt đầu hốt!
                if line.startswith('# '):
                    collecting = True
                    cleaned_lines.append(line)  # Nhớ hốt luôn cả dòng này nhé!
            else:
                # 2. KIỂM TRA ĐIỂM DỪNG: Thấy rác là dừng lại ngay lập tức
                if any(pattern in line for pattern in self.end_patterns):
                    break  # Dừng vòng lặp, không xử lý thêm nữa

                # 3. HỐT HÀNG: Nếu không phải điểm dừng, cứ bỏ vào giỏ
                if line:  # Chỉ thêm những dòng có nội dung
                    cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def extract_title(self, content: str) -> str:
        """Extract the main title from DAA content"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return ""  # Return empty string instead of None
