# Phase A - Giải Thích Chi Tiết (Python RAG Core)

Phase A là lõi chính của hệ thống RAG (Retrieval-Augmented Generation). Đây là phần xử lý dữ liệu và trả lời câu hỏi bằng LLM có tham khảo tài liệu.

---

## 🏗️ Kiến Trúc Phase A

```
Embedding_langchain/
├── src/                    # Code lõi
│   ├── config.py          # Đọc biến môi trường
│   ├── supabase_client.py # Kết nối Supabase
│   ├── text_extractor.py  # Trích xuất text từ PDF
│   ├── chunker.py         # Chia nhỏ text thành chunks
│   ├── embedder.py        # Chuyển chunks → vector (embedding)
│   ├── pipeline.py        # Điều phối: extract → chunk → embed → lưu DB
│   ├── retriever.py       # Tìm chunks liên quan tới câu hỏi
│   ├── prompt_builder.py  # Xây dựng prompt cho LLM
│   ├── llm_client.py      # Gọi Ollama để trả lời
│   └── rag_service.py     # Điều phối toàn bộ: retrieval → prompt → LLM
└── scripts/
    ├── ingest_document.py # CLI: upload PDF → embedding → DB
    ├── rag_query.py       # CLI: test RAG (hỏi câu hỏi)
    └── rag_runner.py      # Wrapper cho Node backend (nhận JSON stdin → trả JSON stdout)
```

---

## 📋 Quy Trình 2 Bước

### **Bước 1: INGEST (Nhập tài liệu)**

Chạy lần **1 lần duy nhất** cho mỗi PDF:

```bash
python scripts/ingest_document.py "path/to/file.pdf" "Tiêu đề tài liệu"
```

**Khi chạy lệnh này xảy ra gì?**

1. **Extract** (text_extractor.py)
   - Đọc PDF, trích xuất text từ từng trang
   - Kết quả: danh sách text

2. **Chunk** (chunker.py)
   - Chia text thành các đoạn nhỏ (~900 ký tự, overlap 200 ký tự)
   - Lý do: model embedding có giới hạn độ dài (512 tokens)
   - Kết quả: danh sách chunk

3. **Embed** (embedder.py)
   - Dùng mô hình `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
   - Chuyển mỗi chunk → vector 768 chiều (danh sách số thực)
   - Kết quả: danh sách vector

4. **Lưu DB** (supabase_client.py)
   - Lưu vào bảng `document_embeddings` trong Supabase
   - Cột `embedding` dùng kiểu **pgvector** (vector database)
   - Tạo index IVFFlat để tìm kiếm nhanh (similarity search)

**Ví dụ:**
```
PDF: "KNN_Algorithm.pdf"
  ↓ Extract
Text: "K-Nearest Neighbors (KNN) là một thuật toán..."
  ↓ Chunk (chia 900 ký tự)
Chunks: [
  "K-Nearest Neighbors (KNN) là một thuật toán...",
  "Ưu điểm của KNN: 1. Đơn giản 2. Không yêu cầu training...",
  ...
]
  ↓ Embed (mô hình multilingual)
Vectors: [
  [0.123, -0.456, 0.789, ..., 0.234],  # chunk 0 → 768 số
  [0.111, -0.222, 0.333, ..., 0.444],  # chunk 1 → 768 số
  ...
]
  ↓ Lưu Supabase
document_embeddings table:
  id  | chunk_index | chunk_text                    | embedding (768 dims)
-----|-------------|-------------------------------|---------------------
  1  |      0      | "K-Nearest Neighbors..."     | [0.123, -0.456, ...]
  2  |      1      | "Ưu điểm của KNN: ..."       | [0.111, -0.222, ...]
