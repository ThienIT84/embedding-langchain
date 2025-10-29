# 🎬 GIẢI THÍCH FILE `src/pipeline.py` - TRÁI TIM CỦA EMBEDDING PIPELINE

## 📌 Mục Đích Của File Này

File `pipeline.py` là **"trái tim"** (hoặc "não bộ") của toàn bộ hệ thống embedding.

**Nếu `ingest_document.py` là "điều khiển từ xa"**, thì `pipeline.py` là **"cỗ máy xử lý thực sự"**.

Nó chứa hàm `process_document()` - hàm chính điều phối tất cả quy trình từ đầu đến cuối:
1. Tải tài liệu từ Supabase
2. Tải file PDF về máy
3. Đọc nội dung PDF
4. Chia thành chunks
5. Sinh embedding
6. Lưu vào Supabase
7. Xoá file tạm

---

## 📚 PHẦN 1: PHẦN IMPORT (Import Các Tool Cần Dùng)

```python
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .chunker import split_chunks, TextChunk
from .embedder import embed_chunks, EmbeddingResult
from .config import settings
from .supabase_client import (
    delete_existing_embeddings,
    download_file,
    fetch_document_metadata,
    insert_embeddings,
    upsert_embedding_status,
)
from .text_extractor import extract_pdf_text
```

**Tưởng tượng:** Bạn sắp xây dựng một ngôi nhà. Trước tiên, bạn phải lấy ra tất cả các công cụ cần dùng từ kho chứa.

### **Giải thích từng import:**

| Import | Từ File Nào | Là Gì |
|--------|------------|-------|
| `Path` | `pathlib` | Công cụ để làm việc với đường dẫn file (VD: `/temp/document.pdf`) |
| `Iterable, List` | `typing` | Type hints cho "chuỗi dữ liệu" và "danh sách" |
| `split_chunks, TextChunk` | `.chunker` | Hàm để chia văn bản & lớp dữ liệu chunk |
| `embed_chunks, EmbeddingResult` | `.embedder` | Hàm để sinh embedding & lớp kết quả |
| `settings` | `.config` | Cấu hình toàn hệ thống (đường dẫn, URL Supabase, etc.) |
| `delete_existing_embeddings, download_file, fetch_document_metadata, insert_embeddings, upsert_embedding_status` | `.supabase_client` | Các hàm giao tiếp với Supabase |
| `extract_pdf_text` | `.text_extractor` | Hàm đọc PDF |

**=> Kết quả:** Chúng ta có tất cả các "công cụ" cần thiết để xây dựng quy trình xử lý.

---

## 📝 PHẦN 2: HAM HỖ TRỢ 1 - `_load_document()`

```python
def _load_document(document_path: Path) -> Iterable[TextChunk]:
    """Đọc file PDF đã tải và trả về danh sách TextChunk."""
    document_chunks = extract_pdf_text(document_path)
    return split_chunks(document_chunks)
```

### **Cú Pháp & Ý Nghĩa:**

*   **`def _load_document(document_path: Path) -> Iterable[TextChunk]:`**
    *   `def`: Khai báo một hàm
    *   `_load_document`: Tên hàm (dấu `_` ở đầu nói "đây là hàm nội bộ, chỉ dùng trong file này")
    *   `document_path: Path`: Tham số đầu vào là đường dẫn file (kiểu `Path`)
    *   `-> Iterable[TextChunk]`: Trả về một "chuỗi" các `TextChunk`

### **Hàm Này Làm Gì?**

Hãy tưởng tượng bạn có một cuốn sách PDF dài 100 trang. Hàm này sẽ:

1. **Bước 1: Đọc toàn bộ PDF** (`extract_pdf_text`)
   - Mở file PDF
   - Đọc từng trang
   - Trích text từ mỗi trang
   - Trả về các "khối lớn" nội dung (mỗi khối là 1 trang)

