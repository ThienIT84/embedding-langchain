# 📚 HƯỚNG DẪN ĐỌC CODE - RAG PIPELINE

**Mục đích:** Hiểu rõ quy trình RAG từ đầu đến cuối  
**Thời gian:** 30-45 phút  
**Độ khó:** ⭐⭐⭐ (Trung bình)

---

## 🎯 TÓM TẮT QUY TRÌNH RAG

```
📄 PDF Document
    ↓ [1. TEXT EXTRACTION]
📝 Raw Text
    ↓ [2. CHUNKING]
📦 Text Chunks (900 chars/chunk)
    ↓ [3. EMBEDDING]
🔢 Vector Embeddings (768-dim)
    ↓ [4. STORAGE]
💾 Supabase pgvector
    ↓ [5. RETRIEVAL - User asks question]
❓ Query → Vector → Find Similar Chunks
    ↓ [6. PROMPT BUILDING]
📋 Context + Query → Prompt
    ↓ [7. LLM GENERATION]
🤖 Ollama llama3 → Answer
    ↓
✅ Final Answer + Sources
```

---

## 📖 CÁCH ĐỌC CODE - THEO THỨ TỰ

### **GIAI ĐOẠN 1: HIỂU CẤU HÌNH** (5 phút)

#### 🔹 File 1: `src/config.py`
**Đọc trước tiên!** - Nơi cấu hình tất cả settings

**Các setting quan trọng:**
- `chunk_size`: 900 chars - độ dài mỗi chunk
- `chunk_overlap`: 200 chars - overlap giữa các chunks
- `hf_model_name`: Model embedding (768-dim vectors)
- `ollama_model`: llama3 - LLM để sinh câu trả lời
- `supabase_url/key`: Database connection

**Kiến thức:**
- `@dataclass(frozen=True)` → Immutable settings
- `load_dotenv()` → Đọc từ `.env` file

---

### **GIAI ĐOẠN 2: INGESTION PIPELINE** (Nhồi tài liệu vào hệ thống)

#### 🔹 File 2: `src/text_extractor.py`
**Chức năng:** Đọc PDF → Raw text

**Đọc theo thứ tự:**
1. **Class `DocumentChunk`** (dòng 18-38)
   - `text`: Nội dung văn bản
   - `page_number`: Số trang
   - `source_file`: Tên file PDF
   - `__slots__` → Tối ưu bộ nhớ

2. **Function `clean_text()`** (dòng 41-63)
   - Loại bỏ null bytes (`\x00`)
   - Nối từ bị ngắt dòng: `"process-\ning"` → `"processing"`
   - Chuẩn hóa whitespace

3. **Function `extract_pdf_text()`** (dòng 66-107)
   - Dùng `PyPDF` để đọc PDF
   - Yield từng trang (streaming, tiết kiệm RAM)
   - Error handling: File not found, encrypted PDF

**Kiến thức:**
- `yield` vs `return` → Generaor pattern
- `__slots__`t → Memory optimization
- Regex `re.sub()` → Text cleaning

---

#### 🔹 File 3: `src/chunker.py`
**Chức năng:** Chia text dài → Chunks nhỏ (900 chars)

**Đọc theo thứ tự:**
1. **Class `TextChunk`** (dòng 14-32)
   - Kế thừa `DocumentChunk`
   - Thêm `chunk_index`: Số thứ tự chunk

2. **`_splitter`** (dòng 35-41)
   - `RecursiveCharacterTextSplitter` từ LangChain
   - `separators`: Ưu tiên tách theo `\n\n`, `\n`, space
   - `keep_separator=False` → Bỏ ký tự phân cách

3. **Function `split_chunks()`** (dòng 44-67)
   - Loop qua từng `DocumentChunk`
   - Split thành nhiều pieces
   - Yield từng `TextChunk` với `chunk_index` tăng dần

**Kiến thức:**
- LangChain `RecursiveCharacterTextSplitter`
- Streaming pattern với `yield`
- `global_chunk_index` → Counter tăng dần

**Tại sao chunk?*
- LLM có giới hạn context window
- Embedding models hoạt động tốt với text ngắn
- Tìm kiếm semantic chính xác hơn với chunks nhỏ

---

#### 🔹 File 4: `src/embedder.py`
**Chức năng:** Text chunks → Vector embeddings (768-dim)

**Đọc theo thứ tự:**
1. **Class `EmbeddingResult`** (dòng 14-19)
   - `chunk`: TextChunk gốc
   - `vector`: numpy array (768 chiều)

2. **Function `_get_model()`** (dòng 25-30)
   - Singleton pattern: Chỉ load model 1 lần
   - `SentenceTransformer` từ HuggingFace
   - Model: `paraphrase-multilingual-mpnet-base-v2`

