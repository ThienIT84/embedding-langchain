# Phase B - Giải Thích Chi Tiết (Backend Integration via Single Port)

Phase B là gộp Phase A (Python RAG core) vào backend Node.js express, rồi frontend gọi qua API. **Chỉ 1 cổng duy nhất** (port 3000).

---

## 🏗️ Kiến Trúc Phase B

```
Frontend (React)                Backend (Express Node)           Python RAG (Phase A)
http://localhost:5173          http://localhost:3000            (child process)
    │                                 │                              │
    │ POST /api/rag/chat              │                              │
    │ (kèm Bearer token)              │                              │
    ├──────────────────────────>      │                              │
    │                                 │                              │
    │                            ragController.js                    │
    │                            (validate input)                    │
    │                                 │                              │
    │                            spawn python                        │
    │                                 ├─ PYTHONIOENCODING=utf-8     │
    │                                 ├─ cwd=/Embedding_langchain   │
    │                                 └─ stdin/stdout/stderr        │
    │                                 │                              │
    │                                 │  JSON stdin                  │
    │                                 ├────────────────────>         │
    │                                 │                              │
    │                                 │                    rag_runner.py
    │                                 │                    ├─ load .env
    │                                 │                    ├─ call rag_query()
    │                                 │                    │  ├─ retriever
    │                                 │                    │  ├─ prompt_builder
    │                                 │                    │  └─ llm_client (Ollama)
    │                                 │                    └─ print JSON stdout
    │                                 │  JSON stdout              │
    │                                 │  <────────────────        │
    │                                 │ (parse JSON)              │
    │                                 │                           │
    │  res.json(ragResult)            │                           │
    │  <─────────────────────────────┤                            │
    │                                                              │
    └─ display answer + sources                                    │
```

---

## 📋 Quy Trình Phase B (Chi Tiết)

### **Bước 1: Frontend Gửi Request**

File: `mindmap-notion-interface/src/pages/RagChatDemo.tsx`

```typescript
import { chatRAG } from '@/services/ragService';

const handleSubmit = async (e) => {
  e.preventDefault();
  
  // apiClient.post tự động lấy Supabase JWT token
  const response = await chatRAG({
    query: "Nêu ưu điểm KNN",
    documentId: "01287d1b-ca04-...",
    topK: 5
  });
  
  // response = {
  //   "answer": "...",
  //   "sources": [...],
  //   "metadata": {...},
  //   ...
  // }
  
  setAnswer(response.answer);
  setSources(response.sources);
};
```

**HTTP Request:**
```http
POST http://localhost:3000/api/rag/chat
Content-Type: application/json
Authorization: Bearer eyJhbGc...

{
  "query": "Nêu ưu điểm KNN",
  "documentId": "01287d1b-ca04-4c8e-9ec7-5126a606cc37",
  "topK": 5
}
```

---

### **Bước 2: Backend Nhận & Validate**

File: `mindmapnote2/backend/src/routes/ragRoutes.js`

```javascript
router.post('/chat', chatRAG);
// middleware authenticateUser đã check Bearer token
```

File: `mindmapnote2/backend/src/controllers/ragController.js`

```javascript
async function chatRAG(req, res) {
  const { query, documentId, topK, systemPrompt } = req.body;
  
  // Validate
  if (!query || !query.trim()) {
    return res.status(400).json({error: "Query không được để trống"});
  }
  if (!documentId) {
    return res.status(400).json({error: "documentId không được để trống"});
  }
  
  // Đọc env vars
  const pythonExe = process.env.RAG_PYTHON_PATH 
    || 'python';
  const runnerPath = process.env.RAG_RUNNER_PATH 
    || 'C:\\...\\Embedding_langchain\\scripts\\rag_runner.py';
  const runnerCwd = 'C:\\...\\Embedding_langchain';
  const timeoutMs = parseInt(process.env.RAG_TIMEOUT_MS || '180000');
  
  // Chuẩn bị payload cho Python
  const payload = {
    query,
    document_id: documentId,  // camelCase → snake_case
    top_k: topK || 5,
    system_prompt: systemPrompt
  };
  
  console.log('[RAG] Spawning Python:', pythonExe);
  console.log('[RAG] Payload:', JSON.stringify(payload));
  
  // ... spawn process (bên dưới)
}
```

