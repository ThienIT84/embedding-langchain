from __future__ import annotations

"""CLI nhỏ để chạy thử quy trình RAG end-to-end."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag_service import rag_query


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Thực thi RAG cho một document cụ thể")
    parser.add_argument("--query", required=True, help="Câu hỏi muốn truy vấn")
    parser.add_argument("--document-id", required=True, help="Định danh tài liệu trong Supabase")
    parser.add_argument("--top-k", type=int, default=5, help="Số đoạn context muốn lấy (mặc định 5)")
    parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Hiển thị prompt đã gửi lên LLM",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="In kết quả dạng JSON đẹp mắt (mặc định: text ngắn gọn)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result: dict[str, Any] = rag_query(
        query=args.query,
        document_id=args.document_id,
        top_k=args.top_k,
    )

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print("\n=== ANSWER ===")
    print(result["answer"])

    if args.show_prompt:
        print("\n=== PROMPT GỬI LÊN LLM ===")
        print(result["prompt"])

    sources = result.get("sources") or []
    if sources:
        print("\n=== CONTEXT SỬ DỤNG ===")
        for idx, item in enumerate(sources, start=1):
            page = f" | Trang {item['page_number']}" if item.get("page_number") else ""
            score = f" | Score {item['similarity']:.4f}"
            print(f"[{idx}] Chunk {item['chunk_index']}{page}{score}")
            print(item["content"])
            print("-")

    metadata = result.get("metadata", {})
    print("\n=== METADATA ===")
    for key, value in metadata.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
