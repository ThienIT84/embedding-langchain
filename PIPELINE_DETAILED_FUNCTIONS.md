# 🔬 GIẢI THÍCH CHI TIẾT TỪNG HÀM TRONG `pipeline.py`

---

## 🎯 HÀM 1: `_load_document(document_path: Path) -> Iterable[TextChunk]`

### **Mục Đích:**
Đọc một file PDF đã được tải về, trích text từ mỗi trang, rồi chia thành các đoạn nhỏ.

### **Cú Pháp Giải Thích:**

```python
def _load_document(document_path: Path) -> Iterable[TextChunk]:
    """Đọc file PDF đã tải và trả về danh sách TextChunk."""
```

#### **`def _load_document(...):`**
- **`def`**: Từ khóa khai báo hàm
- **`_load_document`**: Tên hàm (dấu `_` ở đầu = "hàm nội bộ", chỉ dùng trong file này)
- Dấu `_` không ảnh hưởng tính năng, chỉ là quy ước lập trình viên

#### **`(document_path: Path)`**
- **`document_path`**: Tên tham số đầu vào (input)
- **`: Path`**: Type hint - tham số này phải là kiểu `Path` (đường dẫn file)
- **`Path` là gì?** 
  - Là một lớp (class) từ thư viện `pathlib` của Python
  - Dùng để làm việc với đường dẫn file một cách an toàn, tương thích trên nhiều hệ điều hành
  - Ví dụ: `Path("/tmp/document.pdf")` hoặc `Path("C:\\Users\\...\\file.pdf")`

#### **`-> Iterable[TextChunk]`**
- **`->`**: Type hint trả về
- **`Iterable[TextChunk]`**: Hàm trả về một "chuỗi" các `TextChunk`
- **`Iterable` là gì?**
  - Có nghĩa là "có thể lặp qua" (for loop)
  - `Iterable[TextChunk]` = "một chuỗi mà mỗi phần tử là TextChunk"
  - Ví dụ: `[chunk1, chunk2, chunk3, ...]`
- **`TextChunk`**:
  - Là một lớp dữ liệu tự định nghĩa (từ file `chunker.py`)
  - Chứa: `text` (nội dung), `page_number` (trang), `chunk_index` (thứ tự chunk)

### **Nội Dung Hàm:**

```python
    document_chunks = extract_pdf_text(document_path)
    return split_chunks(document_chunks)
```

#### **Dòng 1: `document_chunks = extract_pdf_text(document_path)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `extract_pdf_text(...)` | Gọi hàm từ file `text_extractor.py` |
| `document_path` | Truyền vào đường dẫn file PDF |
| `= document_chunks` | Lưu kết quả vào biến `document_chunks` |

**Hàm này làm gì?**
- Mở file PDF
- Đọc từng trang
- Trích text từ mỗi trang
- Trả về một chuỗi `DocumentChunk` (mỗi chunk là 1 trang)

**Ví dụ Output:**
```python
# document_chunks sẽ chứa:
[
    DocumentChunk(text="Nội dung trang 1...", page_number=1),
    DocumentChunk(text="Nội dung trang 2...", page_number=2),
    DocumentChunk(text="Nội dung trang 3...", page_number=3),
]
```

#### **Dòng 2: `return split_chunks(document_chunks)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `split_chunks(...)` | Gọi hàm từ file `chunker.py` |
| `document_chunks` | Truyền vào danh sách chunks lớn từ bước trước |
| `return` | Trả về kết quả của hàm |

**Hàm này làm gì?**
- Lấy danh sách chunks lớn (mỗi chunk là 1 trang)
- Chia mỗi chunk thành nhiều chunks nhỏ hơn (theo `CHUNK_SIZE`)
- Trả về danh sách chunks nhỏ (kiểu `TextChunk`)

**Ví dụ Output:**
```python
# Kết quả return sẽ là:
[
    TextChunk(text="Phần 1 của trang 1...", page_number=1, chunk_index=1),
    TextChunk(text="Phần 2 của trang 1...", page_number=1, chunk_index=2),
    TextChunk(text="Phần 1 của trang 2...", page_number=2, chunk_index=3),
    ...
]
```