---

### **Bước 3: Backend Spawn Python Process**

```javascript
// Spawn python process với UTF-8 encoding
const child = spawn(pythonExe, [runnerPath], {
  cwd: runnerCwd,
  env: {
    ...process.env,
    PYTHONIOENCODING: 'utf-8',  // ← FIX: hỗ trợ tiếng Việt
    PYTHONUTF8: '1'              // ← FIX: UTF-8 mode
  },
  stdio: ['pipe', 'pipe', 'pipe']  // stdin, stdout, stderr
});

// Bắt dữ liệu từ stdout (kết quả)
let stdout = '';
child.stdout.on('data', (data) => {
  console.log('[RAG stdout]', data.toString());
  stdout += data.toString();
});

// Bắt lỗi từ stderr
let stderr = '';
child.stderr.on('data', (data) => {
  console.error('[RAG stderr]', data.toString());
  stderr += data.toString();
});

// Timeout (180 giây = 3 phút)
let timeoutHandle = setTimeout(() => {
  console.error('[RAG] TIMEOUT after', timeoutMs, 'ms');
  child.kill();
}, timeoutMs);

// Xử lý khi process kết thúc
child.on('close', (code) => {
  clearTimeout(timeoutHandle);
  
  if (code !== 0) {
    console.error('RAG runner failed:', stderr);
    return res.status(500).json({
      error: 'RAG runner failed',
      details: stderr,
      code: 'RAG_RUNNER_FAILED'
    });
  }
  
  try {
    const result = JSON.parse(stdout);
    return res.status(200).json(result);
  } catch (e) {
    console.error('Invalid JSON:', stdout);
    return res.status(500).json({
      error: 'Invalid response from RAG runner'
    });
  }
});

// Gửi input qua stdin
child.stdin.write(JSON.stringify(payload));
child.stdin.end();
```

---

### **Bước 4: Python Runner Nhận Input**

File: `Embedding_langchain/scripts/rag_runner.py`

```python
#!/usr/bin/env python
"""
RAG runner cho Node backend
Nhận JSON từ stdin, trả JSON qua stdout
"""

import json
import sys
from pathlib import Path

# Đảm bảo sys.path có Embedding_langchain
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env từ Embedding_langchain
from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

def main() -> int:
    try:
        # Đọc JSON từ stdin
        raw = sys.stdin.read()
        if not raw:
            raise ValueError("No input on stdin")
        
        payload = json.loads(raw)
        
        query = payload.get("query")
        document_id = payload.get("document_id")
        top_k = payload.get("top_k", 5)
        system_prompt = payload.get("system_prompt")
        
        # Validate
        if not query or not document_id:
            raise ValueError("Missing query or document_id")
        
        # Import Phase A modules
        from src.rag_service import rag_query
        
        # Gọi Phase A
        result = rag_query(
            query=query,
            document_id=document_id,
            top_k=int(top_k),
            system_prompt=system_prompt
        )
        
        # In JSON qua stdout
        output = json.dumps(result, ensure_ascii=False)
        sys.stdout.write(output)
        sys.stdout.flush()
        
        return 0
        
    except Exception as e:
        # Ghi lỗi vào stderr (dùng repr để tránh encoding issue)
        err_msg = f"RAG runner error: {repr(e)}"
        sys.stderr.write(err_msg)
        sys.stderr.flush()
        return 1

if __name__ == "__main__":
    code = main()
    sys.exit(code)
```

---

### **Bước 5: Python Gọi Phase A**

```python
# rag_service.rag_query() là lõi RAG từ Phase A
# Thực hiện:

result = rag_query(
    query="Nêu ưu điểm KNN",
    document_id="01287d1b-...",
    top_k=5
)

# result = {
#   "answer": "Ưu điểm của KNN là...",
#   "sources": [
#     {
#       "chunk_id": "...",
#       "text": "K-Nearest Neighbors...",
#       "similarity": 0.92,
#       "source": {"document_id": "...", ...}
#     },
#     ...
#   ],
#   "metadata": {
#     "elapsed_ms": 1234,
#     "model": "llama3"
#   },
#   "prompt": "...",
#   "raw_llm_response": {...}
# }
```

