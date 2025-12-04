from __future__ import annotations

from typing import Iterable, Iterator

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings
from .text_extractor import DocumentChunk


"""Chia văn bản dài thành các đoạn nhỏ dựa trên cấu hình chunk size."""


class TextChunk(DocumentChunk):
    """Mở rộng DocumentChunk để lưu thêm thứ tự và chỉ số chunk."""

    __slots__ = ("chunk_index",)  # Chỉ khai báo field MỚI (text, page_number, source_file đã có ở cha)

    def __init__(
        self, 
        text: str, 
        page_number: int | None = None, 
        chunk_index: int = 0,
        source_file: str | None = None
    ) -> None:
        super().__init__(text=text, page_number=page_number, source_file=source_file)
        self.chunk_index = chunk_index

    def to_dict(self) -> dict:
        """Kế thừa từ cha và thêm chunk_index."""
        base = super().to_dict()
        base["chunk_index"] = self.chunk_index
        return base


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", " ", ""],
    keep_separator=False,  # Bỏ ký tự phân cách thừa
    strip_whitespace=True  # Tự động xóa khoảng trắng thừa
)


def split_chunks(chunks: Iterable[DocumentChunk]) -> Iterator[TextChunk]:
    """
    Tách lần lượt từng DocumentChunk thành các TextChunk nhỏ hơn.
    Sử dụng YIELD để tiết kiệm bộ nhớ (Streaming).
    """
    global_chunk_index = 0  # Biến đếm tổng số chunk đã tạo ra
    
    for chunk in chunks:
        # Tách văn bản của trang hiện tại
        pieces = _splitter.split_text(chunk.text)
        
        for piece in pieces:
            text = piece.strip()
            if not text:
                continue
            
            global_chunk_index += 1
            
            # Trả về ngay lập tức từng mảnh nhỏ
            yield TextChunk(
                text=text,
                page_number=chunk.page_number,
                chunk_index=global_chunk_index,
                source_file=getattr(chunk, 'source_file', None)  # Lấy tên file từ cha
            )