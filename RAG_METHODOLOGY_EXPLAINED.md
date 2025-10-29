# RAG Methodology - Hướng Dẫn Đọc Code & Luồng Xử Lý

## 📖 Thứ Tự Đọc Code (Từ Dễ → Khó)

Để hiểu toàn bộ phương thức RAG, bạn nên đọc theo thứ tự sau:

1. **`src/config.py`** — 2–3 phút (đã biết rồi)
   - Lấy cấu hình SUPABASE_URL, OLLAMA_URL, OLLAMA_MODEL, v.v.
   - Điểm mấu chốt: `settings` là singleton, load từ `.env`.

2. **`src/retriever.py`** — 10 phút
   - Lấy context từ Supabase dựa trên câu hỏi.
   - Đây là bước "R" (Retrieval) trong RAG.

3. **`src/prompt_builder.py`** — 5 phút
   - Ghép context + câu hỏi thành prompt.
   - Điểm quan trọng: format sao cho LLM dễ đọc và hiểu được giới hạn (chỉ dựa trên context).

4. **`src/llm_client.py`** — 5 phút
   - Gọi Ollama HTTP API.
   - Trả về câu trả lời từ LLM.
   - Xử lý lỗi khi Ollama không chạy.

5. **`src/rag_service.py`** — 5 phút
   - **Orchestrator**: nối 3 bước trên thành một hàm chính.
   - Đây là giao diện duy nhất backend/frontend cần gọi.

6. **`scripts/rag_query.py`** — 3 phút
   - CLI wrapper, test tool.

---

## 🎯 Tổng Quan Phương Thức RAG

### Khái Niệm
**RAG = Retrieval-Augmented Generation**
- **Retrieval**: Tìm kiếm (lấy tài liệu/chunk gần nhất).
- **Augmented**: Tăng cường dữ liệu (đẩy context vào prompt).
- **Generation**: Sinh (LLM sinh câu trả lời dựa trên context).

### Vấn Đề mà RAG giải quyết
- **LLM thuần** (ví dụ llama3 local) có kiến thức cắt từ lúc train → không biết tài liệu mới.
- **RAG**: Đẩy tài liệu của bạn vào prompt → LLM sinh câu trả lời dựa trên tài liệu thực.

### Quy Trình Tổng Quát (Level 0)

```
Người dùng hỏi: "Introduce about the article"
        ↓
[Retriever] Tìm top-k chunks gần nhất
        ↓
[Prompt Builder] Ghép chunks + câu hỏi thành prompt
        ↓
[LLM Client] Gửi prompt lên Ollama llama3
        ↓
[Ollama] Sinh câu trả lời
        ↓
Trả về: { answer, sources, metadata }
```

---

## 🔍 Chi Tiết Từng Bước

### BƯỚC 1: Retrieval (`src/retriever.py`)

**Mục tiêu**
- Tìm những đoạn văn bản (chunks) trong Supabase có **ý nghĩa tương tự** nhất với câu hỏi.
- Ví dụ: câu hỏi "Ollama là gì?" → tìm chunks nói về Ollama.

**Hợp Đồng Hàm Chính**

```python
def retrieve_similar_chunks(
    query: str,                      # Câu hỏi người dùng
    document_id: str,                # ID tài liệu trong Supabase
    top_k: int = 5                   # Số chunks muốn lấy
) -> List[RetrievedChunk]:           # Danh sách chunks sắp xếp theo độ tương tự
    """
    Input:
      - query: "Introduce about the article"
      - document_id: "01287d1b-ca04-4c8e-9ec7-5126a606cc37"
      - top_k: 5
    
    Output:
      [
        RetrievedChunk(
          content="Article là một bài viết...",
          chunk_index=3,
          page_number=1,
          similarity=0.87  # Càng cao (→1) càng giống
        ),
        RetrievedChunk(
          content="Bài viết này nói về...",
          chunk_index=5,
          page_number=2,
          similarity=0.82
        ),
        ...
      ]
    
    Raise:
      - ValueError: nếu query hoặc document_id rỗng
      - Nếu không có chunk nào → trả về []
    """
```

**Luồng Xử Lý Bên Trong**

