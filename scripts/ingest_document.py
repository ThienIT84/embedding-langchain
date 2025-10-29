from __future__ import annotations

"""Nhận document_id từ dòng lệnh và kích hoạt pipeline xử lý embedding."""

import argparse

from src.pipeline import process_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Nhận document_id và thực thi quy trình embedding trên Supabase"
    )
    parser.add_argument("document_id", help="Định danh tài liệu trong Supabase")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_document(args.document_id)


if __name__ == "__main__":
    main()
