# 🔄 Luồng Dữ Liệu: Từ text_extractor → chunker → embedder

## ❓ Câu Hỏi Của Bạn

> "Tôi thấy embedder.py lấy TextChunk từ chunker.py, nhưng chunker.py `__init__` chưa set `chunk_index`. Sao ở embedder thì `TextChunk(text="Nội dung 1", page_number=1, chunk_index=1)` lại được định nghĩa đúng?"

## ✅ Trả Lời: **Bạn nhận xét ĐÚNG! Nhưng hiểu nhầm luồng dữ liệu.**

---

## 🔍 Hiểu Lại: Chunker.py ĐÃ SET chunk_index!

### Xem Lại Code chunker.py:

```python
def split_chunks(chunks: Iterable[DocumentChunk]) -> List[TextChunk]:
    """Tách lần lượt từng DocumentChunk thành các TextChunk nhỏ hơn."""
    output: List[TextChunk] = []
    for source_idx, chunk in enumerate(chunks):
        pieces = _splitter.split_text(chunk.text)
        for piece_idx, piece in enumerate(pieces):
            text = piece.strip()
            if not text:
                continue
            output.append(
                TextChunk(
                    text=text,
                    page_number=chunk.page_number,
                    chunk_index=len(output) + 1,  # 👈 ĐÃ SET! Dòng này rất quan trọng
                )
            )
    return output
```

### 🎯 Dòng Quan Trọng:

```python
chunk_index=len(output) + 1,
```

**Đây là nơi `chunk_index` được SET!**

---

## 📊 Luồng Dữ Liệu Chi Tiết

```
┌─────────────────────┐
│ text_extractor.py   │
└──────────┬──────────┘
           │ yield DocumentChunk
           │ (text, page_number)
           │ ❌ CHƯA có chunk_index
           ▼
┌─────────────────────┐
│ chunker.py          │
│ split_chunks()      │
│                     │
│ Tạo TextChunk:      │
│ - text: from piece  │
│ - page_number: từ   │
│   chunk gốc         │
│ - chunk_index:      │
│   len(output) + 1   │ ✅ SET TẠI ĐÂY
└──────────┬──────────┘
           │ return List[TextChunk]
           │ (text, page_number, chunk_index)
           │ ✅ ĐÃ CÓ chunk_index
           ▼
┌─────────────────────┐
│ embedder.py         │
│ embed_chunks()      │
│                     │
│ Lấy TextChunk:      │
│ - text ✓            │
│ - page_number ✓     │
│ - chunk_index ✓     │
│                     │
│ Tạo EmbeddingResult:│
│ - chunk (TextChunk) │
│ - vector (embedding)│
└──────────┬──────────┘
           │ return List[EmbeddingResult]
           ▼
┌─────────────────────┐
│ pipeline.py         │
│ Lưu vào DB          │
└─────────────────────┘
```

---

## 🎬 Ví Dụ Chi Tiết: Từng Bước

### BƯỚC 1: text_extractor.py - Tạo DocumentChunk

```python
# text_extractor.py: extract_pdf_text()

def extract_pdf_text(file_path: Path) -> Iterable[DocumentChunk]:
    reader = PdfReader(str(file_path))
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.replace("\x00", "").strip()
        if not text:
            continue
        yield DocumentChunk(text=text, page_number=idx)
        #      ↑ Chỉ có 2 thuộc tính!
        #      text + page_number
        #      CHƯA có chunk_index
```

**Output từ text_extractor:**

```python
[
    DocumentChunk(text="Trang 1 nội dung...", page_number=1),
    #             ↑ chỉ có text và page_number
    
    DocumentChunk(text="Trang 2 nội dung...", page_number=2),
    DocumentChunk(text="Trang 3 nội dung...", page_number=3),
]
```

---

### BƯỚC 2: chunker.py - Tạo TextChunk (CÓ chunk_index)