```
1. Query embedding
   - Dùng SentenceTransformer (cùng model lúc ingest)
   - Chuyển "Introduce about the article" → vector 768 chiều
   
2. Fetch chunks từ Supabase
   SELECT content, chunk_index, page_number, embedding
   FROM document_embeddings
   WHERE document_id = ?
   
3. Tính similarity
   FOR each chunk in chunks:
     cos_score = cosine_similarity(query_vector, chunk_embedding)
     # Formula: (a·b) / (||a|| × ||b||)
   
4. Sort & slice
   sorted_by_score DESC → lấy top_k chunks đầu
```

**Ví Dụ Cosine Similarity**

Nếu:
- Query vector: [0.1, 0.2, 0.3, ..., 0.4]  (768 số)
- Chunk 1 vector: [0.15, 0.18, 0.35, ..., 0.42]  → similarity = 0.95 (rất giống)
- Chunk 2 vector: [0.8, 0.9, -0.5, ..., 0.1]  → similarity = 0.45 (không giống)

→ Chunk 1 được chọn trước.

**Xử Lý Lỗi Thường Gặp**

| Lỗi | Nguyên nhân | Xử lý |
|-----|-------------|-------|
| `ValueError: Query không được để trống` | query = "" | Check empty string |
| `ValueError: document_id không được để trống` | document_id = "" | Check empty string |
| Embedding là chuỗi JSON | Supabase trả `embedding` dạng `"[0.1, 0.2, ...]"` | Parse JSON + convert to numpy array |
| Vector rỗng/độ dài 0 | Dữ liệu hỏng | Skip vector đó |
| Không kết nối Supabase | Thiếu .env | Xem lỗi từ supabase_client |

---

### BƯỚC 2: Prompt Building (`src/prompt_builder.py`)

**Mục tiêu**
- Tạo một prompt rõ ràng cho LLM.
- Prompt = (system instruction) + (context) + (câu hỏi) + (yêu cầu).

**Hợp Đồng Hàm Chính**

```python
def build_rag_prompt(
    query: str,                           # Câu hỏi
    chunks: Sequence[RetrievedChunk],     # Danh sách chunks từ retriever
    system_prompt: str | None = None      # Tuỳ chọn: hướng dẫn hệ thống
) -> str:                                 # Prompt hoàn chỉnh
    """
    Input:
      - query: "Introduce about the article"
      - chunks: [
          RetrievedChunk(content="Article là...", chunk_index=3, page_number=1, similarity=0.87),
          RetrievedChunk(content="Bài viết này...", chunk_index=5, page_number=2, similarity=0.82),
          ...
        ]
      - system_prompt: None (dùng mặc định)
    
    Output (chuỗi):
    ┌─────────────────────────────────────────┐
    │ Bạn là trợ lý AI hỗ trợ trả lời câu hỏi │
    │ dựa trên các đoạn văn bản cung cấp...    │
    │                                         │
    │ Context:                                │
    │ Đoạn 1 | Trang 1 | Score: 0.8700       │
    │ Article là một bài viết...             │
    │                                         │
    │ Đoạn 2 | Trang 2 | Score: 0.8200       │
    │ Bài viết này nói về...                 │
    │                                         │
    │ Câu hỏi: Introduce about the article   │
    │ Hãy cung cấp câu trả lời ngắn gọn...   │
    └─────────────────────────────────────────┘
    
    Raise:
      - ValueError: nếu query rỗng
    """
```

**Cấu Trúc Prompt Chi Tiết**

```
<SYSTEM PROMPT>
Bạn là trợ lý AI hỗ trợ trả lời câu hỏi dựa trên các đoạn văn bản cung cấp.
Chỉ sử dụng thông tin trong phần Context.
Nếu Context không đủ, hãy nói rõ bạn không chắc chắn.
Trả lời ngắn gọn bằng tiếng Việt, ưu tiên liệt kê bullet khi phù hợp.

<CONTEXT>
Đoạn 1 | Trang 1 | Score: 0.8700
<nội dung chunk 1>

Đoạn 2 | Trang 2 | Score: 0.8200
<nội dung chunk 2>

(... thêm các đoạn khác ...)

<QUESTION>
Câu hỏi: Introduce about the article
Hãy cung cấp câu trả lời ngắn gọn và chỉ dựa trên context ở trên.
```

**Tại Sao Cần System Prompt?**
- Giới hạn LLM: "Chỉ trả lời dựa trên context" → tránh LLM dựa vào kiến thức huấn luyện (có thể sai).
- Hướng dẫn format: "Trả lời ngắn gọn, liệt kê bullet" → output dễ đọc.
- Xác định ngôn ngữ: "bằng tiếng Việt" → output đúng ngôn ngữ.

