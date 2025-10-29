# 🚀 ROADMAP: Từ Embedding Pipeline Sang RAG System

## 📌 Tình Hình Hiện Tại

✅ **Bạn đã có:**
1. Embedding pipeline (6 modules)
2. PDF được chia thành chunks
3. Embedding vectors lưu ở Supabase pgvector

❌ **Còn thiếu để có RAG:**
1. Similarity search (tìm chunks tương tự)
2. Prompt template (xây dựng question từ chunks)
3. LLM call (gọi model AI để trả lời)
4. Backend API endpoint (kết nối frontend)

---

## 🎯 3 Bước Để Có RAG

### **BƯỚC 1: Similarity Search (Retriever)**

**Mục đích:** Khi user hỏi câu hỏi → tìm chunks liên quan từ DB

**Cách thực hiện:**

1. Embed câu hỏi thành vector (768 chiều)
2. Query Supabase: tìm embeddings gần nhất (cosine similarity)
3. Return top-k chunks liên quan

**Code:**

```python
# src/retriever.py (file mới)

import numpy as np
from .embedder import _get_model
from .supabase_client import get_supabase_client

def retrieve_similar_chunks(query: str, document_id: str, top_k: int = 5) -> list[dict]:
    """
    Embed câu hỏi → tìm chunks tương tự từ Supabase
    """
    # Bước 1: Embed query
    model = _get_model()
    query_embedding = model.encode(query)  # [0.1, 0.2, ..., 0.3] (768 chiều)
    
    # Bước 2: Query Supabase (similarity search)
    client = get_supabase_client()
    
    # Dùng pgvector similarity operator (<->)
    # Similar documents có distance nhỏ hơn = more similar
    response = client.rpc(
        'search_embeddings',  # Function stored procedure
        {
            'query_embedding': query_embedding.tolist(),  # Convert to list
            'document_id': document_id,
            'similarity_threshold': 0.5,
            'limit': top_k
        }
    ).execute()
    
    return response.data  # List of chunks: [chunk1, chunk2, ...]
```

**SQL Function (tạo ở Supabase):**

```sql
CREATE OR REPLACE FUNCTION search_embeddings(
    query_embedding vector(768),
    document_id text,
    similarity_threshold float DEFAULT 0.5,
    limit int DEFAULT 5
)
RETURNS TABLE (
    chunk_index int,
    content text,
    page_number int,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.chunk_index,
        de.content,
        de.page_number,
        1 - (de.embedding <=> query_embedding) as similarity
    FROM document_embeddings de
    WHERE de.document_id = search_embeddings.document_id
    AND 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT limit;
END;
$$ LANGUAGE plpgsql;
```

**Giải thích:**
- `<=>` operator: pgvector distance (L2 norm)
- `1 - distance` = similarity (0-1)
- `ORDER BY distance`: sắp xếp gần nhất trước

---

### **BƯỚC 2: Prompt Engineering (Context Builder)**

**Mục đích:** Ghép chunks vào prompt để LLM hiểu context

**Code:**

```python
# src/prompt_builder.py (file mới)

def build_rag_prompt(query: str, context_chunks: list[dict], system_prompt: str = None) -> str:
    """
    Xây dựng prompt đầy đủ cho LLM
    """
    
    if system_prompt is None:
        system_prompt = """Bạn là một trợ lý AI thông minh.
Sử dụng thông tin cung cấp dưới để trả lời câu hỏi.
Nếu thông tin không đủ, hãy nói rõ.
"""
    
    # Ghép context chunks
    context_text = "\n\n".join([
        f"[Trang {chunk['page_number']}, Chunk {chunk['chunk_index']}]\n{chunk['content']}"
        for chunk in context_chunks
    ])
    
    # Xây dựng prompt
    prompt = f"""{system_prompt}

---CONTEXT---
{context_text}

---QUESTION---
{query}

---ANSWER---
"""
    
    return prompt

# Ví dụ sử dụng
query = "LangChain là gì?"
context_chunks = [
    {"page_number": 1, "chunk_index": 1, "content": "LangChain là framework..."},
    {"page_number": 1, "chunk_index": 2, "content": "Nó cung cấp công cụ..."},
]
prompt = build_rag_prompt(query, context_chunks)
print(prompt)
```

---

### **BƯỚC 3: LLM Integration (Response Generator)**

**Mục đích:** Gọi LLM (OpenAI, Ollama, etc.) để tạo response

**Lựa Chọn LLM:**

#### **Option A: OpenAI API (Dễ, Nhanh)**