```

---

### **Bước 2: RAG QUERY (Trả lời câu hỏi)**

Dùng khi muốn hỏi câu hỏi về tài liệu đã ingest:

```bash
python scripts/rag_query.py --query "Nêu ưu điểm của KNN" --document-id "01287d1b..." --top-k 5
```

**Khi chạy lệnh này xảy ra gì?**

#### **A. Retrieval (Tìm kiếm)**

1. Lấy câu hỏi: `"Nêu ưu điểm của KNN"`
2. Dùng **cùng mô hình embedding** → chuyển câu hỏi thành vector 768 chiều
3. Tìm trong database những chunk có **cosine similarity cao nhất** (gần nhất) với vector câu hỏi
   - Cosine similarity: số từ 0 đến 1 (1 = giống hệt, 0 = khác hẳn)
   - Lấy top-5 chunk có similarity cao nhất
4. Kết quả: 5 chunk liên quan nhất kèm similarity score

Ví dụ:
```
Query: "Nêu ưu điểm của KNN"
Query vector: [0.111, -0.222, 0.333, ..., 0.444]

So với DB:
  Chunk 0: similarity = 0.45 ("K-Nearest Neighbors...")
  Chunk 1: similarity = 0.92 ✓ ("Ưu điểm của KNN: ...")
  Chunk 2: similarity = 0.88 ✓ ("KNN không yêu cầu training...")
  Chunk 3: similarity = 0.85 ✓ ("Ưu điểm 1: Đơn giản...")
  ...
→ Top-5: [Chunk1 (0.92), Chunk2 (0.88), Chunk3 (0.85), Chunk4 (0.83), Chunk5 (0.81)]
```

#### **B. Prompt Building (Xây dựng câu hỏi cho LLM)**

Ghép lại:
```
System: "Bạn là trợ lý thông minh. Dùng thông tin được cung cấp để trả lời câu hỏi."

Context (từ retrieval):
- Chunk 1 (similarity: 0.92): "Ưu điểm của KNN: 1. Đơn giản 2. Không yêu cầu training..."
- Chunk 2 (similarity: 0.88): "KNN không cần học từ dữ liệu huấn luyện..."
- ... (chunk 3, 4, 5)

User query: "Nêu ưu điểm của KNN"
```

#### **C. LLM Inference (Gọi Ollama)**

Gửi prompt trên đến Ollama (chạy locally tại `http://localhost:11434`):
- Model: `llama3` (chạy trên máy bạn, không cần API key, hoàn toàn offline)
- Ollama đọc context + query → trả lời

Kết quả:
```
"Theo tài liệu, KNN có các ưu điểm sau:

1. Đơn giản: KNN là thuật toán dễ hiểu và dễ implement.

2. Không yêu cầu training: KNN là thuật toán lazy learning, 
   không cần huấn luyện model trước.

3. [ưu điểm khác nếu có trong context]"
```

---

## 💾 Cơ Sở Dữ Liệu (Supabase Schema)

### Bảng: `documents`
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  filename TEXT,
  title TEXT,
  source TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Bảng: `document_embeddings` (pgvector)
```sql
CREATE TABLE document_embeddings (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id),
  chunk_index INTEGER,
  chunk_text TEXT,
  embedding vector(768),    -- 768-dimensional vector
  created_at TIMESTAMP
);

-- Index để tìm kiếm nhanh
CREATE INDEX ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**IVFFlat Index**: 
- Giảm độ phức tạp từ O(n) → O(log n)
- Chia 100 cluster, tìm kiếm chỉ trong cluster gần nhất

---

## 🔧 Từng File Chi Tiết

### **1. config.py** - Đọc Cấu Hình
```python
@dataclass
class Settings:
    supabase_url: str           # Supabase URL
    supabase_service_key: str   # Service key (admin key)
    hf_model_name: str          # Embedding model
    chunk_size: int = 900       # Chiều dài chunk
    chunk_overlap: int = 200    # Overlap giữa chunks
    ollama_url: str             # Ollama endpoint
    ollama_model: str           # LLM model (llama3)
```

**Từ đâu?** File `.env` hoặc biến môi trường

### **2. supabase_client.py** - Kết Nối DB
```python
class SupabaseClient:
    # Lưu embeddings vào DB
    def insert_embeddings(embeddings):
        # INSERT INTO document_embeddings(document_id, chunk_index, embedding, ...)
        
    # Tải metadata tài liệu
    def fetch_document_metadata(doc_id):
        # SELECT * FROM documents WHERE id = doc_id
        
    # Xóa embeddings cũ trước khi ingest lại
    def delete_existing_embeddings(doc_id):
        # DELETE FROM document_embeddings WHERE document_id = doc_id
