from __future__ import annotations

"""Nhận document_id từ dòng lệnh và kích hoạt pipeline xử lý embedding."""

import argparse
import sys
from pathlib import Path

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

from src.pipeline import process_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Nhận document_id và thực thi quy trình embedding trên Supabase"
    )
    parser.add_argument("document_id", help="Định danh tài liệu trong Supabase")
    parser.add_argument("job_id", nargs='?', default=None, help="ID của embedding job để tracking progress")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_document(args.document_id, args.job_id)


if __name__ == "__main__":
    main()
