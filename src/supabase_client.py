from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

from supabase import create_client, Client
from postgrest.exceptions import APIError

from .config import settings
from .retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)

"""Tiện ích giao tiếp với Supabase: tải file, cập nhật trạng thái, ghi embeddings."""


_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Tạo (hoặc tái sử dụng) Supabase client dựa trên cấu hình."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase_client


@retry_with_backoff(max_retries=3, initial_delay=1.0)
def download_file(file_path: str, destination: Path) -> Path:
    """Tải tệp từ bucket Supabase về đường dẫn cục bộ được chỉ định (với retry logic)."""
    client = get_supabase_client()
    response = client.storage.from_(settings.supabase_bucket).download(file_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response)
    return destination


def fetch_document_metadata(document_id: str) -> dict[str, Any]:
    """Lấy metadata tài liệu từ bảng documents dựa trên document_id."""
    client = get_supabase_client()
    response = (
        client.table("documents")
        .select("id, title, file_path, category_id, group_id, created_by, updated_at")
        .eq("id", document_id)
        .limit(1)
        .execute()
    )
    data = response.data
    if not data:
        raise ValueError(f"Document {document_id} not found")
    return data[0]


def upsert_embedding_status(document_id: str, status: str, error_message: str | None = None) -> None:
    """Cập nhật trạng thái embedding; fallback sang bảng embedding_status nếu thiếu cột."""
    client = get_supabase_client()
    doc_payload: dict[str, Any] = {"embedding_status": status}
    doc_payload["embedding_error"] = error_message if error_message else None

    try:
        client.table("documents").update(doc_payload).eq("id", document_id).execute()
        return
    except APIError as exc:
        error_text = str(exc).lower()
        if "embedding_error" not in error_text and "embedding_status" not in error_text:
            raise

    status_payload: dict[str, Any] = {
        "document_id": document_id,
        "status": status,
        "error_message": error_message,
    }
    client.table("embedding_status").upsert(status_payload, on_conflict="document_id").execute()


def delete_existing_embeddings(document_id: str) -> None:
    """Xoá toàn bộ embedding cũ của tài liệu trước khi ghi mới."""
    client = get_supabase_client()
    client.table("document_embeddings").delete().eq("document_id", document_id).execute()


@retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(APIError, Exception))
def insert_embeddings(rows: list[dict[str, Any]]) -> None:
    """Chèn danh sách embedding với retry logic và batch processing."""
    if not rows:
        return
    
    client = get_supabase_client()
    
    # Batch insert để tránh timeout với dataset lớn
    BATCH_SIZE = 100
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        client.table("document_embeddings").insert(batch).execute()
        logger.info(f"Inserted batch {i//BATCH_SIZE + 1}/{(len(rows)-1)//BATCH_SIZE + 1}: {len(batch)} embeddings")