```python
# chunker.py: split_chunks()

def split_chunks(chunks: Iterable[DocumentChunk]) -> List[TextChunk]:
    output: List[TextChunk] = []
    
    for source_idx, chunk in enumerate(chunks):  # chunk từ text_extractor
        pieces = _splitter.split_text(chunk.text)
        
        for piece_idx, piece in enumerate(pieces):
            text = piece.strip()
            
            if not text:
                continue
            
            # ✅ ĐÂY LÀ NƠI TẠO TextChunk VỚI chunk_index!
            output.append(
                TextChunk(
                    text=text,                           # Từ pieces
                    page_number=chunk.page_number,       # Từ DocumentChunk gốc
                    chunk_index=len(output) + 1,         # ✅ SET TẠI ĐÂY!
                )
            )
    
    return output
```

**Xử Lý Chi Tiết:**

```
Input: [DocumentChunk(text="Trang 1...", page_number=1)]

Iteration 1:
  chunk = DocumentChunk(text="Trang 1...", page_number=1)
  pieces = _splitter.split_text("Trang 1...")
         = ["Đoạn 1a", "Đoạn 1b", "Đoạn 1c"]  (3 phần)
  
  Piece 1:
    text = "Đoạn 1a"
    output.append(TextChunk(
        text="Đoạn 1a",
        page_number=1,
        chunk_index=len(output) + 1 = 0 + 1 = 1  ✅
    ))
    output = [TextChunk1]
  
  Piece 2:
    text = "Đoạn 1b"
    output.append(TextChunk(
        text="Đoạn 1b",
        page_number=1,
        chunk_index=len(output) + 1 = 1 + 1 = 2  ✅
    ))
    output = [TextChunk1, TextChunk2]
  
  Piece 3:
    text = "Đoạn 1c"
    output.append(TextChunk(
        text="Đoạn 1c",
        page_number=1,
        chunk_index=len(output) + 1 = 2 + 1 = 3  ✅
    ))
    output = [TextChunk1, TextChunk2, TextChunk3]
```

**Output từ chunker:**

```python
[
    TextChunk(text="Đoạn 1a", page_number=1, chunk_index=1),  # ✅ CÓ chunk_index
    TextChunk(text="Đoạn 1b", page_number=1, chunk_index=2),
    TextChunk(text="Đoạn 1c", page_number=1, chunk_index=3),
]
```

---

### BƯỚC 3: embedder.py - Nhận TextChunk (ĐÃ CÓ chunk_index)

```python
# embedder.py: embed_chunks()

def embed_chunks(chunks: Iterable[TextChunk]) -> List[EmbeddingResult]:
    """chunks đến từ chunker, ĐÃ CÓ chunk_index"""
    
    chunk_list = list(chunks)
    # chunk_list = [
    #     TextChunk(text="Đoạn 1a", page_number=1, chunk_index=1),
    #     TextChunk(text="Đoạn 1b", page_number=1, chunk_index=2),
    #     TextChunk(text="Đoạn 1c", page_number=1, chunk_index=3),
    # ]
    
    if not chunk_list:
        return []
    
    model = _get_model()
    
    # Lấy tất cả text
    texts = [chunk.text for chunk in chunk_list]
    # texts = ["Đoạn 1a", "Đoạn 1b", "Đoạn 1c"]
    
    # Sinh embedding
    embeddings = model.encode(texts, show_progress_bar=True)
    # embeddings = [
    #     [0.1, 0.2, 0.3, ...],  (768 số)
    #     [0.4, 0.5, 0.6, ...],  (768 số)
    #     [0.7, 0.8, 0.9, ...],  (768 số)
    # ]
    
    # Ghép chunks + embeddings
    result = [
        EmbeddingResult(
            chunk=chunk,  # ✅ chunk ĐÃ CÓ chunk_index
            vector=np.array(vector, dtype=np.float32)
        )
        for chunk, vector in zip(chunk_list, embeddings)
    ]
    
    # result = [
    #     EmbeddingResult(
    #         chunk=TextChunk(..., chunk_index=1),
    #         vector=[0.1, 0.2, ...]
    #     ),
    #     EmbeddingResult(
    #         chunk=TextChunk(..., chunk_index=2),
    #         vector=[0.4, 0.5, ...]
    #     ),
    #     EmbeddingResult(
    #         chunk=TextChunk(..., chunk_index=3),
    #         vector=[0.7, 0.8, ...]
    #     ),
    # ]
    
    return result
```

**Output từ embedder:**

