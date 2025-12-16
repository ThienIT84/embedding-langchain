# Phase B: Backend Integration (Single-Port Architecture)

## Tổng Quan

**Phase B** là giai đoạn tích hợp hệ thống RAG vào backend Express.js, cho phép frontend React gọi API để thực hiện truy vấn RAG một cách thực tế.

Thay vì chạy Python RAG standalone, chúng ta sử dụng **Node.js backend (Express.js)** để:
1. Nhận request từ frontend React
2. Spawn Python process (rag_runner.py) để xử lý
3. Trả về kết quả JSON cho frontend

**Lợi ích:**
- ✅ Single-port architecture (Express chạy trên 1 cổng, frontend cũng trên 1 cổng)
- ✅ Stateless Python processes (spawn khi cần, kill khi xong)
- ✅ Dễ scale horizontally (mỗi request tạo process mới)
- ✅ Vietnamese text support (UTF-8 encoding xử lý tốt)

---

## Kiến Trúc Phase B

```
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend (port 5173)                │
│              mindmap-notion-interface/src                   │
│                    (RagChatDemo.tsx)                        │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      │ HTTP POST /api/rag/chat
                      │ {query, documentId, topK, systemPrompt}
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Express.js Backend (port 3000)                    │
│         mindmapnote2/backend/src                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ragController.js / chatRAG(req, res)                │   │
│  │  - Parse request body                                │   │
│  │  - Validate query & documentId                       │   │
│  │  - Set timeout (180s)                                │   │
│  │  - Build stdin payload (JSON)                        │   │
│  └──────────┬───────────────────────────────────────────┘   │
│             │ spawn() child_process                         │
│             ▼                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Python Process (rag_runner.py)                      │   │
│  │  - Read JSON from stdin                              │   │
│  │  - Call rag_query() from rag_service.py              │   │
│  │  - Handle UTF-8 encoding (Vietnamese)                │   │
│  │  - Write JSON result to stdout                       │   │
│  │  - Exit gracefully                                   │   │
│  └──────────┬───────────────────────────────────────────┘   │
│             │ stdout (JSON result)                         │
│             ▼                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ragController.js                                    │   │
│  │  - Parse stdout JSON                                 │   │
│  │  - Return res.json(result)                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      │ HTTP 200 + JSON response
                      │ {answer, sources, metadata, ...}
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend                            │
│              Display answer + sources                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│               Supabase PostgreSQL (pgvector)                │
│                  Shared by all requests                     │
│  - Vector embeddings (768-dim)                             │
│  - Document chunks                                         │
│  - Metadata                                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│               Ollama llama3 (Local LLM)                      │
│            http://localhost:11434                           │
│              Shared by all requests                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Chi Tiết

### 1. Frontend gửi request

**File:** `mindmap-notion-interface/src/services/ragService.ts`

```typescript
export async function chatRAG(
  query: string,
  documentId: string | number,
  topK?: number,
  systemPrompt?: string
) {
  const response = await apiClient.post('/api/rag/chat', {
    query,
    documentId,
    topK,
    systemPrompt
  });
  return response.data; // {answer, sources, metadata, ...}
}
```

**HTTP Request:**
```
POST /api/rag/chat
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>

{
  "query": "Tài liệu này nói gì về machine learning?",
  "documentId": 123,
  "topK": 5,
  "systemPrompt": "Bạn là trợ lý AI giúp tóm tắt tài liệu."
}
```

---

### 2. Backend nhận request

**File:** `mindmapnote2/backend/src/controllers/ragController.js`

```javascript
async function chatRAG(req, res) {
  const { query, documentId, topK, systemPrompt } = req.body;
  
  // Validation
  if (!query || !query.trim()) {
    return res.status(400).json({error: "query is required"});
  }
  if (!documentId) {
    return res.status(400).json({error: "documentId is required"});
  }
  
  // Lấy đường dẫn Python executable
  const pythonExe = process.env.RAG_PYTHON_PATH 
    || 'python';
  
  // Lấy đường dẫn runner script
  const runnerPath = process.env.RAG_RUNNER_PATH 
    || '/path/to/rag_runner.py';
  
  // Timeout 180 giây (3 phút) - đủ cho lần đầu load model
  const timeoutMs = 180000;
  
  // Build payload để gửi cho Python
  const payload = {
    query,
    document_id: documentId,
    top_k: topK,
    system_prompt: systemPrompt
  };
}
```

**Environment Variables (.env):**
```env
RAG_PYTHON_PATH=C:\Code\DACN_MindMapNote\Embedding_langchain\venv\Scripts\python.exe
RAG_RUNNER_PATH=C:\Code\DACN_MindMapNote\Embedding_langchain\scripts\rag_runner.py
RAG_TIMEOUT_MS=180000
```

---

### 3. Backend spawn Python process

```javascript
const child = spawn(pythonExe, [runnerPath], {
  cwd: runnerCwd,
  env: { 
    ...process.env,
    PYTHONIOENCODING: 'utf-8',  // ← Critical cho Vietnamese!
    PYTHONUTF8: '1'              // ← Enable UTF-8 mode on Windows
  },
  stdio: ['pipe', 'pipe', 'pipe']
  // stdin, stdout, stderr đều là pipes
});

