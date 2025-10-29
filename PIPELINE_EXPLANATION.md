# 📚 Pipeline Embedding - Giải Thích Chi Tiết Từng File

## 1️⃣ `scripts/ingest_document.py` - Entry Point

### **Tác dụng chính:**
Đây là điểm vào (entry point) của chương trình. Nó:
1. Nhận `document_id` từ dòng lệnh (command line)
2. Validate ID
3. Gọi hàm chính `process_document()` để bắt đầu embedding

---

## **📖 Giải Thích Chi Tiết Từng Dòng**

### **Dòng 1: `from __future__ import annotations`**

```python
from __future__ import annotations
```

**Là gì?**
- Import từ thư viện tương lai của Python (`__future__`)
- Cho phép sử dụng type hints mới mà không cần import từ `typing`

**Tác dụng cụ thể:**
- **Trước** (Python 3.9): `def func(x: Optional[str]) -> str:`
- **Sau** (với dòng này): `def func(x: str | None) -> str:`

**Ví dụ:**
```python
# Mà không cần làm:
from typing import Optional
def func(x: Optional[str]) -> str:  # Dài dòng

# Có thể làm:
def func(x: str | None) -> str:  # Ngắn gọn hơn
```

**Tại sao dùng?**
- Code ngắn gọn hơn
- Dễ đọc hơn
- Chuẩn hóa với Python 3.10+

---

### **Dòng 3: `import argparse`**

```python
import argparse
```

**Là gì?**
- `argparse` là thư viện Python để parse command-line arguments
- Giúp chương trình nhận tham số từ dòng lệnh

**Tác dụng cụ thể:**
- Tạo parser để xử lý CLI arguments
- Validate kiểu dữ liệu
- Tự động tạo help message

**Ví dụ:**
```bash
# User chạy:
python -m scripts.ingest_document 01287d1b-ca04-4c8e-9ec7-5126a606cc37

# argparse sẽ:
# 1. Nhận "01287d1b-ca04-4c8e-9ec7-5126a606cc37"
# 2. Validate nó là string
# 3. Truyền vào args.document_id
```

---

### **Dòng 5: `from src.pipeline import process_document`**

```python
from src.pipeline import process_document
```

**Là gì?**
- Import function `process_document` từ module `src.pipeline`
- `process_document` là hàm core xử lý toàn bộ embedding

**Tác dụng cụ thể:**
- Đưa hàm chính vào scope của file này
- Sau đó có thể gọi: `process_document(document_id)`

**Cấu trúc thư mục:**
```
Embedding_langchain/
├── scripts/
│   └── ingest_document.py  ← File hiện tại
└── src/
    └── pipeline.py  ← Import từ đây
```

---

## **📝 Phần 1: Define Function `parse_args()`**

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest a document by ID and store embeddings in Supabase"
    )
    parser.add_argument("document_id", help="Supabase document identifier")
    return parser.parse_args()
```

### **Dòng 8: `def parse_args() -> argparse.Namespace:`**

- **`def parse_args()`**: Định nghĩa function tên `parse_args` không có tham số
- **`-> argparse.Namespace`**: Return type hint - hàm trả về object kiểu `Namespace`

**`Namespace` là gì?**
- Object chứa các attributes (tương tự dict)
- Mỗi CLI argument trở thành attribute

**Ví dụ:**
```python
args = argparse.Namespace()
args.document_id = "01287d1b-ca04-4c8e-9ec7-5126a606cc37"
print(args.document_id)  # Output: "01287d1b-ca04-4c8e-9ec7-5126a606cc37"
```

### **Dòng 9-11: Tạo ArgumentParser**

```python
    parser = argparse.ArgumentParser(
        description="Ingest a document by ID and store embeddings in Supabase"
    )
```

- **`ArgumentParser()`**: Tạo parser đối tượng
- **`description=...`**: Mô tả chương trình (hiển thị trong help)

**Kết quả khi user gõ `--help`:**
```bash
$ python -m scripts.ingest_document --help
usage: ingest_document.py [-h] document_id

Ingest a document by ID and store embeddings in Supabase

positional arguments:
  document_id  Supabase document identifier

optional arguments:
  -h, --help   show this help message and exit
```

### **Dòng 12: Khai báo Positional Argument**

```python
    parser.add_argument("document_id", help="Supabase document identifier")
```

- **`"document_id"`**: Tên argument (bắt buộc, không phải option)
- **`help=...`**: Mô tả tham số

**Positional vs Optional:**
```bash
# Positional (bắt buộc):
python -m scripts.ingest_document 01287d1b-ca04-4c8e-9ec7-5126a606cc37
                                   ↑ Không có flag "--"

# Optional (tùy chọn):
python -m scripts.ingest_document --verbose  # Có flag "--"
```

### **Dòng 13: Return Parsed Arguments**

```python
    return parser.parse_args()
```

- **`parse_args()`**: Parse dòng lệnh thực tế
- **Return**: object `Namespace` chứa các arguments

**Ví dụ thực tế:**
```bash
$ python -m scripts.ingest_document 01287d1b-ca04-4c8e-9ec7-5126a606cc37

