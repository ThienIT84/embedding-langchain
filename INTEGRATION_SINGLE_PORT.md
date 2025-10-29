# Single-Port Integration (Express + Python child-process)

This setup lets your existing Node/Express backend call the Python RAG pipeline without running a second HTTP server. The Node route spawns a short-lived Python process for each request and returns the JSON response to the frontend.

## How it works

- Frontend calls your Node server at `POST /api/rag/chat`.
- Express spawns Python and runs `scripts/rag_runner.py` with a JSON payload on stdin.
- The Python runner loads `.env`, calls `src/rag_service.rag_query(...)`, prints JSON, and exits.
- Express returns that JSON to the client. Only one server/port is used.

## Requirements

- Valid `.env` in `Embedding_langchain/` with at least:
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, optional `SUPABASE_BUCKET`
  - `OLLAMA_URL`, `OLLAMA_MODEL`
  - Optional chunking/model overrides
- Node backend `.env` can optionally define:
  - `RAG_PYTHON_PATH` to an explicit Python executable
  - `RAG_RUNNER_PATH` to the absolute path of `scripts/rag_runner.py`
  - `RAG_TIMEOUT_MS` (default 60000)

If not set, the backend will try sensible defaults:
- `python` from PATH
- Runner path resolved relative to the repo
- `cwd` set to `Embedding_langchain/` so the Python runner can load `.env`

## Endpoint contract

POST `/api/rag/chat`

Body JSON:
```
{
  "query": "your user question",        // required
  "documentId": "uuid-or-id",           // required
  "topK": 5,                             // optional, default 5
  "systemPrompt": "..."                 // optional
}
```

Response JSON (from `rag_service.rag_query`):
```
{
  "answer": "...",
  "sources": [
    { "chunk_id": "...", "text": "...", "similarity": 0.87, "source": { /* doc meta */ } }
  ],
  "metadata": { "elapsed_ms": 1234, "model": "llama3" },
  "prompt": "...",
  "raw_llm_response": { /* provider-specific */ }
}
```

## Notes

- This approach is simple and local-friendly. For high QPS or horizontal scaling, consider running a persistent Python API and calling it over HTTP instead.
- On Windows, ensure your Python and Ollama are accessible to the Node process (either in PATH or via absolute paths in `.env`).