### **Tóm Tắt Hàm `_load_document()`**

```
INPUT:  /tmp/document.pdf (một file PDF)
  ↓
[Xử lý]
  1. extract_pdf_text() → Đọc PDF, trích text từng trang
  2. split_chunks() → Chia mỗi trang thành chunks nhỏ
  ↓
OUTPUT: Danh sách TextChunk [chunk1, chunk2, chunk3, ...]
```

---

## 🎯 HÀM 2: `_prepare_records(document_id: str, embeddings: List[EmbeddingResult]) -> List[dict[str, object]]`

### **Mục Đích:**
Lấy danh sách embedding vector (từ hàm `embed_chunks`), định dạng lại thành danh sách "form đơn" để ghi vào database Supabase.

### **Cú Pháp Giải Thích:**

```python
def _prepare_records(document_id: str, embeddings: List[EmbeddingResult]) -> List[dict[str, object]]:
    """Chuyển danh sách embedding thành payload ghi vào bảng document_embeddings."""
```

#### **`(document_id: str, embeddings: List[EmbeddingResult])`**

| Tham Số | Kiểu | Ý Nghĩa |
|--------|------|--------|
| `document_id` | `str` | ID của tài liệu (chuỗi text, VD: "abc-123") |
| `embeddings` | `List[EmbeddingResult]` | Danh sách embedding vectors |

**`List[EmbeddingResult]` là gì?**
- **`List[...]`**: Một danh sách (mảng)
- **`EmbeddingResult`**: Kiểu phần tử trong danh sách
- **`EmbeddingResult`** là lớp dữ liệu chứa:
  - `chunk`: Một `TextChunk` (đoạn text + metadata)
  - `vector`: Embedding vector (mảng số, VD: `[0.1, 0.2, 0.3, ...]`)

#### **`-> List[dict[str, object]]`**

- **`List[...]`**: Danh sách
- **`dict[str, object]`**: Mỗi phần tử là một từ điển (dictionary)
  - **`str`**: Key của từ điển là chuỗi (VD: `"document_id"`, `"content"`)
  - **`object`**: Value có thể là bất cứ kiểu dữ liệu nào (string, number, list, etc.)
- **Ví dụ:**
  ```python
  [
      {"document_id": "abc", "content": "text...", "page_number": 1, ...},
      {"document_id": "abc", "content": "text...", "page_number": 1, ...},
  ]
  ```

### **Nội Dung Hàm:**

```python
    records: List[dict[str, object]] = []
    for item in embeddings:
        records.append(
            {
                "document_id": document_id,
                "content": item.chunk.text,
                "page_number": item.chunk.page_number,
                "chunk_index": item.chunk.chunk_index,
                "embedding": item.vector.tolist(),
            }
        )
    return records
```

#### **Dòng 1: `records: List[dict[str, object]] = []`**

| Phần | Ý Nghĩa |
|-----|--------|
| `records` | Tên biến để chứa kết quả |
| `: List[dict[str, object]]` | Type hint - `records` là danh sách các dictionary |
| `= []` | Khởi tạo thành danh sách rỗng |

#### **Dòng 2-3: `for item in embeddings:`**

**Ý Nghĩa:**
- Lặp qua từng `EmbeddingResult` trong danh sách `embeddings`
- Mỗi lần lặp, `item` sẽ là một `EmbeddingResult`

**Ví dụ:**
```python
embeddings = [
    EmbeddingResult(chunk=chunk1, vector=vec1),
    EmbeddingResult(chunk=chunk2, vector=vec2),
    EmbeddingResult(chunk=chunk3, vector=vec3),
]

# Lần 1: item = EmbeddingResult(chunk=chunk1, vector=vec1)
# Lần 2: item = EmbeddingResult(chunk=chunk2, vector=vec2)
# Lần 3: item = EmbeddingResult(chunk=chunk3, vector=vec3)
```

#### **Dòng 4-10: `records.append({...})`**

**Ý Nghĩa:**
- **`records.append(...)`**: Thêm phần tử vào cuối danh sách `records`
- Phần tử là một dictionary (từ điển) chứa:

