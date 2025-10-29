# 🔌 FILE 6: `src/supabase_client.py` - GIẢ TIẾP SUPABASE

## 📌 Mục Đích File

File này **quản lý tất cả tương tác với Supabase**: authentication, download file, query database, update/insert/delete embeddings.

**Analogy:** Giống như một "trung gian giao tiếp" (client) giữa Python app và Supabase database ở đám mây.

---

## 🔍 PHẦN 1: IMPORT

```python
from pathlib import Path
from typing import Any

from supabase import create_client, Client
from postgrest.exceptions import APIError

from .config import settings
```

| Import | Tác Dụng |
|--------|---------|
| `Path` | Làm việc với file/folder paths |
| `Any` | Type hint cho "bất kỳ kiểu dữ liệu nào" |
| `create_client, Client` | Từ Supabase SDK để tạo/gõ client |
| `APIError` | Exception từ PostgREST (Supabase API) |
| `settings` | Cấu hình từ `config.py` |

**`APIError` là gì?**
- Exception được raise khi API call thất bại
- Ví dụ: column không tồn tại, permission denied, etc.

---

## 🔍 PHẦN 2: GLOBAL CLIENT

```python
_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Tạo (hoặc tái sử dụng) Supabase client dựa trên cấu hình."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase_client
```

### **Cú Pháp Giải Thích:**

#### **`_supabase_client: Client | None = None`**

| Phần | Ý Nghĩa |
|-----|--------|
| `_supabase_client` | Biến global (dấu `_` = private) |
| `: Client \| None` | Có thể là Client object hoặc None |
| `= None` | Khởi tạo thành None (chưa tạo) |

**Tại sao `None` ban đầu?**
- Lazy loading: Chỉ tạo client khi cần
- Tiết kiệm resource

#### **`global _supabase_client`**

- Cho phép sửa biến global bên trong hàm

#### **`if _supabase_client is None:`**

| Phần | Ý Nghĩa |
|-----|--------|
| `is None` | So sánh với None (exact match, không dùng `==`) |

**Tại sao `is` không phải `==`?**
- `is`: So sánh object identity (reference)
- `==`: So sánh value
- Với None, dùng `is` là best practice

```python
# ✓ Đúng
if x is None:
    pass

# ❌ Sai (hoạt động nhưng không best practice)
if x == None:
    pass
```

#### **`_supabase_client = create_client(...)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `create_client(url, key)` | Tạo Supabase client từ credentials |
| `settings.supabase_url` | URL của project Supabase |
| `settings.supabase_service_key` | Service Role Key (có full permissions) |

**Tại sao Service Key không phải Anon Key?**
- Service Key: Full permissions (dùng ở backend)
- Anon Key: Limited permissions (dùng ở frontend)
- Backend cần full permissions để insert/update/delete

#### **Return: `return _supabase_client`**

- Trả về client để dùng ở các function khác

### **Singleton Pattern**

```
Lần 1 gọi get_supabase_client():
  _supabase_client = None
  Tạo client
  Lưu vào _supabase_client
  Return client

Lần 2+ gọi get_supabase_client():
  _supabase_client ≠ None
  Return client (không tạo lại)
```

---

## 🔍 PHẦN 3: HÀM `download_file()`

```python
def download_file(file_path: str, destination: Path) -> Path:
    """Tải tệp từ bucket Supabase về đường dẫn cục bộ được chỉ định."""
    client = get_supabase_client()
    response = client.storage.from_(settings.supabase_bucket).download(file_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response)
    return destination
```

### **Cú Pháp Giải Thích:**

#### **Dòng 1: `def download_file(file_path: str, destination: Path) -> Path:`**

| Phần | Ý Nghĩa |
|-----|--------|
| `file_path: str` | Đường dẫn file TẠI SUPABASE (ví dụ: `"documents/abc.pdf"`) |
| `destination: Path` | Đường dẫn CỤC BỘ để lưu file |
| `-> Path` | Trả về Path (đường dẫn nơi lưu file) |

#### **Dòng 2: `client = get_supabase_client()`**

- Lấy Supabase client (có thể tái sử dụng hoặc tạo mới)

#### **Dòng 3: `response = client.storage.from_(settings.supabase_bucket).download(file_path)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `client.storage` | Module storage (quản lý file uploads) |
| `.from_(settings.supabase_bucket)` | Chọn bucket (ví dụ: `"documents"`) |
| `.download(file_path)` | Tải file từ bucket |

**Chuỗi method gọi:**
```python
client
  .storage  # Access storage module
  .from_("documents")  # Select bucket
  .download("abc.pdf")  # Download file
  # response = binary data (b'...')
```

