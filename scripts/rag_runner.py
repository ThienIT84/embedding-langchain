#!/usr/bin/env python
"""
Script chạy RAG để tích hợp với Node.js child-process.
Đọc JSON từ stdin với các field:
{
  "query": "...",                # bắt buộc - câu hỏi của user
  "user_id": "...",              # bắt buộc - UUID của user (từ JWT token)
  "top_k": 5,                    # tuỳ chọn, mặc định 5 - số chunks lấy ra
  "system_prompt": "..."         # tuỳ chọn - hướng dẫn cho LLM
}

PHASE C1: Đã đổi từ document_id → user_id để search toàn bộ documents của user.

Ghi một dòng JSON duy nhất ra stdout khi thành công và exit code 0.
Nếu lỗi, ghi message ra stderr và exit code khác 0.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Đảm bảo project root (Embedding_langchain) được thêm vào sys.path
# Để có thể import các module từ src.*
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent  # .../Embedding_langchain
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file từ thư mục Embedding_langchain
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except Exception:
    # dotenv là tuỳ chọn; config.py có thể đọc env từ process
    pass


def _read_stdin_json() -> Dict[str, Any]:
    """Đọc JSON từ stdin - dữ liệu từ Node.js process"""
    raw = sys.stdin.read()
    if not raw:
        raise ValueError("Không có input từ stdin; cần JSON payload")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON input không hợp lệ: {e}")


def main() -> int:
    """Hàm chính xử lý RAG query"""
    try:
        # Đọc dữ liệu JSON từ Node.js
        payload = _read_stdin_json()
        query = payload.get("query")
        user_id = payload.get("user_id")  # ĐÃ ĐỔI: Từ document_id → user_id
        top_k = payload.get("top_k", 5)
        system_prompt = payload.get("system_prompt")
        model = payload.get("model")

        # Validate query - phải có và không rỗng
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Field 'query' là bắt buộc và phải là chuỗi không rỗng")
        
        # Validate user_id - phải có (UUID từ JWT token)
        # ĐÃ ĐỔI: Kiểm tra user_id thay vì document_id
        if user_id is None or (isinstance(user_id, str) and not user_id.strip()):
            raise ValueError("Field 'user_id' là bắt buộc (UUID của user từ JWT token)")
        
        # Chuyển top_k thành int, mặc định 5 nếu không hợp lệ
        try:
            top_k = int(top_k)
        except Exception:
            top_k = 5
        if top_k <= 0:
            top_k = 5

        # Import RAG service (thực hiện sau khi sys.path + env sẵn sàng)
        from src.rag_service import rag_query  # type: ignore

        # Gọi hàm RAG query - PHASE C1: Truyền user_id thay vì document_id
        # Function rag_query sẽ gọi retrieve_similar_chunks_by_user()
        # → RPC match_embeddings_by_user() → search TẤT CẢ documents của user
        result = rag_query(
            query=query,
            user_id=user_id,  # ĐÃ ĐỔI: Truyền user_id thay vì document_id
            top_k=top_k,
            system_prompt=system_prompt,
            model=model,
        )

        # Đảm bảo result có thể serialize thành JSON
        out = json.dumps(result, ensure_ascii=False)
        # Ghi kết quả ra stdout để Node.js đọc
        sys.stdout.write(out)
        sys.stdout.flush()
        return 0

    except Exception as e:
        # Ghi lỗi ra stderr với định dạng tốt nhất
        # Dùng repr() để tránh vấn đề encoding trên Windows
        err_msg = f"RAG runner error: {repr(e)}"
        try:
            sys.stderr.write(err_msg)
        except Exception:
            # Nếu stderr cũng fail, ghi minimal ASCII message
            sys.stderr.write("RAG runner error: encoding issue")
        sys.stderr.flush()
        return 1


if __name__ == "__main__":
    # Chạy hàm main và exit với code trả về
    code = main()
    sys.exit(code)