2. **Bước 2: Chia những khối lớn thành khối nhỏ hơn** (`split_chunks`)
   - Lấy những khối từ bước 1
   - Chia mỗi khối thành nhiều đoạn nhỏ (tuỳ theo `CHUNK_SIZE`)
   - Trả về danh sách những đoạn nhỏ này (gọi là `TextChunk`)

**Ví dụ:**
```
Input: /temp/document.pdf (100 trang)
       ↓
       extract_pdf_text()
       ↓
[Trang 1 text..., Trang 2 text..., ..., Trang 100 text...]
       ↓
       split_chunks()
       ↓
[Chunk từ trang 1, Chunk từ trang 1, Chunk từ trang 2, ...]
       ↓
Output: Danh sách các TextChunk
```

---

## 📝 PHẦN 3: HAM HỖ TRỢ 2 - `_prepare_records()`

```python
def _prepare_records(document_id: str, embeddings: List[EmbeddingResult]) -> List[dict[str, object]]:
    """Chuyển danh sách embedding thành payload ghi vào bảng document_embeddings."""
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

### **Hàm Này Làm Gì?**

Hãy tưởng tượng bạn có một danh sách "nhân khẩu" (embedding vectors) của mỗi chunk text. Hàm này sẽ **định dạng lại** thành một danh sách "form đơn" để ghi vào database Supabase.

**Chi tiết:**

*   **`for item in embeddings:`** - Lặp qua từng embedding trong danh sách

*   **`records.append({...})`** - Với mỗi embedding, tạo một "form đơn" (dictionary) chứa:
    *   `"document_id"`: ID của tài liệu (để Supabase biết embedding này thuộc tài liệu nào)
    *   `"content"`: Nội dung text của chunk này
    *   `"page_number"`: Trang nào của PDF
    *   `"chunk_index"`: Chunk thứ mấy
    *   `"embedding"`: Vector số (chuyển từ numpy array sang list bằng `.tolist()`)

**Ví dụ:**
```python
# Input:
embeddings = [
    EmbeddingResult(chunk=TextChunk("Trang 1 nội dung...", 1, 1), vector=[0.1, 0.2, ...]),
    EmbeddingResult(chunk=TextChunk("Trang 1 nội dung tiếp...", 1, 2), vector=[0.3, 0.4, ...]),
]

# Output:
[
    {
        "document_id": "abc-123",
        "content": "Trang 1 nội dung...",
        "page_number": 1,
        "chunk_index": 1,
        "embedding": [0.1, 0.2, ...]
    },
    {
        "document_id": "abc-123",
        "content": "Trang 1 nội dung tiếp...",
        "page_number": 1,
        "chunk_index": 2,
        "embedding": [0.3, 0.4, ...]
    }
]
```

---

## 🎯 PHẦN 4: HAM CHINH - `process_document()`

Đây là **hàm quan trọng nhất**. Nó điều phối toàn bộ quy trình.

```python
def process_document(document_id: str) -> None:
    """Xử lý toàn bộ vòng đời ingest embedding cho một tài liệu duy nhất."""
    metadata = fetch_document_metadata(document_id)
    upsert_embedding_status(document_id=document_id, status="processing")

    file_path: Path | None = None

    try:
        # ... code xử lý ...
    except Exception as exc:
        # ... xử lý lỗi ...
    finally:
        # ... dọn dẹp ...
```

Hàm này có **3 phần chính**: Try, Except, Finally. Hãy đọc từng phần:

### **PHẦN A: KHAI BÁO VÀ ChuẩN bị**

```python
def process_document(document_id: str) -> None:
    """Xử lý toàn bộ vòng đời ingest embedding cho một tài liệu duy nhất."""
    # Lấy thông tin tài liệu từ Supabase
    metadata = fetch_document_metadata(document_id)
    
    # Cập nhật trạng thái: "Tôi đang xử lý"
    upsert_embedding_status(document_id=document_id, status="processing")

    # Chuẩn bị biến lưu trữ đường dẫn file (ban đầu là None)
    file_path: Path | None = None