---

### BƯỚC 3: LLM Call (`src/llm_client.py`)

**Mục Tiêu**
- Gửi prompt tới Ollama (llama3 local).
- Nhận câu trả lời đã sinh.

**Hợp Đồng Hàm Chính**

```python
def generate_answer(
    prompt: str,                    # Prompt đầy đủ từ prompt_builder
    model: str | None = None,       # Model name (mặc định: settings.ollama_model)
    timeout: int = 120              # Timeout (giây)
) -> LLMResponse:                   # Kết quả từ LLM
    """
    Input:
      - prompt: "<SYSTEM>....<CONTEXT>....<QUESTION>..."
      - model: None → dùng "llama3"
      - timeout: 120
    
    Output:
      LLMResponse(
        answer="Article là một loại tài liệu...",
        model="llama3",
        raw={...} # JSON gốc từ Ollama
      )
    
    Raise:
      - ValueError: prompt rỗng
      - LLMClientError: Không kết nối Ollama
      - LLMClientError: Response không hợp lệ
    """
```

**HTTP Request Chi Tiết**

```
POST http://localhost:11434/api/generate

Body:
{
  "model": "llama3",
  "prompt": "<SYSTEM>....<CONTEXT>....",
  "stream": false
}

Response (200):
{
  "response": "Article là một bài viết chứa thông tin...",
  "model": "llama3",
  "created_at": "2024-10-29T10:30:00Z",
  "done": true,
  "context": [123, 456, 789, ...],  # Token IDs
  "total_duration": 4669359048600,  # ns
  "load_duration": 832090710,
  ...
}
```

**Xử Lý Lỗi**

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `Connection refused` | Ollama chưa chạy | `ollama serve` |
| `500 Internal Server Error` | Ollama crash hoặc model lỗi | Check logs, reload model |
| Timeout (>120s) | Prompt quá dài hoặc máy chậm | Giảm `top_k`, dùng model nhẹ |
| Missing "response" field | Response JSON sai định dạng | Kiểm tra version Ollama |

---

### BƯỚC 4: Orchestration (`src/rag_service.py`)

**Mục Tiêu**
- Nối 3 bước trên thành 1 hàm duy nhất.
- Đây là **giao diện công cộng** (public API) cho backend/frontend gọi.

**Hợp Đồng Hàm Chính**

```python
def rag_query(
    query: str,
    document_id: str,
    top_k: int = 5,
    system_prompt: str | None = None
) -> Dict[str, Any]:
    """
    Input:
      - query: "Introduce about the article"
      - document_id: "01287d1b-ca04-4c8e-9ec7-5126a606cc37"
      - top_k: 5
      - system_prompt: None
    
    Output:
      {
        "answer": "Article là một bài viết chứa...",
        "sources": [
          {
            "content": "Article là...",
            "chunk_index": 3,
            "page_number": 1,
            "similarity": 0.87
          },
          {
            "content": "Bài viết này...",
            "chunk_index": 5,
            "page_number": 2,
            "similarity": 0.82
          },
          ...
        ],
        "metadata": {
          "model": "llama3",
          "query_time_ms": 12345.67,
          "chunk_count": 5
        },
        "prompt": "<SYSTEM>....<CONTEXT>....<QUESTION>...",  # Debug
        "raw_llm_response": {...}  # Debug
      }
    
    Raise:
      - Bất kỳ lỗi từ retriever, prompt_builder, llm_client
      - (Không nuốt lỗi, để caller xử lý)
    """
```

**Luồng Tổng Hợp**

```
START
  ↓
1. retrieve_similar_chunks(query, document_id, top_k)
   → chunks: List[RetrievedChunk]
  ↓
2. build_rag_prompt(query, chunks, system_prompt)
   → prompt: str
  ↓
3. generate_answer(prompt)
   → llm_response: LLMResponse
  ↓
4. Format output
   - answer: llm_response.answer
   - sources: convert chunks → dict list
   - metadata: {model, query_time_ms, chunk_count}
   - prompt: để debug
  ↓
5. Return dict
END
```

**Tính Toán Thời Gian**

```python
from time import perf_counter

start = perf_counter()
# ... tất cả 3 hàm gọi ...
elapsed_ms = (perf_counter() - start) * 1000
# elapsed_ms = ~12500 ms = 12.5 giây (tuỳ độ phức tạp)
```