**Chi tiết Phase A:**
1. **Retriever**: Embed query → tìm top-5 chunks
2. **Prompt Builder**: Ghép context + system instruction
3. **LLM Client**: Gọi Ollama llama3 → trả lời

---

### **Bước 6: Python In JSON Qua Stdout**

```python
# rag_runner.py ghi JSON ra stdout
output = json.dumps(result, ensure_ascii=False)
sys.stdout.write(output)  # ← Backend capture dòng này
sys.stdout.flush()
```

**Output (JSON):**
```json
{
  "answer": "Ưu điểm của KNN bao gồm:\n\n1. Đơn giản...",
  "sources": [
    {
      "chunk_id": "chunk-1",
      "text": "K-Nearest Neighbors là...",
      "similarity": 0.92,
      "source": {
        "document_id": "01287d1b-...",
        "chunk_index": 0
      }
    },
    ...
  ],
  "metadata": {
    "elapsed_ms": 34567,
    "model": "llama3"
  },
  "prompt": "Bạn là trợ lý...\n\nThông tin tham chiếu:\n...",
  "raw_llm_response": {
    "model": "llama3",
    "response": "...",
    "done": true
  }
}
```

---

### **Bước 7: Backend Parse & Return**

```javascript
// Backend parse JSON từ stdout
const result = JSON.parse(stdout);
// result = { answer, sources, metadata, ... }

// Trả về frontend
return res.status(200).json(result);
```

---

### **Bước 8: Frontend Hiển Thị**

```typescript
// RagChatDemo.tsx

const response = await chatRAG({...});

// response.answer → hiển thị trong div
setAnswer(response.answer);

// response.sources → map thành list
setSources(response.sources);

// Render:
// - Câu trả lời
// - Từng source kèm similarity score
```

---

## 🔌 Cấu Hình Environment Variables

### Backend (`mindmapnote2/backend/.env`):
```env
PORT=3000
NODE_ENV=development

# Supabase
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...

# RAG: trỏ tới Python venv
RAG_PYTHON_PATH=C:\Code\DACN_MindMapNote\Embedding_langchain\venv\Scripts\python.exe

# Optional:
# RAG_RUNNER_PATH=C:\Code\DACN_MindMapNote\Embedding_langchain\scripts\rag_runner.py
# RAG_TIMEOUT_MS=180000
```

### Python (`Embedding_langchain/.env`):
```env
# Supabase
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Embedding
HF_MODEL_NAME=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
CHUNK_SIZE=900
CHUNK_OVERLAP=200
```

---

## 📊 Luồng Dữ Liệu Phase B

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React)                              │
│ http://localhost:5173/rag-demo                                  │
│                                                                  │
│  [Input: query, documentId, topK]                               │
│           ↓                                                      │
│  Click "Hỏi" → POST /api/rag/chat                               │
│           ↓                                                      │
│  (+ Bearer token tự động từ Supabase)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    POST JSON body
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Backend (Node.js)                              │
│ http://localhost:3000                                            │
│                                                                  │
│ ragController.js:                                                │
│  1. Validate input                                               │
│  2. Đọc env vars (RAG_PYTHON_PATH, timeout, etc)               │
│  3. Set PYTHONIOENCODING=utf-8                                  │
│  4. Spawn Python process                                        │
│  5. Gửi JSON payload qua stdin                                  │
│  6. Bắt stdout/stderr                                           │
│  7. Parse JSON từ stdout                                        │
│  8. Return res.json(result)                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                 spawn child_process
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Python (RAG Core)                              │
│ rag_runner.py (short-lived process)                             │
│                                                                  │
│  1. Đọc JSON từ stdin                                           │
│  2. Load .env (Supabase, Ollama)                                │
│  3. Import Phase A modules:                                     │
│     - retriever.py (tìm chunks)                                 │
│     - prompt_builder.py (ghép prompt)                           │
│     - llm_client.py (gọi Ollama)                                │
│     - rag_service.py (điều phối)                                │
│  4. Call rag_query(query, document_id, top_k)                  │
│  5. Lấy kết quả (answer + sources)                              │
│  6. In JSON qua stdout                                          │
│  7. Exit code 0 (thành công) hoặc 1 (lỗi)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              stdout JSON (hoặc stderr error)
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Backend (Node.js)                              │
│  Parse JSON from stdout                                          │
│  Return res.json(result)                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              HTTP 200 JSON response
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (React)                               │
│  Hiển thị:                                                       │
│  - "Câu trả lời": response.answer                               │
│  - "Nguồn tham chiếu": response.sources[].text                 │
│     (+ similarity score)                                         │
│  - elapsed time, model name (metadata)                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Cách Hoạt Động Chi Tiết