```

### **3. text_extractor.py** - Trích Text PDF
```python
def extract_pdf_text(pdf_path):
    """
    Đọc PDF từng trang, trích text
    Yield: (page_num, text) từng trang
    """
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            yield (i, text)
```

### **4. chunker.py** - Chia Chunk
```python
def split_chunks(text, chunk_size=900, chunk_overlap=200):
    """
    Dùng langchain RecursiveCharacterTextSplitter
    Chia text thành chunks ~900 ký tự
    Chunks gối nhau 200 ký tự (để không mất thông tin ở biên)
    
    Return: [TextChunk(text, chunk_index)]
    """
```

**Tại sao chia chunk?**
- Model embedding có limit token (~384 tokens = ~1500 ký tự)
- Chunk nhỏ hơn → dễ match với query
- Overlap giữ thông tin liên tục

### **5. embedder.py** - Tạo Vector
```python
class EmbeddingResult:
    vector: list[float]  # 768 số (multilingual model)
    model: str

def embed_chunks(chunks):
    """
    Load mô hình sentence-transformers
    Chuyển chunk text → vector 768 chiều
    Return: [EmbeddingResult(vector=[...], model="multilingual")]
    """
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    embeddings = model.encode(chunk_texts, convert_to_numpy=True)
    # embeddings shape: (n_chunks, 768)
```

**Mô hình đặc biệt:**
- `paraphrase-multilingual-mpnet-base-v2`
- Hiểu 50+ ngôn ngữ (bao gồm tiếng Việt)
- Đầu ra: vector 768 chiều

### **6. retriever.py** - Tìm Kiếm Tương Tự
```python
def retrieve_similar_chunks(query: str, document_id: str, top_k: int = 5):
    """
    1. Embed query bằng cùng mô hình → vector 768 chiều
    2. SELECT embeddings FROM document_embeddings WHERE document_id = doc_id
    3. Tính cosine_similarity(query_vector, mỗi chunk_vector)
    4. Sort theo similarity giảm dần
    5. Return top-k chunks + similarity score
    
    Return: [
        RetrievedChunk(
            chunk_id="...", 
            text="...", 
            similarity=0.92,
            source={"document_id": "...", ...}
        ),
        ...
    ]
    """
```

**Cosine Similarity:**
```
similarity = dot_product(vec1, vec2) / (norm(vec1) * norm(vec2))
Range: [0, 1]
  1.0 = identical
  0.5 = partially similar
  0.0 = completely different
```

### **7. prompt_builder.py** - Xây Prompt
```python
def build_rag_prompt(query: str, context_chunks: List[RetrievedChunk], system_prompt=None):
    """
    Ghép:
    1. System instruction (tiếng Việt thân thiện)
    2. Context từ top-5 chunks (mỗi chunk ghi similarity)
    3. User query
    
    Return: prompt string để gửi LLM
    """
    
    prompt = f"""
    {system_prompt or "Bạn là trợ lý thông minh..."}
    
    Thông tin tham chiếu:
    {"\n".join([
        f"- Chunk {i+1} (similarity: {c.similarity:.2%}): {c.text}"
        for i, c in enumerate(context_chunks)
    ])}
    
    Câu hỏi: {query}
    """
    return prompt
```

### **8. llm_client.py** - Gọi Ollama
```python
async def generate_answer(prompt: str, model: str = "llama3", timeout=30):
    """
    Gọi POST http://localhost:11434/api/generate
    Body: {
        "model": "llama3",
        "prompt": prompt,
        "stream": false
    }
    
    Return: LLMResponse(answer="...", model="llama3", raw={"...": "..."})
    """