```python
# src/llm_client.py

from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.openai_api_key)

def generate_answer(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
    """
    Gọi OpenAI API để generate answer
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=500
    )
    
    return response.choices[0].message.content
```

**Setup:**
```bash
pip install openai
# .env thêm:
OPENAI_API_KEY=sk-...
```

---

#### **Option B: Ollama (Local, Free, Privacy)**

```python
# src/llm_client.py

import requests
from .config import settings

def generate_answer(prompt: str, model: str = "llama2", temperature: float = 0.7) -> str:
    """
    Gọi Ollama local API
    """
    response = requests.post(
        f"{settings.ollama_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature
        }
    )
    
    result = response.json()
    return result['response']
```

**Setup (macOS/Linux):**
```bash
# Cài Ollama
brew install ollama

# Pull model (lần đầu mất ~5-10 phút)
ollama pull llama2

# Chạy Ollama server
ollama serve
# Server chạy ở http://localhost:11434

# .env thêm:
OLLAMA_URL=http://localhost:11434
```

**So sánh:**

| Tiêu Chí | OpenAI | Ollama |
|----------|--------|--------|
| **Chi phí** | $ (pay per request) | Free |
| **Speed** | 1-2s | 10-20s (tùy hardware) |
| **Quality** | Tốt nhất | Tốt |
| **Privacy** | Data gửi tới OpenAI | Local (private) |
| **Setup** | API key | Docker/Binary |

---

## 🎬 Flow RAG Hoàn Chỉnh

```
User Question
    ↓
[retriever.py]
  1. Embed query
  2. Search Supabase
  3. Get top-k chunks
    ↓
[prompt_builder.py]
  1. Format context
  2. Build prompt
    ↓
[llm_client.py]
  1. Call LLM API
  2. Get response
    ↓
Response to User
```

---

## 📋 Todo List: Xây Dựng RAG

### **Phase 1: Core RAG (1-2 ngày)**

- [ ] **Step 1.1:** Tạo `src/retriever.py`
  - Hàm `retrieve_similar_chunks(query, doc_id, top_k)`
  - Embed query bằng SentenceTransformer
  - Query Supabase pgvector similarity

- [ ] **Step 1.2:** Tạo SQL function ở Supabase
  - `search_embeddings()` stored procedure
  - Test với query từ Python

- [ ] **Step 1.3:** Tạo `src/prompt_builder.py`
  - Hàm `build_rag_prompt(query, chunks)`
  - Format context chunks đúng

- [ ] **Step 1.4:** Tạo `src/llm_client.py`
  - Hàm `generate_answer(prompt)`
  - Chọn OpenAI hoặc Ollama

- [ ] **Step 1.5:** Test end-to-end
  - Python script: query → retrieve → generate → print

### **Phase 2: Backend API (1-2 ngày)**

- [ ] **Step 2.1:** Tạo endpoint `/api/rag/chat`
  - Method: POST
  - Body: `{ query: "...", document_id: "..." }`
  - Response: `{ answer: "...", sources: [...] }`

- [ ] **Step 2.2:** Add tracing/logging
  - Log query → retrieved chunks → generated answer

- [ ] **Step 2.3:** Add error handling
  - No chunks found
  - LLM timeout
  - Invalid document_id

### **Phase 3: Frontend Integration (1 ngày)**

- [ ] **Step 3.1:** Tạo UI component `<ChatInterface />`
  - Input field (query)
  - Display answer
  - Show sources (retrieved chunks)

- [ ] **Step 3.2:** Wire up API call
  - Fetch POST `/api/rag/chat`
  - Handle loading/error states

---

## 🔧 Recommended Tech Stack

**For RAG System:**

```
Backend:
├─ Python (Flask/FastAPI) - API server
├─ SentenceTransformer - Query embedding
├─ Supabase pgvector - Vector DB
├─ OpenAI / Ollama - LLM
└─ LangChain (optional) - Orchestration

Frontend:
├─ React - UI
├─ TailwindCSS - Styling
├─ React Query - API calls
└─ Markdown renderer - Display formatted answers
```

---

## 📝 File Structure (Sau khi thêm RAG)