### **1. Frontend Service (ragService.ts)**

```typescript
export async function chatRAG(payload: RAGChatRequest): Promise<RAGChatResponse> {
  // apiClient = client có sẵn, tự động:
  // - Lấy Supabase JWT token
  // - Set Authorization header
  // - Handle CORS
  
  return apiClient.post<RAGChatResponse>('/api/rag/chat', payload);
}
```

### **2. Backend Route (ragRoutes.js)**

```javascript
router.use(authenticateUser);  // ← Middleware check Bearer token
router.post('/chat', chatRAG);  // ← Gọi controller
```

**authenticateUser middleware:**
- Kiểm tra Authorization header
- Verify token với Supabase
- Nếu valid → req.user = user data
- Nếu invalid → 401 Unauthorized

### **3. Backend Controller (ragController.js)**

Xử lý logic:
1. Validate payload
2. Đọc env vars
3. Spawn Python
4. Manage stdin/stdout/stderr
5. Handle timeout
6. Parse & return

### **4. Python Runner (rag_runner.py)**

```python
def main():
    # Read JSON from stdin
    payload = json.loads(sys.stdin.read())
    
    # Call Phase A
    result = rag_service.rag_query(...)
    
    # Write JSON to stdout
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    
    return 0
```

---

## 🎯 Ưu Điểm Phase B (1 Cổng)

| Ưu điểm | Chi tiết |
|---------|---------|
| **Đơn giản** | Chỉ 1 server, 1 cổng (3000). Không cần quản lý 2 servers |
| **Stateless** | Mỗi request spawn Python process mới (clean state) |
| **Offline** | Không gọi API bên ngoài. Tất cả chạy locally |
| **Secure** | Backend check auth (Bearer token), Python không cần auth |
| **Scale-able** | Có thể thêm connection pool nếu cần nhiều request |

---

## ⚠️ Giới Hạn Phase B (1 Cổng)

| Hạn chế | Giải pháp |
|---------|-----------|
| **Chậm lần đầu** | Model embedding download ~500MB lần đầu (~2-3 phút) |
| **Memory** | Ollama + embedding model ~3-4GB RAM |
| **QPS** | ~1-2 request/giây (tùy Ollama performance) |
| **Timeout** | Nếu Ollama chậm, có thể bị timeout (tăng RAG_TIMEOUT_MS) |

---

## 🚀 Tóm Tắt Phase B

**Phase B = Bọc Phase A (Python RAG) thành HTTP API qua Node backend**

| Layer | Công nghệ | Cổng |
|-------|-----------|------|
| Frontend | React + TS | 5173 |
| Backend | Express Node.js | 3000 |
| Python | RAG service (Phase A) | (child process) |
| LLM | Ollama llama3 | 11434 |
| DB | Supabase pgvector | (cloud) |

**Flow:**
```
Frontend → Backend (HTTP) → Python (spawn) → Phase A → Ollama → DB
```

**Một cổng duy nhất:** `http://localhost:3000`

---

## 📚 File Chính Phase B

| File | Vị trí | Tác dụng |
|------|--------|---------|
| `ragService.ts` | frontend/src/services | POST /api/rag/chat wrapper |
| `RagChatDemo.tsx` | frontend/src/pages | UI demo |
| `ragRoutes.js` | backend/src/routes | Route + auth |
| `ragController.js` | backend/src/controllers | Spawn process + manage I/O |
| `rag_runner.py` | Embedding_langchain/scripts | CLI wrapper cho Phase A |

---

Bây giờ bạn hiểu Phase B rồi! Muốn test end-to-end không?