```

**Giải thích:**

1. **`metadata = fetch_document_metadata(document_id)`**
   - Gọi hàm Supabase để lấy thông tin tài liệu
   - VD: tên file, đường dẫn storage, etc.
   - Lưu vào biến `metadata`

2. **`upsert_embedding_status(..., status="processing")`**
   - Cập nhật trạng thái trong Supabase: "Tài liệu này đang được xử lý"
   - Nếu người dùng kiểm tra, họ sẽ thấy "Processing..."

3. **`file_path: Path | None = None`**
   - Chuẩn bị một biến để lưu đường dẫn file PDF khi tải về
   - Ban đầu là `None` (chưa tải gì cả)
   - Kiểu `Path | None` có nghĩa: có thể là `Path` (đường dẫn) hoặc `None` (không có gì)

### **PHẦN B: TRY - PHẦN XỬ LÝ CHÍNH**

```python
    try:
        # Lấy đường dẫn file trong Supabase storage
        remote_path = metadata.get("file_path")
        if not remote_path:
            raise ValueError(f"Document {document_id} is missing file_path in Supabase")

        # Tạo tên file cục bộ
        filename = Path(remote_path).name or f"{document_id}.pdf"
        file_path = settings.temp_dir / filename
        
        # Tải file về máy
        file_path = download_file(remote_path, file_path)

        # Đọc PDF và chia thành chunks
        text_chunks = _load_document(file_path)
        
        # Sinh embedding cho từng chunk
        embeddings = embed_chunks(text_chunks)
        
        # Chuẩn bị dữ liệu để ghi vào DB
        records = _prepare_records(document_id, embeddings)

        # Xoá embedding cũ (nếu có)
        delete_existing_embeddings(document_id)
        
        # Ghi embedding mới vào DB
        if records:
            insert_embeddings(records)

        # Cập nhật trạng thái: "Xong rồi"
        upsert_embedding_status(document_id=document_id, status="completed")
```

**Giải thích chi tiết từng dòng:**

| Dòng | Tác Dụng |
|-----|---------|
| `remote_path = metadata.get("file_path")` | Lấy đường dẫn file từ metadata (VD: `documents/abc123.pdf`) |
| `if not remote_path: raise ValueError(...)` | Nếu không có đường dẫn, báo lỗi |
| `filename = Path(remote_path).name or f"{document_id}.pdf"` | Trích tên file (VD: `abc123.pdf`); nếu không có tên, dùng `document_id.pdf` |
| `file_path = settings.temp_dir / filename` | Tạo đường dẫn cục bộ (VD: `./tmp/abc123.pdf`) |
| `file_path = download_file(remote_path, file_path)` | Tải file từ Supabase storage về đường dẫn cục bộ |
| `text_chunks = _load_document(file_path)` | Đọc PDF và chia thành chunks (gọi hàm hỗ trợ) |
| `embeddings = embed_chunks(text_chunks)` | Sinh embedding vector cho từng chunk |
| `records = _prepare_records(document_id, embeddings)` | Định dạng embedding thành records (gọi hàm hỗ trợ) |
| `delete_existing_embeddings(document_id)` | Xoá embedding cũ của tài liệu này (tránh trùng lặp) |
| `if records: insert_embeddings(records)` | Nếu có records, ghi vào DB Supabase |
| `upsert_embedding_status(..., status="completed")` | Cập nhật trạng thái: "Hoàn thành" |

### **PHẦN C: EXCEPT - XỬ LÝ LỖI**

```python
    except Exception as exc:
        upsert_embedding_status(document_id=document_id, status="failed", error_message=str(exc))
        raise