| Key | Value | Ý Nghĩa |
|-----|-------|--------|
| `"document_id"` | `document_id` | ID tài liệu (truyền vào hàm) |
| `"content"` | `item.chunk.text` | Nội dung text của chunk |
| `"page_number"` | `item.chunk.page_number` | Trang nào |
| `"chunk_index"` | `item.chunk.chunk_index` | Chunk thứ mấy |
| `"embedding"` | `item.vector.tolist()` | Vector embedding (chuyển từ numpy array sang list) |

**`item.chunk.text` là gì?**
- **`item`**: Một `EmbeddingResult`
- **`.chunk`**: Truy cập thuộc tính `chunk` của `item`
- **`.text`**: Truy cập thuộc tính `text` của `chunk`
- Tức là: "Lấy text từ chunk bên trong embedding này"

**`item.vector.tolist()` là gì?**
- **`item.vector`**: Một numpy array (mảng từ thư viện numpy)
- **`.tolist()`**: Chuyển numpy array thành list thường của Python
- **Tại sao?** Vì Supabase (database) dễ lưu trữ list hơn numpy array

#### **Dòng 11: `return records`**
- Trả về danh sách `records` đã được điền đầy đủ

### **Ví Dụ Cụ Thể:**

**Input:**
```python
document_id = "doc-123"
embeddings = [
    EmbeddingResult(
        chunk=TextChunk(text="Nội dung 1", page_number=1, chunk_index=1),
        vector=np.array([0.1, 0.2, 0.3])
    ),
    EmbeddingResult(
        chunk=TextChunk(text="Nội dung 2", page_number=1, chunk_index=2),
        vector=np.array([0.4, 0.5, 0.6])
    ),
]
```

**Output (kết quả return):**
```python
[
    {
        "document_id": "doc-123",
        "content": "Nội dung 1",
        "page_number": 1,
        "chunk_index": 1,
        "embedding": [0.1, 0.2, 0.3]
    },
    {
        "document_id": "doc-123",
        "content": "Nội dung 2",
        "page_number": 1,
        "chunk_index": 2,
        "embedding": [0.4, 0.5, 0.6]
    },
]
```

### **Tóm Tắt Hàm `_prepare_records()`**

```
INPUT:
  - document_id: "doc-123"
  - embeddings: [EmbeddingResult1, EmbeddingResult2, ...]
  ↓
[Xử Lý]
  Lặp qua từng embedding
  Tạo dictionary chứa: document_id, content, page_number, chunk_index, embedding
  Thêm vào danh sách records
  ↓
OUTPUT: Danh sách dictionary [dict1, dict2, dict3, ...]
```

---

## 🎯 HÀM 3: `process_document(document_id: str) -> None`

### **Mục Đích:**
Hàm chính, điều phối toàn bộ quy trình embedding từ đầu đến cuối.

### **Cú Pháp Giải Thích:**

```python
def process_document(document_id: str) -> None:
    """Xử lý toàn bộ vòng đời ingest embedding cho một tài liệu duy nhất."""
```

#### **`(document_id: str)`**
- **`document_id`**: ID của tài liệu cần xử lý
- **`: str`**: Phải là chuỗi text

#### **`-> None`**
- **`None`**: Hàm này không trả về giá trị
- Hàm chỉ thực hiện các "tác vụ phụ" (side effects): tải file, ghi DB, etc.
- Khi gọi hàm, không có gì để lưu: `process_document("id")` (không có `result = ...`)

### **Nội Dung Hàm - PHẦN A: CHUẨN BỊ**

```python
    metadata = fetch_document_metadata(document_id)
    upsert_embedding_status(document_id=document_id, status="processing")
    file_path: Path | None = None
```

#### **Dòng 1: `metadata = fetch_document_metadata(document_id)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `fetch_document_metadata(...)` | Gọi hàm từ `supabase_client.py` |
| `document_id` | Truyền vào ID tài liệu |
| `= metadata` | Lưu kết quả vào biến `metadata` |

