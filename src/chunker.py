from __future__ import annotations

from typing import Iterable, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings
from .text_extractor import DocumentChunk


"""Chia văn bản dài thành các đoạn nhỏ dựa trên cấu hình chunk size."""


class TextChunk(DocumentChunk):
    """Mở rộng DocumentChunk để lưu thêm thứ tự và chỉ số chunk."""

    __slots__ = ("text", "page_number", "chunk_index")

    def __init__(self, text: str, page_number: int | None = None, chunk_index: int | None = None) -> None:
        super().__init__(text=text, page_number=page_number)
        self.chunk_index = chunk_index


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", " ", ""],
)


def split_chunks(chunks: Iterable[DocumentChunk]) -> List[TextChunk]:
    """Tách lần lượt từng DocumentChunk thành các TextChunk nhỏ hơn."""
    output: List[TextChunk] = []
    for source_idx, chunk in enumerate(chunks):
        pieces = _splitter.split_text(chunk.text)
        for piece_idx, piece in enumerate(pieces):
            text = piece.strip()
            if not text:
                continue
            output.append(
                TextChunk(
                    text=text,
                    page_number=chunk.page_number,
                    chunk_index=len(output) + 1,
                )
            )
    return output