```

**Giải thích:**

*   **`except Exception as exc:`** - Nếu có lỗi xảy ra ở trong `try` block, bắt lỗi đó

*   **`upsert_embedding_status(..., status="failed", error_message=str(exc))`** - Cập nhật trạng thái:
    - Status: "failed" (thất bại)
    - Error message: Mô tả lỗi (VD: "Document not found")
    - Người dùng sẽ thấy lỗi gì

*   **`raise`** - Ném lỗi trở lại để lập trình viên biết

### **PHẦN D: FINALLY - DỌN DẸP**

```python
    finally:
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
```

**Giải thích:**

*   **`finally:`** - Phần này **LUÔN** chạy, dù có lỗi hay không

*   **`if file_path and file_path.exists():`** - Kiểm tra:
    - `file_path`: Có đường dẫn file không? (Không phải `None`)
    - `file_path.exists()`: File thực sự tồn tại trên đĩa không?

*   **`file_path.unlink(missing_ok=True)`** - Xoá file tạm:
    - `unlink()`: Xoá file
    - `missing_ok=True`: Nếu file không tồn tại, không báo lỗi (im lặng xoá)

**Tại sao cần xoá?** Vì file PDF được tải về là tạm thời, chỉ dùng để xử lý. Sau khi xử lý xong, không cần giữ nó nữa, xoá để tiết kiệm không gian.

---

## 📊 LUỒNG THỰC TỊ ĐẦY ĐỦ

```
process_document("abc-123") được gọi
    ↓
📝 Chuẩn bị:
    - fetch_document_metadata() → lấy thông tin file
    - upsert_embedding_status("processing") → cập nhật trạng thái
    ↓
🔄 TRY BLOCK - Xử lý chính:
    1️⃣ Kiểm tra remote_path (đường dẫn trong Supabase)
    2️⃣ Tạo đường dẫn cục bộ (./tmp/...)
    3️⃣ download_file() → tải PDF về
    4️⃣ _load_document() → đọc PDF + chia chunks
    5️⃣ embed_chunks() → sinh embedding
    6️⃣ _prepare_records() → định dạng dữ liệu
    7️⃣ delete_existing_embeddings() → xoá cũ
    8️⃣ insert_embeddings() → ghi vào DB
    9️⃣ upsert_embedding_status("completed") → cập nhật trạng thái
    ↓
❌ EXCEPT BLOCK (nếu có lỗi):
    - upsert_embedding_status("failed", error_message=...)
    - Ném lỗi
    ↓
🧹 FINALLY BLOCK (luôn chạy):
    - Xoá file tạm
    ↓
✅ Xong!
```

---

## 🎯 TÓM LẠI

| Phần | Tác Dụng |
|-----|---------|
| **Import** | Lấy tất cả công cụ cần dùng |
| **`_load_document()`** | Đọc PDF + chia chunks |
| **`_prepare_records()`** | Định dạng embedding thành records DB |
| **`process_document()`** | Điều phối toàn bộ quy trình |
| **Try** | Phần xử lý chính |
| **Except** | Xử lý lỗi, cập nhật trạng thái "failed" |
| **Finally** | Xoá file tạm |

---

## 💡 ANALOGY - ĐẠI LOẠI NHƯ

File `pipeline.py` giống như một **đầu bếp nấu ăn**:

1. **Import** = Chuẩn bị tất cả dụng cụ (dao, nĩa, xoong...)
2. **`_load_document()`** = Chuẩn bị nguyên liệu (rửa rau, thái thành từng miếng nhỏ)
3. **`_prepare_records()`** = Trang trí món ăn (xếp đẹp trên đĩa)
4. **`process_document()`** = Cả quy trình nấu ăn (từ mua nguyên liệu, nấu, ra đĩa, dọn dẹp)

Khi bạn gọi `process_document()`, đầu bếp (pipeline) sẽ tự động làm hết mọi thứ.

---

Bạn đã hiểu rõ `pipeline.py` chưa? Có gì thắc mắc không?