```

**Ollama:**
- Chạy LLM locally (offline)
- Không cần API key
- Model đã download trước: `ollama pull llama3`

### **9. rag_service.py** - Điều Phối RAG
```python
def rag_query(query: str, document_id: str, top_k: int = 5, system_prompt=None):
    """
    Bước 1: Retrieval
        chunks = retriever.retrieve_similar_chunks(query, document_id, top_k)
    
    Bước 2: Prompt Building
        prompt = prompt_builder.build_rag_prompt(query, chunks, system_prompt)
    
    Bước 3: LLM Inference
        answer = llm_client.generate_answer(prompt)
    
    Return: {
        "answer": "...",
        "sources": [...],
        "metadata": {"elapsed_ms": 1234, "model": "llama3"},
        "prompt": "...",
        "raw_llm_response": {...}
    }
    """
```

---

## 🔄 Luồng Dữ Liệu (Data Flow)

### **INGEST Flow**
```
PDF File
  ↓ extract_pdf_text()
Text (nhiều trang)
  ↓ chunker.split_chunks()
Chunks: ["K-Nearest...", "Ưu điểm...", ...]
  ↓ embedder.embed_chunks()
Embeddings: [[0.1, 0.2, ...], [0.3, 0.4, ...], ...]
  ↓ supabase_client.insert_embeddings()
Supabase DB (document_embeddings table)
```

### **QUERY Flow**
```
User Query: "Nêu ưu điểm KNN"
  ↓ embedder.embed_query()
Query Vector: [0.1, -0.2, 0.3, ...]
  ↓ retriever.retrieve_similar_chunks()
Top-5 Chunks (từ DB, sorted by similarity)
  ↓ prompt_builder.build_rag_prompt()
Prompt (system + context + query)
  ↓ llm_client.generate_answer()
Ollama (locally) → Answer
  ↓
Return to User: {"answer": "...", "sources": [...], "metadata": {...}}
```

---

## 📝 Ví Dụ Thực Tế

**Tài liệu PDF:** "Machine Learning Algorithms.pdf"

### Ingest:
```bash
python scripts/ingest_document.py "Machine Learning Algorithms.pdf" "ML Algorithms"
```

**Kết quả:** 
- Trích được 50 trang, chia thành 200 chunks
- Tạo 200 vector 768 chiều
- Lưu vào Supabase

### Query:
```bash
python scripts/rag_query.py \
  --query "Hãy giải thích cách hoạt động của Support Vector Machine (SVM)" \
  --document-id "01287d1b-ca04-4c8e-9ec7-5126a606cc37" \
  --top-k 5
```

**Kết quả:**
1. Embed query "Hãy giải thích..." → vector
2. Tìm 5 chunk gần nhất:
   - Chunk 45 (sim: 0.95) "SVM là một thuật toán phân loại..."
   - Chunk 47 (sim: 0.92) "Nguyên tắc SVM: maximize margin..."
   - Chunk 50 (sim: 0.89) "Ví dụ SVM trong binary classification..."
   - ...
3. Ghép prompt gửi Ollama
4. Llama3 trả lời dựa vào 5 chunk:
   ```
   "Support Vector Machine (SVM) là một thuật toán phân loại...
   
   Cách hoạt động:
   1. Tìm hyperplane tối ưu để phân tách hai lớp
   2. Maximize margin (khoảng cách từ hyperplane đến các điểm gần nhất)
   3. Sử dụng kernel trick để xử lý dữ liệu phi tuyến
   ..."
   ```

---

## 🎯 Tóm Tắt Phase A

| Bước | Làm gì | Tool/Library |
|------|--------|--------------|
| **Extract** | Đọc PDF | pdfplumber |
| **Chunk** | Chia text | langchain RecursiveCharacterTextSplitter |
| **Embed** | Text → vector | sentence-transformers (multilingual) |
| **Store** | Lưu DB | Supabase pgvector |
| **Retrieve** | Tìm chunks gần nhất | Cosine similarity |
| **Prompt** | Ghép context + query | String formatting |
| **Generate** | Gọi LLM | Ollama (llama3) |

**Độc lập & Offline:** Phase A chạy hoàn toàn trên máy bạn, không cần API bên ngoài.

---

## ✅ Phase A đã hoàn thành:
- ✓ Lõi RAG (retrieval + generation)
- ✓ Database + Indexing
- ✓ CLI scripts để test
- ✓ Tích hợp sẵn cho Phase B (backend API)

**Phase B** sắp tới: Gói Phase A thành API qua Node backend, để frontend gọi.