// Ghi payload JSON vào stdin
child.stdin.write(JSON.stringify(payload));
child.stdin.end();

// Lắng nghe stdout và stderr
let stdout = '';
let stderr = '';

child.stdout.on('data', (data) => {
  stdout += data.toString();
  console.log('[RAG stdout]', data.toString());
});

child.stderr.on('data', (data) => {
  stderr += data.toString();
  console.error('[RAG stderr]', data.toString());
});
```

**Tại sao cần PYTHONIOENCODING?**
- Windows mặc định dùng encoding là `cp1252` (Latin-1)
- Vietnamese text (UTF-8) không thể encode được → lỗi `charmap`
- Solution: Force Python dùng UTF-8 cho I/O

---

### 4. Python process (rag_runner.py)

**File:** `Embedding_langchain/scripts/rag_runner.py`

```python
import sys
import json
import os

# Đảm bảo sys.path có thư mục Embedding_langchain
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_service import rag_query

# Đọc JSON từ stdin
input_data = sys.stdin.read()
payload = json.loads(input_data)

query = payload.get('query')
document_id = payload.get('document_id')
top_k = payload.get('top_k', 5)
system_prompt = payload.get('system_prompt')

try:
  # Gọi RAG core function
  result = rag_query(
    query=query,
    document_id=document_id,
    top_k=top_k,
    system_prompt=system_prompt
  )
  
  # Ghi kết quả JSON vào stdout
  print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stdout)
  sys.exit(0)
  
except Exception as e:
  # Ghi lỗi ra stderr (không dùng stdout)
  error_result = {
    'error': str(e),
    'type': type(e).__name__
  }
  print(json.dumps(error_result, ensure_ascii=False), file=sys.stderr)
  sys.exit(1)
```

**Luồng xử lý:**
1. Đọc JSON từ stdin (dữ liệu từ Node.js)
2. Parse thành dict Python
3. Gọi `rag_query()` để:
   - Truy vấn vector DB (Supabase)
   - Lấy top_k chunks liên quan
   - Build prompt cho LLM
   - Gọi Ollama llama3
   - Trả về answer + sources
4. Ghi JSON kết quả vào stdout
5. Exit code 0 (thành công) hoặc 1 (lỗi)

**Output Format (JSON):**
```json
{
  "answer": "Machine learning là...",
  "sources": [
    {
      "chunk": "Đoạn text từ document...",
      "similarity": 0.8234,
      "metadata": {"page": 1, "section": "Introduction"}
    }
  ],
  "metadata": {
    "document_id": 123,
    "query": "Tài liệu này nói gì về machine learning?",
    "processing_time_ms": 2340
  }
}
```

---

### 5. Backend nhận stdout từ Python

```javascript
child.on('close', (code) => {
  clearTimeout(timeoutHandle);
  
  if (code !== 0) {
    // Python exited with error
    return res.status(500).json({
      error: 'RAG runner failed',
      details: stderr,
      code: 'RAG_RUNNER_FAILED'
    });
  }
  
  try {
    // Parse stdout JSON
    const result = JSON.parse(stdout);
    
    // Trả về cho frontend
    return res.status(200).json(result);
  } catch (e) {
    return res.status(500).json({
      error: 'Invalid JSON from RAG runner',
      details: e.message
    });
  }
});
```

---

### 6. Frontend nhận response

**File:** `mindmap-notion-interface/src/pages/RagChatDemo.tsx`

```typescript
const { data, isLoading, error } = useQuery(
  ['rag-chat', query],
  () => chatRAG(query, documentId, topK, systemPrompt),
  { enabled: !!query }
);

return (
  <div>
    {isLoading && <p>Loading...</p>}
    {error && <p>Error: {error.message}</p>}
    {data && (
      <div>
        <h3>Answer:</h3>
        <p>{data.answer}</p>
        
        <h3>Sources:</h3>
        {data.sources.map((source, idx) => (
          <div key={idx}>
            <p>{source.chunk}</p>
            <small>Similarity: {source.similarity.toFixed(3)}</small>
          </div>
        ))}
      </div>
    )}
  </div>
);
```

---

## Key Features

### 1. **UTF-8 Encoding Support (Vietnamese)**

**Problem:** Windows mặc định dùng `cp1252`, không handle Vietnamese text

**Solution:**
```javascript
env: {
  ...process.env,
  PYTHONIOENCODING: 'utf-8',
  PYTHONUTF8: '1'
}
```

**Kết quả:** Vietnamese text được encode/decode đúng cách, không bị "mojibake"

---

### 2. **Timeout Management**

```javascript
const timeoutMs = 180000; // 3 phút

const timeoutHandle = setTimeout(() => {
  console.error('[RAG] TIMEOUT - killing process');
  child.kill(); // Terminate process gracefully
}, timeoutMs);