**`response` là gì?**
- Binary data (bytes) của file
- Ví dụ: file PDF content ở dạng bytes

#### **Dòng 4: `destination.parent.mkdir(parents=True, exist_ok=True)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `destination.parent` | Folder chứa file (parent directory) |
| `.mkdir(...)` | Tạo folder |

**Ví dụ:**
```python
destination = Path("tmp/sub1/file.pdf")
destination.parent  # Path("tmp/sub1")
destination.parent.mkdir(parents=True, exist_ok=True)  # Tạo tmp/sub1 nếu chưa có
```

**Tại sao?**
- Nếu folder chưa tồn tại, sẽ error khi write file
- Tạo trước để chắc chắn

#### **Dòng 5: `destination.write_bytes(response)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `.write_bytes(bytes)` | Ghi binary data vào file |

**Ví dụ:**
```python
path = Path("tmp/file.pdf")
binary_data = b'%PDF-1.4...'  # PDF content
path.write_bytes(binary_data)  # Ghi vào tmp/file.pdf
```

#### **Dòng 6: `return destination`**

- Trả về Path nơi file được lưu
- Để code tiếp theo biết file ở đâu

### **Tóm Tắt Hàm `download_file()`**

```
INPUT: file_path tại Supabase, destination cục bộ
  ↓
1. Get Supabase client
2. Download file từ bucket
3. Tạo folder destination nếu cần
4. Ghi binary data vào file cục bộ
5. Return đường dẫn file
  ↓
OUTPUT: Path nơi file được lưu
```

---

## 🔍 PHẦN 4: HÀM `fetch_document_metadata()`

```python
def fetch_document_metadata(document_id: str) -> dict[str, Any]:
    """Lấy metadata tài liệu từ bảng documents dựa trên document_id."""
    client = get_supabase_client()
    response = (
        client.table("documents")
        .select("id, title, file_path, category_id, group_id, created_by, updated_at")
        .eq("id", document_id)
        .limit(1)
        .execute()
    )
    data = response.data
    if not data:
        raise ValueError(f"Document {document_id} not found")
    return data[0]
```

### **Cú Pháp Giải Thích:**

#### **Query Builder Pattern**

```python
client.table("documents")
    .select("...")
    .eq("id", document_id)
    .limit(1)
    .execute()
```

**Đây là "method chaining":**

| Method | Ý Nghĩa | SQL Tương Đương |
|--------|--------|-----------------|
| `.table("documents")` | Chọn table | `FROM documents` |
| `.select("...")` | Chọn columns | `SELECT id, title, ...` |
| `.eq("id", doc_id)` | WHERE id = doc_id | `WHERE id = ...` |
| `.limit(1)` | Giới hạn 1 hàng | `LIMIT 1` |
| `.execute()` | Thực thi query | Gửi request |

**SQL Tương Đương:**
```sql
SELECT id, title, file_path, category_id, group_id, created_by, updated_at
FROM documents
WHERE id = ?
LIMIT 1
```

#### **`response.data`**

- Kết quả query dạng danh sách dicts
- Ví dụ: `[{"id": "123", "title": "File 1", ...}]`

#### **`if not data: raise ValueError(...)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `if not data:` | Nếu danh sách rỗng (không tìm thấy) |
| `raise ValueError(...)` | Ném lỗi |

#### **`return data[0]`**

- Trả về phần tử đầu tiên (dicts)
- Ví dụ: `{"id": "123", "title": "File 1", ...}`

### **Tóm Tắt Hàm `fetch_document_metadata()`**

```
INPUT: document_id (string)
  ↓
1. Query bảng documents WHERE id = document_id
2. Nếu không tìm thấy → error
3. Nếu tìm thấy → return dicts metadata
  ↓
OUTPUT: dict[str, Any] (metadata)
```

---

## 🔍 PHẦN 5: HÀM `upsert_embedding_status()`

```python
def upsert_embedding_status(document_id: str, status: str, error_message: str | None = None) -> None:
    """Cập nhật trạng thái embedding; fallback sang bảng embedding_status nếu thiếu cột."""
    client = get_supabase_client()
    doc_payload: dict[str, Any] = {"embedding_status": status}
    doc_payload["embedding_error"] = error_message if error_message else None

    try:
        client.table("documents").update(doc_payload).eq("id", document_id).execute()
        return
    except APIError as exc:
        error_text = str(exc).lower()
        if "embedding_error" not in error_text and "embedding_status" not in error_text:
            raise

    status_payload: dict[str, Any] = {
        "document_id": document_id,
        "status": status,
        "error_message": error_message,
    }
    client.table("embedding_status").upsert(status_payload, on_conflict="document_id").execute()
```

### **Cú Pháp Giải Thích:**