```
Embedding_langchain/
├─ src/
│  ├─ __init__.py
│  ├─ config.py              ✅ Có
│  ├─ text_extractor.py      ✅ Có
│  ├─ chunker.py             ✅ Có
│  ├─ embedder.py            ✅ Có
│  ├─ supabase_client.py     ✅ Có
│  ├─ pipeline.py            ✅ Có
│  ├─ retriever.py           🆕 Tạo (retrieve chunks)
│  ├─ prompt_builder.py      🆕 Tạo (build prompt)
│  ├─ llm_client.py          🆕 Tạo (call LLM)
│  └─ rag_pipeline.py        🆕 Tạo (end-to-end)
├─ scripts/
│  ├─ ingest_document.py     ✅ Có
│  └─ test_rag.py            🆕 Tạo (test RAG)
└─ requirements.txt          📝 Update
```

---

## 🚀 Quick Start (Nếu Chọn Ollama)

```bash
# 1. Cài Ollama
brew install ollama  # macOS
# hoặc download từ ollama.ai

# 2. Pull model
ollama pull llama2

# 3. Chạy Ollama server (background)
ollama serve

# 4. Cập nhật requirements.txt
pip install requests  # Cho Ollama API call

# 5. Tạo retriever.py
# (giải thích ở BƯỚC 1 ở trên)

# 6. Test
python -c "
from src.retriever import retrieve_similar_chunks
chunks = retrieve_similar_chunks('LangChain là gì?', 'doc123')
print(chunks)
"
```

---

## 💡 Workflow Recommend

### **Nếu Muốn Nhanh:**
1. ✅ Dùng Ollama (local, free, privacy)
2. ✅ Implement retriever.py (similarity search)
3. ✅ Implement prompt_builder.py (format context)
4. ✅ Implement llm_client.py (Ollama API call)
5. ✅ Test ở Python trước (không cần frontend)

### **Nếu Muốn Production-Ready:**
1. ✅ Dùng OpenAI (stable, high quality)
2. ✅ Implement retriever.py
3. ✅ Implement prompt_builder.py
4. ✅ Implement llm_client.py
5. ✅ Tạo Express API endpoint
6. ✅ Add caching (Redis)
7. ✅ Add monitoring (logs, metrics)
8. ✅ Wire up frontend

---

## ❓ Câu Hỏi Thường Gặp

### **Q: Khi nào nên dùng OpenAI vs Ollama?**

**Dùng OpenAI nếu:**
- Muốn quality cao nhất
- Dự án commercial
- Có budget
- Không quan tâm data privacy

**Dùng Ollama nếu:**
- Muốn free + private
- Development/learning
- Có GPU mạnh (RTX 4090, etc.)
- Chấp nhận quality thấp hơn

### **Q: Bao lâu mới có RAG?**

- **Minimal RAG** (Python only): 2-3 giờ
- **Full RAG with API**: 1 ngày
- **Production-ready**: 2-3 ngày (+ testing, monitoring)

### **Q: Cần GPU không?**

**Cho retrieval:** Không (CPU đủ)
**Cho local LLM (Ollama):** Có GPU tốt hơn nhiều
  - Ollama có hỗ trợ GPU (CUDA, Metal)
  - CPU mode chạy được nhưng chậm

### **Q: Embeddings 768 chiều là bao nhiêu "thông tin"?**

- 768-dim vector ≈ "semantic fingerprint" của text
- Dùng để đo độ tương tự (cosine similarity)
- Không phải "compression" - thông tin không mất

---

## 🎯 Next Steps (Cụ Thể)

**Bạn muốn:**

1. **[A] Minimal RAG demo** (chạy local Python)
   → Cần: retriever.py + prompt_builder.py + Ollama
   → Time: 2-3 giờ
   
2. **[B] Backend API** (Express endpoint)
   → Cần: thêm llm_client.py + Express POST endpoint
   → Time: 1 ngày
   
3. **[C] Full UI** (chatbot interface)
   → Cần: React component + styling + error handling
   → Time: 1-2 ngày

**Bạn chọn hướng nào?** Tôi sẽ implement chi tiết! 🚀

---

## 📚 Resources

**Docs:**
- SentenceTransformer: https://www.sbert.net/
- Supabase pgvector: https://supabase.com/docs/guides/database/extensions/pgvector
- Ollama: https://ollama.ai/
- OpenAI: https://platform.openai.com/docs/

**Examples:**
- LangChain RAG: https://github.com/langchain-ai/langchain/tree/master/templates/rag
- pgvector examples: https://github.com/pgvector/pgvector/tree/master/examples

**Best Practices:**
- Chunk size: 800-1000 tokens (bạn đã tối ưu 900)
- Similarity threshold: 0.5-0.7 (tuỳ use case)
- Top-k: 3-5 chunks (balance quality & latency)
- Temperature: 0.5-0.7 (creativity vs consistency)
