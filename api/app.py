from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router as rag_router

app = FastAPI(title="Embedding RAG API", version="0.1.0")

# CORS for local dev: read from env or allow localhost defaults
origins_env = os.getenv("API_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins_env if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router)
