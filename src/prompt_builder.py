from __future__ import annotations

from typing import Sequence

from .retriever import RetrievedChunk

"""Xây dựng prompt hoàn chỉnh để gửi tới LLM dựa trên các đoạn văn bản đã truy xuất."""

_DEFAULT_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI hỗ trợ trả lời câu hỏi dựa trên các đoạn văn bản cung cấp. "
    "Chỉ sử dụng thông tin trong phần Context. Nếu Context không đủ, hãy nói rõ bạn không chắc chắn." 
)

# Fast mode: Câu trả lời ngắn gọn
_FAST_MODE_INSTRUCTION = (
    "Trả lời ngắn gọn trong 2-3 câu, đi thẳng vào vấn đề chính. "
    "Chỉ đưa ra thông tin quan trọng nhất."
)

# DeepThink mode: Phân tích chi tiết
_DEEPTHINK_MODE_INSTRUCTION = (
    "Phân tích và trả lời chi tiết, đầy đủ. "
    "Giải thích rõ ràng các khái niệm, đưa ra ví dụ khi cần thiết. "
    "Sử dụng bullet points để tổ chức thông tin. "
    "Cung cấp reasoning và kết luận cuối cùng."
)


def build_rag_prompt(
    query: str,
    chunks: Sequence[RetrievedChunk],
    system_prompt: str | None = None,
    mode: str = "fast",  # "fast" hoặc "deepthink"
) -> str:
    """Ghép câu hỏi và context thành prompt duy nhất để gọi LLM.
    
    Args:
        query: Câu hỏi của user
        chunks: Các đoạn context đã retrieve
        system_prompt: Custom system prompt (override default)
        mode: "fast" (ngắn gọn) hoặc "deepthink" (chi tiết)
    """
    if not query.strip():
        raise ValueError("Query không được để trống")

    # Chọn instruction dựa trên mode
    if mode == "deepthink":
        mode_instruction = _DEEPTHINK_MODE_INSTRUCTION
    else:  # default: fast
        mode_instruction = _FAST_MODE_INSTRUCTION

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
        f"Câu hỏi: {query.strip()}\n\n"
        f"{mode_instruction}"
    )
    return prompt