#### **Dòng 1: `def upsert_embedding_status(...)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `document_id` | ID của document |
| `status` | "processing", "completed", "failed" |
| `error_message` | Lỗi (nếu có) |

#### **Dòng 2-3: Tạo Payload**

```python
doc_payload: dict[str, Any] = {"embedding_status": status}
doc_payload["embedding_error"] = error_message if error_message else None
```

| Phần | Ý Nghĩa |
|-----|--------|
| `dict[str, Any]` | Type hint: dict với key=str, value=anything |
| `embedding_status: status` | Status value |
| `embedding_error: error_msg or None` | Error (có thể None) |

**Kết quả:**
```python
doc_payload = {
    "embedding_status": "completed",
    "embedding_error": None
}
```

#### **Dòng 4-6: Try Block (Cố Gắng Update Bảng documents)**

```python
try:
    client.table("documents").update(doc_payload).eq("id", document_id).execute()
    return
```

**SQL Tương Đương:**
```sql
UPDATE documents
SET embedding_status = ?, embedding_error = ?
WHERE id = ?
```

**`return` là gì?**
- Nếu thành công, thoát hàm (không chạy phần còn lại)

#### **Dòng 7-9: Except Block (Nếu Lỗi)**

```python
except APIError as exc:
    error_text = str(exc).lower()
    if "embedding_error" not in error_text and "embedding_status" not in error_text:
        raise
```

| Phần | Ý Nghĩa |
|-----|--------|
| `except APIError as exc:` | Nếu API call thất bại |
| `error_text = str(exc).lower()` | Chuyển error thành lowercase string |
| `if "column_name" not in error_text:` | Kiểm tra column "embedding_error" hoặc "embedding_status" gây lỗi |
| `raise` | Re-throw error (nếu không phải column error) |

**Lý do try/except:**
- Schema cũ: `documents` table không có column `embedding_status`, `embedding_error`
- Schema mới: Có column này
- Code này linh hoạt với cả 2 schema

#### **Dòng 10-14: Fallback (Nếu Column Không Tồn Tại)**

```python
status_payload: dict[str, Any] = {
    "document_id": document_id,
    "status": status,
    "error_message": error_message,
}
client.table("embedding_status").upsert(status_payload, on_conflict="document_id").execute()
```

**Upsert = Update or Insert:**
- Nếu `document_id` tồn tại → Update
- Nếu không tồn tại → Insert

**SQL Tương Đương (PostgreSQL):**
```sql
INSERT INTO embedding_status (document_id, status, error_message)
VALUES (?, ?, ?)
ON CONFLICT (document_id) DO UPDATE SET
    status = EXCLUDED.status,
    error_message = EXCLUDED.error_message
```

**`on_conflict="document_id"`:**
- Nếu conflict (trùng document_id), update thay vì error

### **Tóm Tắt Hàm `upsert_embedding_status()`**

```
INPUT: document_id, status, error_message
  ↓
TRY:
  1. Update bảng documents
  2. Nếu thành công → exit
  
EXCEPT APIError:
  1. Check lỗi liên quan embedding column
  2. Nếu không → re-throw error
  
FALLBACK:
  1. Upsert bảng embedding_status (compatibility)
  ↓
OUTPUT: None (chỉ update DB)
```

---

## 🔍 PHẦN 6: HÀM `delete_existing_embeddings()`

```python
def delete_existing_embeddings(document_id: str) -> None:
    """Xoá toàn bộ embedding cũ của tài liệu trước khi ghi mới."""
    client = get_supabase_client()
    client.table("document_embeddings").delete().eq("document_id", document_id).execute()
```

### **Cú Pháp Giải Thích:**

**Query Builder:**

| Method | Ý Nghĩa |
|--------|--------|
| `.table("document_embeddings")` | Chọn table |
| `.delete()` | Xoá hàng |
| `.eq("document_id", id)` | WHERE document_id = id |
| `.execute()` | Thực thi |

**SQL Tương Đương:**
```sql
DELETE FROM document_embeddings
WHERE document_id = ?
```

**Tại sao xoá trước khi ghi mới?**
- Nếu ghi lại document → xoá embeddings cũ
- Tránh trùng/duplicate
- Đảm bảo data fresh

---

## 🔍 PHẦN 7: HÀM `insert_embeddings()`

```python
def insert_embeddings(rows: list[dict[str, Any]]) -> None:
    """Chèn danh sách embedding đã chuẩn hoá vào bảng document_embeddings."""
    if not rows:
        return
    client = get_supabase_client()
    client.table("document_embeddings").insert(rows).execute()
```

### **Cú Pháp Giải Thích:**

