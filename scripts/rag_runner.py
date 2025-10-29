#!/usr/bin/env python
"""
Simple RAG runner for Node.js child-process integration.
Reads JSON from stdin with fields:
{
  "query": "...",                # required
  "document_id": "...",         # required (string or int acceptable)
  "top_k": 5,                    # optional, default 5
  "system_prompt": "..."        # optional
}

Writes a single JSON line to stdout on success and exits with code 0.
On error, writes a human-readable message to stderr and exits with non-zero code.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure project root (Embedding_langchain) is on sys.path so we can import src.*
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent  # .../Embedding_langchain
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env from Embedding_langchain root
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
except Exception:
    # dotenv is optional; config.py may still read env from process
    pass


def _read_stdin_json() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw:
        raise ValueError("No input received on stdin; expected JSON payload")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON input: {e}")


def main() -> int:
    try:
        payload = _read_stdin_json()
        query = payload.get("query")
        document_id = payload.get("document_id")
        top_k = payload.get("top_k", 5)
        system_prompt = payload.get("system_prompt")

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Field 'query' is required and must be a non-empty string")
        if document_id is None or (isinstance(document_id, str) and not document_id.strip()):
            raise ValueError("Field 'document_id' is required")
        # Normalize top_k
        try:
            top_k = int(top_k)
        except Exception:
            top_k = 5
        if top_k <= 0:
            top_k = 5

        # Import here to ensure sys.path + env are ready
        from src.rag_service import rag_query  # type: ignore

        result = rag_query(
            query=query,
            document_id=document_id,
            top_k=top_k,
            system_prompt=system_prompt,
        )

        # Ensure it's JSON serializable
        out = json.dumps(result, ensure_ascii=False)
        sys.stdout.write(out)
        sys.stdout.flush()
        return 0

    except Exception as e:
        # Best-effort structured error on stderr
        # Use repr() to avoid encoding issues on Windows
        err_msg = f"RAG runner error: {repr(e)}"
        try:
            sys.stderr.write(err_msg)
        except Exception:
            # If even stderr fails, write minimal ASCII message
            sys.stderr.write("RAG runner error: encoding issue")
        sys.stderr.flush()
        return 1


if __name__ == "__main__":
    code = main()
    sys.exit(code)