**Hàm này trả về gì?**
- Một dictionary (từ điển) chứa thông tin tài liệu từ Supabase
- **Ví dụ:**
  ```python
  metadata = {
      "id": "doc-123",
      "title": "My Document",
      "file_path": "documents/my-doc.pdf",
      "category_id": "cat-1",
      "created_by": "user-1",
      ...
  }
  ```

#### **Dòng 2: `upsert_embedding_status(document_id=document_id, status="processing")`**

| Phần | Ý Nghĩa |
|-----|--------|
| `upsert_embedding_status(...)` | Gọi hàm từ `supabase_client.py` |
| `document_id=document_id` | Keyword argument: ID tài liệu |
| `status="processing"` | Keyword argument: Trạng thái là "đang xử lý" |

**Hàm này làm gì?**
- Cập nhật trạng thái tài liệu trong Supabase
- Từ "pending" (chờ xử lý) thành "processing" (đang xử lý)
- Người dùng sẽ thấy: "Embedding this document..."

#### **Dòng 3: `file_path: Path | None = None`**

| Phần | Ý Nghĩa |
|-----|--------|
| `file_path` | Tên biến |
| `: Path \| None` | Type hint: có thể là `Path` hoặc `None` |
| `\|` | Ký hiệu "hoặc" (or) |
| `= None` | Khởi tạo thành `None` (chưa có gì) |

**Tại sao cần biến này?**
- Sẽ lưu đường dẫn file PDF khi tải về
- Ban đầu là `None` vì chưa tải
- Cần chuẩn bị sẵn vì `finally` block sẽ kiểm tra

### **Nội Dung Hàm - PHẦN B: TRY (XỬ LÝ CHÍNH)**

```python
    try:
        remote_path = metadata.get("file_path")
        if not remote_path:
            raise ValueError(f"Document {document_id} is missing file_path in Supabase")

        filename = Path(remote_path).name or f"{document_id}.pdf"
        file_path = settings.temp_dir / filename
        file_path = download_file(remote_path, file_path)

        text_chunks = _load_document(file_path)
        embeddings = embed_chunks(text_chunks)
        records = _prepare_records(document_id, embeddings)

        delete_existing_embeddings(document_id)
        if records:
            insert_embeddings(records)

        upsert_embedding_status(document_id=document_id, status="completed")
```

#### **Dòng 1: `remote_path = metadata.get("file_path")`**

| Phần | Ý Nghĩa |
|-----|--------|
| `metadata.get("file_path")` | Lấy giá trị của key `"file_path"` từ dictionary `metadata` |
| `.get(...)` | Phương thức để lấy value từ dictionary |
| `= remote_path` | Lưu vào biến `remote_path` |

**Tại sao dùng `.get()` thay vì `metadata["file_path"]`?**
- `.get()` trả về `None` nếu key không tồn tại
- `[...]` sẽ báo lỗi nếu key không tồn tại
- Dùng `.get()` an toàn hơn

**`remote_path` là gì?**
- Đường dẫn file trong Supabase storage
- **Ví dụ:** `"documents/my-doc.pdf"`

#### **Dòng 2-3: `if not remote_path: raise ValueError(...)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `if not remote_path:` | Nếu `remote_path` là `None` hoặc rỗng |
| `raise ValueError(...)` | Ném lỗi với message |

**`not` là gì?**
- Toán tử logic "không" (NOT)
- `not None` = `True`
- `not "something"` = `False`
- `if not remote_path` = "nếu `remote_path` là None hay rỗng"

**`raise ValueError(...)` là gì?**
- **`raise`**: Từ khóa ném lỗi
- **`ValueError`**: Loại lỗi (giá trị không đúng)
- **`(...)`**: Thông điệp lỗi
- Khi ném lỗi, hàm sẽ dừng và nhảy vào `except` block

#### **Dòng 5: `filename = Path(remote_path).name or f"{document_id}.pdf"`**

| Phần | Ý Nghĩa |
|-----|--------|
| `Path(remote_path)` | Chuyển đường dẫn (string) thành object `Path` |
| `.name` | Lấy tên file (phần cuối của đường dẫn) |
| `or` | Toán tử logic "hoặc" |
| `f"{document_id}.pdf"` | Fallback: nếu `.name` rỗng, dùng string này |