---

## 🔄 Luồng End-to-End (Level 1: Tổng Quát)

```
USER INPUT
"Introduce about the article"
        ↓
╔═══════════════════════════════════════╗
║   rag_service.rag_query()             ║
║   ═══════════════════════             ║
║  1. retriever.retrieve_similar_chunks ║
║  2. prompt_builder.build_rag_prompt   ║
║  3. llm_client.generate_answer        ║
╚═══════════════════════════════════════╝
        ↓
RESPONSE {
  answer: "...",
  sources: [...],
  metadata: {...}
}
```

---

## 🔄 Luồng End-to-End (Level 2: Chi Tiết)

```
1. RETRIEVAL
   query_vector = embed("Introduce about the article")
   chunks = Supabase.select("document_embeddings")
   scores = [cosine_sim(query_vector, chunk.embedding) for chunk in chunks]
   top_5_chunks = sort(chunks by scores)[0:5]
   
2. PROMPT BUILDING
   prompt = f"""
   {SYSTEM_PROMPT}
   
   Context:
   {Đoạn 1 | Trang 1 | Score: 0.87}
   {chunk_1_content}
   ...
   
   Question: Introduce about the article
   """
   
3. LLM CALL
   response = ollama.post("/api/generate", {
     model: "llama3",
     prompt: prompt,
     stream: false
   })
   answer = response["response"]
   
4. FORMAT OUTPUT
   return {
     answer: answer,
     sources: [
       {content, chunk_index, page_number, similarity},
       ...
     ],
     metadata: {model, query_time_ms, chunk_count}
   }
```

---

## 📊 Data Flow Diagram (Level 3: Transformer)

```
Input Query String
"Introduce about the article"
        ↓
┌─────────────────────────┐
│ SentenceTransformer     │
│ encode()                │
└─────────────────────────┘
        ↓
Query Vector (768-dim)
[0.1, 0.2, 0.3, ..., 0.4]
        ↓
┌─────────────────────────┐
│ Supabase pgvector       │
│ document_embeddings     │
│ (fetch by document_id)  │
└─────────────────────────┘
        ↓
All Chunk Vectors
[
  {content: "...", embedding: [...]},
  {content: "...", embedding: [...]},
  ...
]
        ↓
┌─────────────────────────┐
│ Cosine Similarity       │
│ Compute & Sort          │
└─────────────────────────┘
        ↓
Top-K Chunks (Ranked by Score)
[
  RetrievedChunk(content="...", similarity=0.87),
  RetrievedChunk(content="...", similarity=0.82),
  ...
]
        ↓
┌─────────────────────────┐
│ Prompt Builder          │
│ Format + Concatenate    │
└─────────────────────────┘
        ↓
Prompt String (1000+ chars)
"<SYSTEM>...<CONTEXT>...<QUESTION>..."
        ↓
┌─────────────────────────┐
│ Ollama HTTP POST        │
│ /api/generate           │
└─────────────────────────┘
        ↓
LLM Response JSON
{
  response: "Article là một bài viết...",
  model: "llama3",
  ...
}
        ↓
┌─────────────────────────┐
│ Format Output           │
│ Extract + Structure     │
└─────────────────────────┘
        ↓
Final Dict Output
{
  answer: "Article là...",
  sources: [...],
  metadata: {...}
}
```

---

## 🏗️ Kiến Trúc File (Level 4: Components)