#### **`rows: list[dict[str, Any]]`**

| Phần | Ý Nghĩa |
|-----|--------|
| `list[dict[...]]` | Danh sách dicts |
| `dict[str, Any]` | Mỗi dict có key=str, value=anything |

**Ví dụ:**
```python
rows = [
    {
        "document_id": "abc123",
        "content": "Nội dung chunk 1",
        "page_number": 1,
        "chunk_index": 1,
        "embedding": [0.1, 0.2, 0.3, ...]  # 768 số
    },
    {
        "document_id": "abc123",
        "content": "Nội dung chunk 2",
        "page_number": 1,
        "chunk_index": 2,
        "embedding": [0.4, 0.5, 0.6, ...]
    }
]
```

#### **`if not rows: return`**

- Nếu danh sách trống, thoát hàm (tránh insert 0 hàng)

#### **`client.table(...).insert(rows).execute()`**

**SQL Tương Đương:**
```sql
INSERT INTO document_embeddings (document_id, content, page_number, chunk_index, embedding)
VALUES
  (?, ?, ?, ?, ?),
  (?, ?, ?, ?, ?),
  ...
```

---

## 📊 BẢNG TÓM TẮT: 5 Hàm

| Hàm | Input | Output | Tác Dụng |
|-----|-------|--------|---------|
| `get_supabase_client()` | - | Client | Lấy/tạo Supabase client (singleton) |
| `download_file()` | file_path, destination | Path | Tải file từ storage Supabase |
| `fetch_document_metadata()` | document_id | dict | Lấy metadata document từ DB |
| `upsert_embedding_status()` | doc_id, status, error | None | Update trạng thái embedding |
| `delete_existing_embeddings()` | document_id | None | Xoá embeddings cũ |
| `insert_embeddings()` | rows (list of dicts) | None | Insert embeddings mới vào DB |

---

## 🔄 Flow Sử Dụng (pipeline.py)

```python
# pipeline.py: process_document()

# Bước 1: Lấy metadata
metadata = fetch_document_metadata(document_id)
file_path = metadata["file_path"]

# Bước 2: Download file
local_path = download_file(file_path, destination)

# ... extract, chunk, embed ...

# Bước 3: Update status
upsert_embedding_status(document_id, "processing")

# Bước 4: Xoá embeddings cũ
delete_existing_embeddings(document_id)

# Bước 5: Insert embeddings mới
insert_embeddings(records)

# Bước 6: Update status (hoàn thành)
upsert_embedding_status(document_id, "completed")
```

---

## 💡 Các CÚ PHÁP PYTHON CẦN BIẾT

| Cú Pháp | Ý Nghĩa | Ví Dụ |
|--------|--------|-------|
| `global var` | Cho phép sửa biến global | `global _supabase_client` |
| `is None` | So sánh với None | `if x is None:` |
| `path.parent` | Folder chứa file | `Path("a/b/c").parent` = `Path("a/b")` |
| `path.mkdir(parents=True, exist_ok=True)` | Tạo folder | Tạo tất cả parent folders |
| `path.write_bytes(data)` | Ghi binary data | Ghi PDF content vào file |
| `.table("name")` | Chọn table Supabase | `.table("documents")` |
| `.select("col1, col2")` | SELECT columns | `.select("id, title, ...")` |
| `.eq("col", value)` | WHERE col = value | `.eq("id", "abc123")` |
| `.limit(n)` | LIMIT n rows | `.limit(1)` |
| `.execute()` | Thực thi query | Gửi request |
| `.update(dict)` | UPDATE row | `.update({"status": "done"})` |
| `.delete()` | DELETE rows | `.delete().eq("id", "123")` |
| `.insert(rows)` | INSERT rows | `.insert([{...}, {...}])` |
| `.upsert(row, on_conflict="col")` | INSERT or UPDATE | Upsert nếu conflict |
| `try/except Exception:` | Exception handling | Bắt lỗi |
| `raise error` | Ném lỗi | `raise ValueError("...")` |

---

## ✅ Kết Luận

**`supabase_client.py` là "trung gian giao tiếp":**

1. **Singleton Client**: Tạo một lần, tái sử dụng
2. **File Operations**: Download PDF từ cloud
3. **Metadata Query**: Lấy thông tin document
4. **Status Management**: Cập nhật trạng thái + fallback handling
5. **Embedding CRUD**: Delete/Insert/Upsert embeddings

**Pattern: Query Builder**
- Linh hoạt, dễ đọc, dễ thay đổi
- `.table().select().where().execute()`

**Lợi Ích: Tách Concerns**
- Database logic riêng biệt
- Dễ test (mock Supabase)
- Dễ reuse (gọi từ nhiều chỗ)