# parse_args() sẽ:
# 1. Đọc sys.argv = ['ingest_document.py', '01287d1b-ca04-4c8e-9ec7-5126a606cc37']
# 2. Nhận ra "01287d1b-ca04-4c8e-9ec7-5126a606cc37" là document_id
# 3. Return Namespace(document_id='01287d1b-ca04-4c8e-9ec7-5126a606cc37')
```

---

## **📝 Phần 2: Define Function `main()`**

```python
def main() -> None:
    args = parse_args()
    process_document(args.document_id)
```

### **Dòng 16: `def main() -> None:`**

- **`def main()`**: Hàm chính
- **`-> None`**: Hàm này không return gì (return type là None)

### **Dòng 17: `args = parse_args()`**

```python
    args = parse_args()
```

- Gọi hàm `parse_args()` để lấy CLI arguments
- Lưu kết quả vào biến `args`

**Ví dụ:**
```python
# Nếu user chạy: python -m scripts.ingest_document 01287d1b-ca04-4c8e-9ec7-5126a606cc37
# Thì: args = Namespace(document_id='01287d1b-ca04-4c8e-9ec7-5126a606cc37')
```

### **Dòng 18: `process_document(args.document_id)`**

```python
    process_document(args.document_id)
```

- Trích xuất `document_id` từ args
- Gọi hàm core `process_document()` từ pipeline
- Bắt đầu xử lý embedding

**Dòng chảy:**
```
args.document_id = "01287d1b-ca04-4c8e-9ec7-5126a606cc37"
    ↓
process_document("01287d1b-ca04-4c8e-9ec7-5126a606cc37")
    ↓
Bắt đầu embedding...
```

---

## **📝 Phần 3: `if __name__ == "__main__"`**

```python
if __name__ == "__main__":
    main()
```

### **`__name__` là gì?**

Python tự động tạo biến `__name__`:
- Nếu file được **execute trực tiếp**: `__name__ = "__main__"`
- Nếu file được **import từ file khác**: `__name__ = "<tên module>"`

**Ví dụ 1: Execute trực tiếp**
```bash
$ python -m scripts.ingest_document 01287d1b-ca04-4c8e-9ec7-5126a606cc37

# Python báo:
# __name__ = "__main__"
# ✓ Điều kiện if đúng → Chạy main()
```

**Ví dụ 2: Import từ file khác**
```python
# Nếu file khác làm:
from scripts.ingest_document import parse_args

# Python báo:
# __name__ = "scripts.ingest_document"
# ✗ Điều kiện if sai → KHÔNG chạy main()
```

### **Tại sao cần?**

Tránh chạy code lơ lửng khi import:

```python
# ❌ Không nên:
def main():
    args = parse_args()
    process_document(args.document_id)

main()  # ← Chạy ngay lập tức khi file được import!

# ✅ Nên:
def main():
    args = parse_args()
    process_document(args.document_id)

if __name__ == "__main__":
    main()  # ← Chỉ chạy nếu execute trực tiếp
```

---

## **📊 Luồng Thực Thi Chi Tiết**

```
1. User gõ lệnh:
   python -m scripts.ingest_document 01287d1b-ca04-4c8e-9ec7-5126a606cc37
   
2. Python load file ingest_document.py
   
3. Import các module:
   - from __future__ import annotations
   - import argparse
   - from src.pipeline import process_document
   
4. Define functions:
   - parse_args()
   - main()
   
5. Kiểm tra: __name__ == "__main__" ?
   → Yes (vì file được execute trực tiếp)
   
6. Chạy: if __name__ == "__main__":
   
7. Gọi: main()
   
8. main() gọi: args = parse_args()
   
9. parse_args() chạy:
   - ArgumentParser() tạo parser
   - add_argument() khai báo document_id là positional arg
   - parse_args() parse sys.argv
   → Return: Namespace(document_id='01287d1b-ca04-4c8e-9ec7-5126a606cc37')
   
10. main() gọi: process_document(args.document_id)
    
11. process_document('01287d1b-ca04-4c8e-9ec7-5126a606cc37') chạy
    → Bắt đầu embedding pipeline
```

---

## **🎯 Tóm Tắt**

| Phần | Tác dụng |
|-----|---------|
| `from __future__ import annotations` | Type hints hiện đại |
| `import argparse` | Parse CLI arguments |
| `from src.pipeline import process_document` | Import hàm core |
| `parse_args()` | Nhận document_id từ CLI |
| `main()` | Hàm chính, gọi process_document |
| `if __name__ == "__main__"` | Chỉ chạy nếu execute trực tiếp |

---

## **💡 Ví Dụ Thực Tế**

### **Chạy với document_id hợp lệ:**
```bash
$ python -m scripts.ingest_document 01287d1b-ca04-4c8e-9ec7-5126a606cc37
# Output: [Pipeline embedding chạy...]
```

### **Chạy thiếu document_id:**
```bash
$ python -m scripts.ingest_document
# Output: error: the following arguments are required: document_id
```

### **Xem help:**
```bash
$ python -m scripts.ingest_document --help
# Output: (hiển thị description và document_id help text)
```

---

## **Tiếp Theo**
👉 Xem file: `src/pipeline.py` để hiểu quy trình embedding chính
