from __future__ import annotations

from typing import Sequence

from .retriever import RetrievedChunk

"""Xây dựng prompt hoàn chỉnh để gửi tới LLM dựa trên các đoạn văn bản đã truy xuất."""

_DEFAULT_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI hỗ trợ trả lời câu hỏi dựa trên các đoạn văn bản cung cấp. "
    "Chỉ sử dụng thông tin trong phần Context. Nếu Context không đủ, hãy nói rõ bạn không chắc chắn." 
    "Trả lời ngắn gọn bằng tiếng Việt, ưu tiên liệt kê bullet khi phù hợp."
)


def build_rag_prompt(
    query: str,
    chunks: Sequence[RetrievedChunk],
    system_prompt: str | None = None,
) -> str:
    """Ghép câu hỏi và context thành prompt duy nhất để gọi LLM."""
    if not query.strip():
        raise ValueError("Query không được để trống")

    system = system_prompt.strip() if system_prompt else _DEFAULT_SYSTEM_PROMPT
    if not chunks:
        context_section = "(Không có context phù hợp được tìm thấy.)"
    else:
        formatted_chunks: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            header_parts: list[str] = [f"Đoạn {idx}"]
            if chunk.page_number:
                header_parts.append(f"Trang {chunk.page_number}")
            header_parts.append(f"Score: {chunk.similarity:.4f}")
            header = " | ".join(header_parts)
            formatted_chunks.append(f"{header}\n{chunk.content.strip()}")
        context_section = "\n\n".join(formatted_chunks)

    prompt = (
        f"{system}\n\n"
        f"Context:\n{context_section}\n\n"
        f"Câu hỏi: {query.strip()}\n"
        "Hãy cung cấp câu trả lời ngắn gọn và chỉ dựa trên context ở trên."
    )
    return prompt