```python
[
    EmbeddingResult(
        chunk=TextChunk(text="Đoạn 1a", page_number=1, chunk_index=1),
        vector=np.array([0.1, 0.2, ...])
    ),
    EmbeddingResult(
        chunk=TextChunk(text="Đoạn 1b", page_number=1, chunk_index=2),
        vector=np.array([0.4, 0.5, ...])
    ),
    EmbeddingResult(
        chunk=TextChunk(text="Đoạn 1c", page_number=1, chunk_index=3),
        vector=np.array([0.7, 0.8, ...])
    ),
]
```

---

## 🎯 Bảng So Sánh: Dữ Liệu Ở Mỗi Giai Đoạn

| Giai Đoạn | Lớp | text | page_number | chunk_index | Trạng Thái |
|-----------|-----|------|-------------|-------------|-----------|
| **text_extractor.py** | `DocumentChunk` | ✅ | ✅ | ❌ | Chưa set |
| **chunker.py (output)** | `TextChunk` | ✅ | ✅ | ✅ | Đã set |
| **embedder.py** | `EmbeddingResult.chunk` | ✅ | ✅ | ✅ | Có sẵn |

---

## 💡 Lý Do Bạn Nhầm Lẫn

### Ở File EXTRACTOR_CHUNKER_EMBEDDER_EXPLAINED.md:

Tôi viết ví dụ cho embedder:

```python
EmbeddingResult(
    chunk=TextChunk(text="Nội dung 1", page_number=1, chunk_index=1),
    vector=...
),
```

**Bạn hỏi:** "Sao `chunk_index=1` được mà chunker.py `__init__` không set?"

**Câu Trả Lời:** 
- **Chunker ĐÃ set!** (dòng `chunk_index=len(output) + 1`)
- Embedder CHỈ nhận TextChunk từ chunker
- TextChunk từ chunker ĐÃ CÓ `chunk_index`

### Tôi Viết Bị Nhầm Hình Ảnh

Ở ví dụ embedder, tôi nên viết rõ hơn:

```python
# ❌ SAI: Tạo TextChunk trực tiếp (như ở chunker)
chunk = TextChunk(text="Nội dung 1", page_number=1, chunk_index=1)

# ✅ ĐÚNG: Nhận TextChunk từ chunker
chunk = ...  # Từ split_chunks() return

# Rồi dùng nó:
result = EmbeddingResult(chunk=chunk, vector=...)
```

---

## 🔄 Luồng Dữ Liệu Thực Tế (pipeline.py)

```python
# pipeline.py

def process_document(document_id: str) -> None:
    """Quy trình chính"""
    
    # Bước 1: Tải file PDF
    file_path = download_file(...)
    
    # Bước 2: Extract text (mỗi trang = 1 DocumentChunk)
    # ❌ CHƯA có chunk_index
    document_chunks = extract_pdf_text(file_path)
    #  ↓
    # [DocumentChunk(..., page=1), DocumentChunk(..., page=2)]
    
    # Bước 3: Chia chunks (tạo TextChunk với chunk_index)
    # ✅ ĐÃ set chunk_index
    text_chunks = split_chunks(document_chunks)
    #  ↓
    # [TextChunk(..., page=1, index=1), TextChunk(..., page=1, index=2), ...]
    
    # Bước 4: Sinh embedding
    # ✅ chunk ĐÃ CÓ chunk_index
    embeddings = embed_chunks(text_chunks)
    #  ↓
    # [EmbeddingResult(chunk=..., vector=...), ...]
    
    # Bước 5: Lưu vào DB
    records = _prepare_records(document_id, embeddings)
    insert_embeddings(records)
```

---

## ✅ Kết Luận

**Chunker ĐÃ set `chunk_index`!**

```python
# chunker.py - Dòng quan trọng:
output.append(
    TextChunk(
        text=text,
        page_number=chunk.page_number,
        chunk_index=len(output) + 1,  # ✅ SET TẠI ĐÂY
    )
)
```

**Flow dữ liệu:**
```
text_extractor (chưa index)
    ↓ yield
chunker (tạo index)  ← SET chunk_index TẠI ĐÂY
    ↓ return
embedder (dùng sẵn index)
    ↓
pipeline (lưu index vào DB)
```

**Bạn không nhầm lẫn logic, chỉ là flow dữ liệu qua các file làm bạn confused!** 🎉

Bây giờ hiểu rõ hơn chưa?