child.on('close', (code) => {
  clearTimeout(timeoutHandle); // Clear timeout nếu process tự exit
});
```

**Tại sao 180 giây?**
- Lần đầu load model: ~60-90 giây (download + cache)
- Lần sau: ~10-30 giây
- Buffer: +60 giây cho edge cases
- Total: 180 giây (3 phút) đủ an toàn

---

### 3. **Error Handling Levels**

| Level | Handler | Example |
|-------|---------|---------|
| **Frontend validation** | 400 Bad Request | Missing query field |
| **Python crash** | `child.on('error')` | spawn fails |
| **Python exit code != 0** | `child.on('close')` code check | Python error |
| **Invalid JSON** | JSON.parse() catch | Malformed output |
| **Timeout** | setTimeout callback | Process hangs |

---

### 4. **Stateless Architecture**

Mỗi request là độc lập:
- ✅ No shared state between requests
- ✅ No memory leaks (process dies after each request)
- ✅ Easy to restart / recover
- ✅ Can run multiple requests in parallel

---

## Configuration Files

### `.env` (Backend)
```env
# RAG Configuration
RAG_PYTHON_PATH=C:\Code\DACN_MindMapNote\Embedding_langchain\venv\Scripts\python.exe
RAG_RUNNER_PATH=C:\Code\DACN_MindMapNote\Embedding_langchain\scripts\rag_runner.py
RAG_TIMEOUT_MS=180000

# Python path for subprocess
PYTHONPATH=C:\Code\DACN_MindMapNote\Embedding_langchain
```

### `Embedding_langchain/requirements.txt`
```
numpy<2.0.0           # Must pin < 2.0.0 for Torch/TF compatibility
sentence-transformers # Multilingual embeddings
supabase              # pgvector client
langchain-text-splitters
python-dotenv
requests
```

---

## Testing Phase B

### 1. Manual test via HTTP

```bash
curl -X POST http://localhost:3000/api/rag/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "query": "Tài liệu này nói gì?",
    "documentId": 1,
    "topK": 3
  }'
```

### 2. Test via Frontend (RagChatDemo)

1. Start backend: `npm run dev` (port 3000)
2. Start frontend: `npm run dev` (port 5173)
3. Go to `http://localhost:5173/rag-demo`
4. Login with Supabase credentials
5. Enter query, select document, click Chat

### 3. Debug via logs

**Backend logs:**
```
[RAG] Spawning Python: python.exe
[RAG] Runner path: C:\Code\...\rag_runner.py
[RAG] Timeout: 180000 ms
[RAG] Payload: {"query":"...","document_id":1,...}
[RAG stdout] {...answer...}
[RAG] Process closed with code: 0
[RAG] Success - returning answer
```

---

## Performance Considerations

| Metric | Typical Value | Notes |
|--------|---------------|-------|
| **Embedding lookup** | 50-100ms | IVFFlat index on pgvector |
| **Python startup** | 2-5s | Cold start overhead |
| **LLM generation** | 10-30s | Ollama on CPU (local) |
| **Total (1st request)** | 80-140s | Plus model loading |
| **Total (subsequent)** | 15-40s | Model cached |

**Optimization tips:**
- Keep Ollama running 24/7 (no shutdown between requests)
- Increase `top_k` gradually (tradeoff between relevance & latency)
- Monitor Supabase query performance (add IVFFlat index if not present)

---

## Debugging Checklist

- [ ] Check `.env` has correct paths for `RAG_PYTHON_PATH`
- [ ] Verify Python venv is activated with correct packages: `pip list | grep -E "sentence-transformers|supabase|numpy"`
- [ ] Test Python directly: `python Embedding_langchain/scripts/rag_runner.py < test_input.json`
- [ ] Check Supabase pgvector has IVFFlat index on `embeddings` table
- [ ] Verify Ollama running: `curl http://localhost:11434/api/tags`
- [ ] Monitor backend logs for `[RAG]` prefix messages
- [ ] Test UTF-8: Send Vietnamese text in query, check logs for encoding errors

---

## Summary

**Phase B** chuyển đổi RAG từ standalone Python scripts thành **HTTP API** thông qua:

1. **Frontend** → gửi JSON request via HTTP POST
2. **Express backend** → nhận request, spawn Python process
3. **Python runner** → xử lý RAG logic, trả về JSON
4. **Express backend** → parse kết quả, gửi lại frontend
5. **Frontend** → hiển thị answer + sources

Kiến trúc này cho phép:
- ✅ Multiple concurrent requests (mỗi spawn process mới)
- ✅ Vietnamese text support (UTF-8 encoding)
- ✅ Easy error handling (exit codes, stderr capture)
- ✅ Clean separation of concerns (Node ↔ Python)
- ✅ Single-port architecture (Express on 3000, Frontend on 5173)

**Next Step:** Phase C (nếu có) có thể là tối ưu hóa performance, caching, hay integrate thêm features.