**Ví dụ:**
```python
# Nếu remote_path = "documents/my-doc.pdf"
Path(remote_path).name  # → "my-doc.pdf"

# Nếu remote_path = "documents/"  (không có tên file)
Path(remote_path).name  # → ""  (rỗng)
# Thì dùng fallback: f"{document_id}.pdf"  → "doc-123.pdf"
```

**`f"..."` là gì?**
- **f-string**: Chuỗi định dạng (formatted string)
- Cho phép nhúng biến vào chuỗi bằng `{...}`
- **Ví dụ:** `f"{document_id}.pdf"` → `"doc-123.pdf"`

#### **Dòng 6: `file_path = settings.temp_dir / filename`**

| Phần | Ý Nghĩa |
|-----|--------|
| `settings.temp_dir` | Đường dẫn thư mục tạm (từ file config) |
| `/` | Toán tử nối đường dẫn (chỉ hoạt động với `Path` object) |
| `filename` | Tên file cần nối |
| `= file_path` | Lưu đường dẫn đầy đủ |

**Ví dụ:**
```python
settings.temp_dir = Path("./tmp")
filename = "my-doc.pdf"
file_path = Path("./tmp") / "my-doc.pdf"
# Kết quả: Path("./tmp/my-doc.pdf")
```

**`/` là toán tử gì?**
- Bình thường `/` là phép chia
- Nhưng với `Path` object, nó là "nối đường dẫn"
- Tiện hơn `os.path.join()` và tương thích với mọi OS

#### **Dòng 7: `file_path = download_file(remote_path, file_path)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `download_file(...)` | Gọi hàm từ `supabase_client.py` |
| `remote_path` | Đường dẫn trong Supabase storage |
| `file_path` | Đường dẫn cục bộ để lưu file |
| `= file_path` | Lưu kết quả (đường dẫn file đã tải) |

**Hàm này làm gì?**
- Tải file từ Supabase storage xuống máy
- Lưu vào `file_path`
- Trả về `file_path` (xác nhận file đã tải xong)

#### **Dòng 9: `text_chunks = _load_document(file_path)`**

- Gọi hàm helper `_load_document()` (đã giải thích ở trên)
- Truyền vào đường dẫn file PDF
- Trả về danh sách `TextChunk`

#### **Dòng 10: `embeddings = embed_chunks(text_chunks)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `embed_chunks(...)` | Gọi hàm từ `embedder.py` |
| `text_chunks` | Danh sách `TextChunk` từ trước |
| `= embeddings` | Lưu danh sách `EmbeddingResult` |

**Hàm này làm gì?**
- Lấy danh sách text chunks
- Sinh embedding vector cho từng chunk
- Trả về danh sách `EmbeddingResult` (chunk + vector)

#### **Dòng 11: `records = _prepare_records(document_id, embeddings)`**

- Gọi hàm helper `_prepare_records()` (đã giải thích ở trên)
- Truyền vào ID tài liệu và danh sách embeddings
- Trả về danh sách dictionary (payload cho database)

#### **Dòng 13: `delete_existing_embeddings(document_id)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `delete_existing_embeddings(...)` | Gọi hàm từ `supabase_client.py` |
| `document_id` | ID tài liệu |

**Hàm này làm gì?**
- Tìm tất cả embedding cũ của tài liệu này trong DB
- Xoá chúng (để tránh trùng lặp)
- Sẽ ghi embedding mới ở dòng tiếp theo

#### **Dòng 14-15: `if records: insert_embeddings(records)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `if records:` | Nếu `records` không rỗng |
| `insert_embeddings(records)` | Chèn danh sách records vào database |

**Tại sao `if records:`?**
- Chỉ ghi vào DB nếu có dữ liệu
- Tránh lỗi nếu `records` là danh sách rỗng

#### **Dòng 17: `upsert_embedding_status(document_id=document_id, status="completed")`**

- Cập nhật trạng thái: "completed" (hoàn thành)
- Người dùng sẽ thấy: "Embedding completed ✓"

### **Nội Dung Hàm - PHẦN C: EXCEPT (XỬ LÝ LỖI)**