3. **Function `embed_chunks()`** (dòng 33-42)
   - Input: List of TextChunk
   - `model.encode()` → Batch encoding
   - Output: List of EmbeddingResult (chunk + vector)

**Kiến thức:**
- Sentence Transformers → Dense vector representations
- 768 dimensions → Semantic meaning
- Batch processing → Efficient GPU usage
- Singleton pattern → Memory optimization

**Tại sao 768 chiều?**
- Model architecture (BERT-based)
- Balance giữa accuracy và performance
- Enough để capture semantic meaning

---

#### 🔹 File 5: `src/supabase_client.py`
**Chức năng:** Giao tiếp với Supabase (Database + Storage)

**Đọc theo thứ tự:**
1. **Function `get_supabase_client()`** (dòng 18-23)
   - Singleton pattern
   - Create Supabase client 1 lần

2. **Function `download_file()`** (dòng 26-32)
   - Download PDF từ Supabase Storage
   - Lưu vào local `tmp/` directory

3. **Function `fetch_document_metadata()`** (dòng 35-47)
   - Query bảng `documents`
   - Lấy metadata: title, file_path, category_id, etc.

4. **Function `insert_embeddings()`** (dòng 85-95)
   - Insert vectors vào bảng `document_embeddings`
   - **NEW:** Batch insert (100 rows/batch) để tránh timeout

**Kiến thức:**
- Supabase Python SDK
- PostgreSQL with pgvector extension
- Retry logic với `@retry_with_backoff`
- Error handling với `APIError`

---

#### 🔹 File 6: `src/pipeline.py`
**Chức năng:** ORCHESTRATOR - Kết hợp tất cả bước ingestion

**Đọc theo thứ tự:**
1. **Function `_load_document()`** (dòng 18-21)
   - Extract PDF → DocumentChunk
   - Split → TextChunk

2. **Function `_prepare_records()`** (dòng 24-39)
   - TextChunk + Vector → Database records
   - Format: `{document_id, content, page_number, chunk_index, embedding}`

3. **Function `process_document()`** (dòng 42-75)
   - **MAIN ORCHESTRATOR**
   - Flow:
     ```
     1. Fetch metadata từ DB
     2. Set status = "processing"
     3. Download PDF từ Storage
     4. Extract text → chunks
     5. Embed chunks → vectors
     6. Prepare records
     7. Delete old embeddings
     8. Insert new embeddings
     9. Set status = "completed"
     10. Cleanup: Delete temp file
     ```

**Kiến thức:**
- Try-except-finally pattern
- Status tracking: processing → completed/failed
- Resource cleanup trong `finally` block
- Error propagation

---

### **GIAI ĐOẠN 3: RETRIEVAL PIPELINE** (Truy vấn)

#### 🔹 File 7: `src/retriever.py`
**Chức năng:** Tìm chunks tương đồng với câu hỏi

**Đọc theo thứ tự:**
1. **Class `RetrievedChunk`** (dòng 13-18)
   - `content`: Text của chunk
   - `similarity`: Điểm tương đồng (0-1)
   - `chunk_index`, `page_number`: Metadata

2. **Function `_cosine_similarity()`** (dòng 21-28)
   - Tính độ tương đồng giữa 2 vectors
   - Formula: `dot(a,b) / (norm(a) * norm(b))`
   - Output: 0 (không giống) → 1 (giống hệt)

3. **Function `retrieve_similar_chunks()`** (dòng 31-90)
   - **CŨ:** Search trong 1 document cụ thể
   - Query DB → Get all chunks of document
   - Encode query → vector
   - Tính cosine similarity với từng chunk
   - Sort theo similarity giảm dần
   - Return top_k chunks

4. **Function `retrieve_similar_chunks_by_user()`** (dòng 93-161)
   - **MỚI - PHASE C1:** Search trong TẤT CẢ documents của user
   - Encode query → vector
   - Call Supabase RPC `match_embeddings_by_user`
   - RPC function:
     - JOIN `document_embeddings` với `documents`
     - Filter theo `created_by = user_id`
     - Tính cosine similarity bằng pgvector
     - Sort + Limit top_k

**Kiến thức:**
- Cosine similarity → Semantic search
- Vector search với pgvector
- RPC (Remote Procedure Call) trong Supabase
- Numpy operations

**Tại sao cosine similarity?**
- Measure semantic similarity
- Không phụ thuộc vào độ dài vector
- Fast computation

---

#### 🔹 File 8: `src/prompt_builder.py`
**Chức năng:** Xây dựng prompt cho LLM

**Đọc theo thứ tự:**
1. **`_DEFAULT_SYSTEM_PROMPT`** (dòng 7-11)
   - Hướng dẫn LLM cách trả lời
   - Chỉ dùng thông tin trong Context
   - Trả lời bằng tiếng Việt

