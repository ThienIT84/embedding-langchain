from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .chunker import split_chunks, TextChunk
from .embedder import embed_chunks, EmbeddingResult
from .config import settings
from .supabase_client import (
    delete_existing_embeddings,
    download_file,
    fetch_document_metadata,
    insert_embeddings,
    upsert_embedding_status,
)
from .text_extractor import extract_pdf_text


"""Chuỗi tác vụ ingest tài liệu: tải, tách đoạn, sinh embedding và lưu Supabase."""


def _load_document(document_path: Path) -> Iterable[TextChunk]:
    """Đọc file PDF đã tải và trả về danh sách TextChunk."""
    document_chunks = extract_pdf_text(document_path)
    return split_chunks(document_chunks)


def _prepare_records(document_id: str, embeddings: List[EmbeddingResult]) -> List[dict[str, object]]:
    """Chuyển danh sách embedding thành payload ghi vào bảng document_embeddings."""
    records: List[dict[str, object]] = []
    for item in embeddings:
        records.append(
            {
                "document_id": document_id,
                "content": item.chunk.text,
                "page_number": item.chunk.page_number,
                "chunk_index": item.chunk.chunk_index,
                "embedding": item.vector.tolist(),
            }
        )
    return records


def process_document(document_id: str) -> None:
    """Xử lý toàn bộ vòng đời ingest embedding cho một tài liệu duy nhất."""
    metadata = fetch_document_metadata(document_id)
    upsert_embedding_status(document_id=document_id, status="processing")

    file_path: Path | None = None

    try:
        remote_path = metadata.get("file_path")
        if not remote_path:
            raise ValueError(f"Document {document_id} is missing file_path in Supabase")

        filename = Path(remote_path).name or f"{document_id}.pdf"
        file_path = settings.temp_dir / filename
        file_path = download_file(remote_path, file_path)

        text_chunks = _load_document(file_path)
        embeddings = embed_chunks(text_chunks)
        records = _prepare_records(document_id, embeddings)

        delete_existing_embeddings(document_id)
        if records:
            insert_embeddings(records)

        upsert_embedding_status(document_id=document_id, status="completed")
    except Exception as exc:  # noqa: BLE001 - log and re-raise after marking failed
        upsert_embedding_status(document_id=document_id, status="failed", error_message=str(exc))
        raise
    finally:
        if file_path and file_path.exists():
            # unlink xóa file tạm thời
            file_path.unlink(missing_ok=True)