```
config.py
├─ Settings dataclass
│  ├─ supabase_url, supabase_service_key
│  ├─ ollama_url, ollama_model
│  └─ chunk_size, chunk_overlap, hf_model_name
└─ settings: Settings (singleton)

supabase_client.py
├─ get_supabase_client() → Client
├─ fetch_document_metadata()
├─ download_file()
└─ insert_embeddings()

embedder.py
├─ _get_model() → SentenceTransformer (singleton)
└─ embed_chunks() → List[EmbeddingResult]

retriever.py
├─ retrieve_similar_chunks()
│  ├─ Embed query (SentenceTransformer)
│  ├─ Fetch chunks from Supabase
│  ├─ Compute cosine similarity
│  └─ Return top_k
├─ RetrievedChunk dataclass
│  ├─ content: str
│  ├─ chunk_index: int
│  ├─ page_number: int | None
│  └─ similarity: float
└─ _cosine_similarity() helper

prompt_builder.py
├─ build_rag_prompt()
│  ├─ Format system prompt
│  ├─ Format context (chunks)
│  └─ Append question
└─ _DEFAULT_SYSTEM_PROMPT constant

llm_client.py
├─ generate_answer()
│  ├─ POST to Ollama /api/generate
│  ├─ Handle errors
│  └─ Parse response
├─ LLMResponse dataclass
│  ├─ answer: str
│  ├─ model: str
│  └─ raw: dict
└─ LLMClientError exception

rag_service.py
├─ rag_query() ← **MAIN PUBLIC API**
│  ├─ Call retriever
│  ├─ Call prompt_builder
│  ├─ Call llm_client
│  ├─ Measure time
│  └─ Format & return
└─ _serialize_chunk() helper

scripts/rag_query.py
├─ parse_args()
│  ├─ --query (required)
│  ├─ --document-id (required)
│  ├─ --top-k (default 5)
│  ├─ --show-prompt
│  └─ --pretty
└─ main()
   ├─ Call rag_service.rag_query()
   └─ Pretty print result
```

---

## 🎯 Bảng Tóm Tắt: Hợp Đồng I/O

| Module | Input | Output | Lỗi |
|--------|-------|--------|-----|
| **retriever.py** | query: str, document_id: str, top_k: int | List[RetrievedChunk] | ValueError (empty), None (no data) |
| **prompt_builder.py** | query: str, chunks: Sequence[RetrievedChunk], system_prompt?: str | str (prompt) | ValueError (empty query) |
| **llm_client.py** | prompt: str, model?: str, timeout: int | LLMResponse | LLMClientError (connection, response) |
| **rag_service.py** | query: str, document_id: str, top_k: int, system_prompt?: str | Dict (answer, sources, metadata) | Any error from 3 modules |

---

## 💡 Ví Dụ Chạy Thử

### Scenario: Hỏi về một tài liệu
```bash
python scripts/rag_query.py \
  --query "Introduce about the article" \
  --document-id 01287d1b-ca04-4c8e-9ec7-5126a606cc37 \
  --top-k 5 \
  --show-prompt
```

### Output mong đợi
```
=== ANSWER ===
Article là một bài viết chứa thông tin về...

=== PROMPT GỬI LÊN LLM ===
Bạn là trợ lý AI hỗ trợ trả lời câu hỏi dựa trên các đoạn văn bản cung cấp...
[... prompt dài ...]

=== CONTEXT SỬ DỤNG ===
[1] Chunk 3 | Trang 1 | Score 0.8700
Article là một dạng tài liệu...
-
[2] Chunk 5 | Trang 2 | Score 0.8200
Bài viết này nói về...
-
...

=== METADATA ===
model: llama3
query_time_ms: 12345.67
chunk_count: 5
```

---

## 🔍 Gỡ Lỗi Nhanh

| Vấn Đề | Nguyên nhân | Cách Fix |
|--------|-------------|---------|
| `ModuleNotFoundError: No module named 'src'` | Script chạy từ sai thư mục | Đã sửa ở rag_query.py: thêm sys.path |
| `No similar chunks found` (sources = []) | Document không có embeddings | Kiểm tra document đã ingest chưa |
| LLM trả lời không liên quan | top_k quá thấp hoặc prompt không rõ | Tăng top_k hoặc sửa system_prompt |
| Ollama timeout | Server chậm hoặc model nặng | Dùng model nhẹ hơn (mistral, phi) |
| Embedding mismatch | Model embedding khác lúc ingest | Bảo đảm config HF_MODEL_NAME giống |

---

## 🎓 Key Takeaways

1. **RAG = 3 bước tuần tự**: Retrieval → Prompt Building → LLM Generation.
2. **Retriever dùng embedding similarity** (cosine): vector space matching.
3. **Prompt Builder định hình output**: system instruction giới hạn LLM, context cung cấp kiến thức.
4. **LLM Client là wrapper HTTP**: gọi Ollama local `/api/generate`.
5. **RAG Service là công cộng API**: backend/frontend chỉ cần gọi hàm này.
6. **Thời gian xử lý**: phần lớn ở step 1 (embedding) + step 3 (LLM generation).

---

## 📚 Đọc Thêm
- Cosine Similarity: https://en.wikipedia.org/wiki/Cosine_similarity
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Sentence Transformers: https://www.sbert.net/