2. **Function `build_rag_prompt()`** (dòng 14-45)
   - Input: query + list of chunks + (optional) system_prompt
   - Format chunks thành context:
     ```
     Đoạn 1 | Trang 5 | Score: 0.9500
     [Content của chunk 1]
     
     Đoạn 2 | Trang 6 | Score: 0.8500
     [Content của chunk 2]
     ```
   - Final prompt:
     ```
     [System Prompt]
     
     Context:
     [Formatted chunks]
     
     Câu hỏi: [User query]
     Hãy cung cấp câu trả lời ngắn gọn...
     ```

**Kiến thức:**
- Prompt engineering
- Context injection
- Template pattern

**Tại sao cần System Prompt?**
- Hướng dẫn behavior của LLM
- Giảm hallucination
- Định dạng output

---

#### 🔹 File 9: `src/llm_client.py`
**Chức năng:** Gọi Ollama LLM để sinh câu trả lời

**Đọc theo thứ tự:**
1. **Class `LLMResponse`** (dòng 14-19)
   - `answer`: Câu trả lời từ LLM
   - `model`: Tên model (llama3)
   - `raw`: Full response JSON

2. **Function `generate_answer()`** (dòng 28-60)
   - **NEW:** Có `@retry_with_backoff` decorator
   - POST request → `http://localhost:11434/api/generate`
   - Payload: `{model, prompt, stream: false}`
   - Parse response → Extract answer
   - Error handling: Connection error, HTTP error, Invalid response

**Kiến thức:**
- Ollama API
- HTTP requests với `requests` library
- Retry logic với exponential backoff
- Error handling với custom exceptions

**Tại sao Ollama?**
- Local LLM → Privacy
- No API costs
- Offline capable
- llama3 → Good Vietnamese support

---

#### 🔹 File 10: `src/rag_service.py` ⭐ **MAIN ORCHESTRATOR**
**Chức năng:** Kết hợp retrieval + prompt + LLM

**Đọc theo thứ tự:**
1. **Function `_serialize_chunk()`** (dòng 13-20)
   - Convert `RetrievedChunk` → JSON-friendly dict

2. **Function `rag_query()`** (dòng 23-97) ⭐⭐⭐
   - **MAIN RAG WORKFLOW**
   - **NEW:** Input validation với Pydantic
   
   **Flow:**
   ```python
   # 1. VALIDATION
   validated = RAGQueryRequest(query, user_id, top_k, system_prompt)
   
   # 2. RETRIEVAL
   chunks = retrieve_similar_chunks_by_user(
       query=validated.query,
       user_id=validated.user_id,
       top_k=validated.top_k
   )
   
   # 3. PROMPT BUILDING
   prompt = build_rag_prompt(
       query=validated.query,
       chunks=chunks,
       system_prompt=validated.system_prompt
   )
   
   # 4. LLM GENERATION
   llm_response = generate_answer(prompt)
   
   # 5. RETURN RESPONSE
   return {
       "answer": llm_response.answer,
       "sources": [serialized chunks],
       "metadata": {model, query_time_ms, chunk_count},
       "prompt": full_prompt,
       "raw_llm_response": raw_data
   }
   ```

**Kiến thức:**
- Orchestration pattern
- Performance tracking với `perf_counter()`
- Input validation với Pydantic
- Comprehensive error handling

---

### **GIAI ĐOẠN 4: HELPERS & UTILITIES**

#### 🔹 File 11: `src/validators.py`
**Chức năng:** Input validation với Pydantic

**Đọc các classes:**
1. **`RAGQueryRequest`** (dòng 6-37)
   - Validate query (min 1, max 2000 chars)
   - Validate user_id (phải là UUID)
   - Validate top_k (1-20)
   - Auto strip whitespace

2. **`DocumentIngestRequest`** (dòng 40-53)
   - Validate document_id (UUID)
   - Force refresh flag

3. **`ChunkConfig`** (dòng 56-72)
   - Validate chunk_size (100-2000)
   - Validate chunk_overlap < chunk_size

**Kiến thức:**
- Pydantic v2 validation
- `@field_validator` decorator
- Cross-field validation
- UUID validation

---

#### 🔹 File 12: `src/retry_utils.py`
**Chức năng:** Retry logic với exponential backoff

**Đọc theo thứ tự:**
1. **Function `retry_with_backoff()`** (dòng 11-68)
   - Decorator pattern
   - Retry logic: 1s → 2s → 4s → 8s
   - Configurable: max_retries, exceptions

2. **Class `CircuitBreaker`** (dòng 71-144)
   - States: CLOSED → OPEN → HALF_OPEN
   - Prevent cascading failures
   - Timeout-based recovery

**Kiến thức:**
- Decorator pattern
- Exponential backoff
- Circuit breaker pattern
- Resilience engineering

---

