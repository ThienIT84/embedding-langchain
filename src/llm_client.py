from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .config import settings

"""Gọi Ollama local để sinh câu trả lời dựa trên prompt đã chuẩn bị."""


@dataclass(slots=True)
class LLMResponse:
    """Kết quả trả về từ mô hình ngôn ngữ."""

    answer: str
    model: str
    raw: dict[str, Any]


class LLMClientError(RuntimeError):
    """Báo lỗi khi gọi Ollama thất bại."""


def generate_answer(prompt: str, model: str | None = None, timeout: int = 120) -> LLMResponse:
    """Gọi Ollama generate API và trả về câu trả lời."""
    if not prompt.strip():
        raise ValueError("Prompt không được để trống")

    target_model = model or settings.ollama_model
    if not target_model:
        raise ValueError("Chưa cấu hình OLLAMA_MODEL")

    url = settings.ollama_url.rstrip("/") + "/api/generate"
    payload = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:  # noqa: BLE001 - wrap lỗi request
        raise LLMClientError(f"Không thể kết nối tới Ollama tại {url}: {exc}") from exc

    if response.status_code != 200:
        text = response.text[:500]
        raise LLMClientError(f"Ollama trả về mã lỗi {response.status_code}: {text}")

    data = response.json()
    answer = data.get("response")
    if not isinstance(answer, str):
        raise LLMClientError("Phản hồi từ Ollama không hợp lệ: thiếu trường 'response'")

    return LLMResponse(answer=answer.strip(), model=target_model, raw=data)
