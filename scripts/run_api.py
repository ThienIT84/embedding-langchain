from __future__ import annotations

"""Starter cho FastAPI với cấu hình PYTHONPATH phù hợp khi dùng reload trên Windows."""

import os
import sys
from pathlib import Path

import uvicorn


def _ensure_pythonpath() -> None:
    """Đảm bảo thư mục dự án nằm trong PYTHONPATH để uvicorn reload import được 'api.*'."""
    project_root = Path(__file__).resolve().parents[1]
    # Thêm vào sys.path cho tiến trình hiện tại
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    # Thiết lập biến môi trường để tiến trình reload kế thừa
    existing = os.environ.get("PYTHONPATH", "")
    paths = [str(project_root)] + ([existing] if existing else [])
    os.environ["PYTHONPATH"] = os.pathsep.join(paths)


if __name__ == "__main__":
    _ensure_pythonpath()
    # Chạy FastAPI server cho RAG API
    project_root = Path(__file__).resolve().parents[1]
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root)],
    )