## 🎯 ĐỌC THEO USECASE

### **USECASE 1: User upload PDF → Embedding**
Đọc theo thứ tự:
1. `scripts/ingest_document.py` (entry point)
2. `src/pipeline.py` → `process_document()`
3. `src/text_extractor.py` → `extract_pdf_text()`
4. `src/chunker.py` → `split_chunks()`
5. `src/embedder.py` → `embed_chunks()`
6. `src/supabase_client.py` → `insert_embeddings()`

---

### **USECASE 2: User hỏi câu hỏi → Nhận answer**
Đọc theo thứ tự:
1. `scripts/rag_runner.py` (entry point từ Node.js)
2. `src/rag_service.py` → `rag_query()` ⭐
3. `src/validators.py` → Validate input
4. `src/retriever.py` → `retrieve_similar_chunks_by_user()`
5. `src/prompt_builder.py` → `build_rag_prompt()`
6. `src/llm_client.py` → `generate_answer()`

---

## 📊 KIẾN THỨC CẦN NẮM

### **Python Concepts**
- ✅ Generators (`yield`)
- ✅ Decorators (`@retry_with_backoff`)
- ✅ Type hints (Python 3.10+)
- ✅ Dataclasses
- ✅ Context managers (try-finally)
- ✅ Singleton pattern

### **ML/AI Concepts**
- ✅ Text embeddings (Dense vectors)
- ✅ Semantic similarity (Cosine)
- ✅ Chunking strategies
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ Prompt engineering

### **Libraries**
- ✅ LangChain (RecursiveCharacterTextSplitter)
- ✅ Sentence Transformers (Embeddings)
- ✅ Supabase Python SDK
- ✅ Pydantic (Validation)
- ✅ NumPy (Vector operations)
- ✅ PyPDF (PDF parsing)

---

## 🚀 QUICK START - ĐỌC NHANH (15 phút)

Nếu chỉ có 15 phút, đọc 5 files này theo thứ tự:

1. **`src/config.py`** - Settings
2. **`src/pipeline.py`** - Ingestion flow
3. **`src/rag_service.py`** - Query flow ⭐
4. **`src/retriever.py`** - Semantic search
5. **`src/llm_client.py`** - LLM generation

---

## 🎓 TIPS ĐỌC CODE HIỆU QUẢ

### ✅ **DO:**
- Đọc theo flow (không nhảy lung tung)
- Chú ý comments tiếng Việt
- Vẽ diagram flow trên giấy
- Chạy tests để hiểu behavior
- Debug step-by-step

### ❌ **DON'T:**
- Đọc từ đầu đến cuối từng file
- Bỏ qua docstrings
- Đọc không theo usecase
- Cố nhớ tất cả details

---

## 🔍 DEBUG & EXPERIMENT

### Chạy thử từng bước

```python
# 1. Test text extraction
from src.text_extractor import extract_pdf_text
chunks = list(extract_pdf_text(Path("test.pdf")))
print(chunks[0].text)

# 2. Test chunking
from src.chunker import split_chunks
text_chunks = list(split_chunks(chunks))
print(f"Total chunks: {len(text_chunks)}")

# 3. Test embedding
from src.embedder import embed_chunks
embeddings = embed_chunks(text_chunks[:5])  # Embed 5 chunks
print(embeddings[0].vector.shape)  # (768,)

# 4. Test retrieval
from src.retriever import retrieve_similar_chunks_by_user
results = retrieve_similar_chunks_by_user(
    query="What is Python?",
    user_id="user-uuid",
    top_k=3
)
print(results[0].content)

# 5. Test RAG query
from src.rag_service import rag_query
response = rag_query(
    query="Explain OOP",
    user_id="user-uuid",
    top_k=5
)
print(response["answer"])
```

---

## 📚 TÀI LIỆU THAM KHẢO

- **LangChain:** https://python.langchain.com/docs/modules/data_connection/document_transformers/
- **Sentence Transformers:** https://www.sbert.net/
- **Supabase Python:** https://supabase.com/docs/reference/python/
- **Pydantic:** https://docs.pydantic.dev/
- **Ollama:** https://ollama.ai/

---

## ✨ TÓM TẮT

### **Ingestion Pipeline:**
```
PDF → Text → Chunks → Embeddings → Database
```

### **Query Pipeline:**
```
Question → Vector → Search Similar → Build Prompt → LLM → Answer
```

### **Core Concepts:**
- 📦 Chunking: 900 chars, overlap 200
- 🔢 Embeddings: 768-dim vectors
- 🔍 Search: Cosine similarity
- 🤖 LLM: Ollama llama3
- 💾 Storage: Supabase pgvector

---

**Happy Learning! 🎉**

Bắt đầu từ `src/config.py` → `src/pipeline.py` → `src/rag_service.py`
