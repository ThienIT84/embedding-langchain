from __future__ import annotations
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


"""Tiện ích đọc từng trang PDF và cung cấp nội dung dạng DocumentChunk."""


class DocumentChunk:
    """Cấu trúc nhẹ chứa đoạn văn bản và (tuỳ chọn) số trang."""

    __slots__ = ("text", "page_number")

    def __init__(self, text: str, page_number: int | None = None) -> None:
        self.text = text
        self.page_number = page_number


def extract_pdf_text(file_path: Path) -> Iterable[DocumentChunk]:
    """Đọc PDF và yield các khối nội dung theo từng trang."""
    reader = PdfReader(str(file_path))
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.replace("\x00", "").strip()
        if not text:
            continue
        yield DocumentChunk(text=text, page_number=idx)
