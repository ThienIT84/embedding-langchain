from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

"""Đọc cấu hình môi trường cho pipeline embedding."""

# Nạp biến môi trường từ file .env nếu tồn tại
load_dotenv()


def _get_env(name: str, default: str | None = None, required: bool = True) -> str:
    """Đọc biến môi trường, cho phép giá trị mặc định và đánh dấu bắt buộc."""
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value if value is not None else ""


@dataclass(frozen=True)
class Settings:
    supabase_url: str = _get_env("SUPABASE_URL")
    supabase_service_key: str = _get_env("SUPABASE_SERVICE_KEY")
    supabase_bucket: str = _get_env("SUPABASE_BUCKET", "documents")
    hf_model_name: str = _get_env(
        "HF_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2", required=False
    )
    hf_api_token: str = _get_env("HF_API_TOKEN", required=False)
    chunk_size: int = int(_get_env("CHUNK_SIZE", "900", required=False) or 900)
    chunk_overlap: int = int(_get_env("CHUNK_OVERLAP", "200", required=False) or 200)
    temp_dir: Path = Path(_get_env("TEMP_DIR", "tmp", required=False) or "tmp")
    ollama_url: str = _get_env("OLLAMA_URL", "http://localhost:11434", required=False)
    ollama_model: str = _get_env("OLLAMA_MODEL", "llama3", required=False)


settings = Settings()
settings.temp_dir.mkdir(parents=True, exist_ok=True)
