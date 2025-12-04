from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable
from pypdf import PdfReader
import logging

# Thiết lập logging để theo dõi lỗi thay vì print
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
Tiện ích đọc từng trang PDF và cung cấp nội dung dạng DocumentChunk.
Đã tối ưu hóa cho RAG Pipeline: xử lý lỗi, làm sạch text và thêm metadata nguồn.
"""


class DocumentChunk:
    """
    Cấu trúc chứa nội dung văn bản, số trang và tên nguồn.
    Sử dụng __slots__ để tối ưu hóa bộ nhớ khi xử lý lượng lớn tài liệu.
    """
    __slots__ = ("text", "page_number", "source_file")

    def __init__(self, text: str, page_number: int | None = None, source_file: str | None = None) -> None:
        self.text = text
        self.page_number = page_number
        self.source_file = source_file or "unknown"

    def to_dict(self) -> dict:
        """Chuyển đổi sang dictionary để lưu vào DB hoặc serialize."""
        return {
            "text": self.text,
            "page_number": self.page_number,
            "source_file": self.source_file
        }


def clean_text(text: str) -> str:
    """
    Hàm làm sạch văn bản nâng cao cho RAG.
    - Loại bỏ null bytes
    - Nối các từ bị ngắt dòng (hyphenation)
    - Chuẩn hóa khoảng trắng
    """
    if not text:
        return ""
    
    # 1. Loại bỏ Null bytes (quan trọng cho Vector DB)
    text = text.replace("\x00", "")
    
    # 2. Nối các từ bị ngắt dòng (Hyphenation restoration)
    # Ví dụ: "process- \ning" -> "processing"
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # 3. Thay thế nhiều khoảng trắng hoặc xuống dòng thừa bằng 1 khoảng trắng
    # Giúp mô hình Embedding hiểu ngữ nghĩa liền mạch hơn
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_pdf_text(file_path: Path) -> Iterable[DocumentChunk]:
    """
    Đọc PDF và yield các khối nội dung theo từng trang.
    Bao gồm xử lý ngoại lệ (File không tồn tại, File lỗi, File bị mã hóa).
    """
    file_str = str(file_path)
    
    try:
        # Kiểm tra file tồn tại
        if not file_path.exists():
            logger.error(f"File not found: {file_str}")
            return

        reader = PdfReader(file_str)
        
        # Lấy tên file để làm metadata source
        file_name = file_path.name

        total_pages = len(reader.pages)
        logger.info(f"Start processing {file_name}: {total_pages} pages.")

        for idx, page in enumerate(reader.pages, start=1):
            try:
                raw_text = page.extract_text() or ""
                
                # Áp dụng hàm làm sạch
                cleaned_text = clean_text(raw_text)
                
                # Bỏ qua trang trắng hoặc trang quá ít thông tin (< 5 ký tự)
                if len(cleaned_text) < 5:
                    continue
                
                yield DocumentChunk(
                    text=cleaned_text, 
                    page_number=idx,
                    source_file=file_name
                )
            except Exception as e:
                # Nếu lỗi 1 trang, log lại và tiếp tục trang sau (không dừng cả chương trình)
                logger.warning(f"Error extracting page {idx} of {file_name}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Critical error processing file {file_str}: {e}")
        return