```python
    except Exception as exc:
        upsert_embedding_status(document_id=document_id, status="failed", error_message=str(exc))
        raise
```

#### **Dòng 1: `except Exception as exc:`**

| Phần | Ý Nghĩa |
|-----|--------|
| `except` | Bắt lỗi |
| `Exception` | Bắt mọi loại lỗi |
| `as exc` | Gán lỗi vào biến `exc` |

**`Exception` là gì?**
- Lớp cơ sở cho tất cả lỗi trong Python
- `except Exception` bắt hầu hết mọi lỗi

#### **Dòng 2: `upsert_embedding_status(..., status="failed", error_message=str(exc))`**

| Phần | Ý Nghĩa |
|-----|--------|
| `status="failed"` | Đánh dấu tài liệu thất bại |
| `error_message=str(exc)` | Thông điệp lỗi (chuyển exception thành string) |

**`str(exc)` là gì?**
- Chuyển object exception thành chuỗi text
- **Ví dụ:** `"File not found"` hoặc `"Connection error"`

#### **Dòng 3: `raise`**

- Ném lỗi lên (sau khi cập nhật status)
- Cho phép lập trình viên biết lỗi gì xảy ra

### **Nội Dung Hàm - PHẦN D: FINALLY (DỌN DẸP)**

```python
    finally:
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
```

#### **Dòng 1: `finally:`**

- Phần này **luôn chạy**, dù có lỗi hay không
- Dùng để dọn dẹp tài nguyên

#### **Dòng 2-3: `if file_path and file_path.exists(): file_path.unlink(...)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `file_path` | Kiểm tra `file_path` không phải `None` |
| `and` | Toán tử logic "và" |
| `file_path.exists()` | Kiểm tra file tồn tại trên đĩa không |
| `file_path.unlink(...)` | Xoá file |
| `missing_ok=True` | Nếu file không tồn tại, im lặn (không báo lỗi) |

**Tại sao `and`?**
- Nếu `file_path` là `None`, thì `file_path.exists()` sẽ báo lỗi
- Dùng `and` để kiểm tra `file_path` trước
- Nếu `file_path` là `None`, phần sau không chạy (short-circuit)

---

## 📊 BẢNG TÓMLỖI TẤT CẢ HÀM

| Hàm | Input | Output | Tác Dụng |
|-----|-------|--------|---------|
| **`_load_document()`** | File path (Path) | Danh sách TextChunk | Đọc PDF + chia chunks |
| **`_prepare_records()`** | document_id (str), embeddings (list) | Danh sách dict | Định dạng data cho DB |
| **`process_document()`** | document_id (str) | None (không có) | Điều phối toàn bộ |

---

## 💡 CÁC CÚ PHÁP PYTHON CẦN BIẾT

| Cú Pháp | Ý Nghĩa | Ví Dụ |
|--------|--------|-------|
| `: type` | Type hint | `document_id: str` |
| `-> type` | Type hint trả về | `-> None` |
| `List[T]` | Danh sách phần tử kiểu T | `List[int]` |
| `dict[K, V]` | Dictionary với key kiểu K, value kiểu V | `dict[str, int]` |
| `\|` | Hoặc | `Path \| None` |
| `for x in iterable:` | Lặp | `for item in embeddings:` |
| `.get(key)` | Lấy value từ dict | `metadata.get("file_path")` |
| `.append(x)` | Thêm vào cuối list | `records.append({...})` |
| `.tolist()` | Chuyển numpy array sang list | `vector.tolist()` |
| `Path(...)` | Tạo path object | `Path("/tmp/file.pdf")` |
| `/` với Path | Nối đường dẫn | `Path("./tmp") / "file.pdf"` |
| `if not x:` | Nếu x là False/None/rỗng | `if not remote_path:` |
| `raise Error(...)` | Ném lỗi | `raise ValueError("Error!")` |
| `try/except/finally` | Xử lý lỗi | (xem ở trên) |
| `f"..."` | F-string | `f"{name}.pdf"` |

---

Bạn đã hiểu rõ từng hàm chưa? Có phần nào cần giải thích thêm không?
