# 🔬 GIẢI THÍCH 3 FILE TRỌNG TÂM: TEXT_EXTRACTOR, CHUNKER, EMBEDDER

---

# 📄 FILE 1: `src/text_extractor.py` - ĐỌC FILE PDF

## 📌 Mục Đích File

File này chỉ làm **một việc duy nhất**: Đọc file PDF, trích text từ từng trang, và gửi cho file tiếp theo.

**Analogy:** Giống như bạn mở một cuốn sách PDF, đọc từng trang, viết lại nội dung trang đó vào notebook.

---

## 🔍 PHẦN 1: IMPORT & KHÁI NIỆM

```python
from __future__ import annotations
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader
```

| Import | Từ Đâu | Tác Dụng |
|--------|--------|---------|
| `Path` | `pathlib` | Làm việc với đường dẫn file |
| `Iterable` | `typing` | Type hint cho "chuỗi dữ liệu có thể lặp" |
| `PdfReader` | `pypdf` | Thư viện đọc file PDF |

**`PdfReader` là gì?**
- Một lớp (class) từ thư viện `pypdf`
- Dùng để mở file PDF và đọc từng trang
- Giống như một "bộ đọc PDF" chuyên nghiệp

---

## 🔍 PHẦN 2: LỚP `DocumentChunk`

```python
class DocumentChunk:
    """Cấu trúc nhẹ chứa đoạn văn bản và (tuỳ chọn) số trang."""

    __slots__ = ("text", "page_number")

    def __init__(self, text: str, page_number: int | None = None) -> None:
        self.text = text
        self.page_number = page_number
```

### **Cú Pháp Giải Thích:**

#### **`class DocumentChunk:`**
- **`class`**: Từ khóa định nghĩa một lớp (class)
- **`DocumentChunk`**: Tên lớp
- Lớp này là một "mẫu" (template) để tạo object chứa dữ liệu

#### **`__slots__ = ("text", "page_number")`**

| Phần | Ý Nghĩa |
|-----|--------|
| `__slots__` | Một attribute đặc biệt của Python |
| `= (...)` | Danh sách các thuộc tính object này có thể chứa |

**`__slots__` là gì?**
- Nói với Python: "Object này chỉ chứa 2 attribute: `text` và `page_number`"
- Không thể thêm attribute khác
- **Lợi ích:** Tiết kiệm memory (quan trọng khi có nhiều objects)

**Ví dụ:**
```python
# Với __slots__, chỉ được
chunk.text = "nội dung"
chunk.page_number = 1

# Nhưng không được
chunk.author = "John"  # ❌ Error: 'DocumentChunk' object has no attribute 'author'
```

#### **`def __init__(self, text: str, page_number: int | None = None) -> None:`**

| Phần | Ý Nghĩa |
|-----|--------|
| `def __init__(...)` | Hàm khởi tạo (constructor) |
| `self` | Object hiện tại |
| `text: str` | Tham số, phải là chuỗi |
| `page_number: int \| None = None` | Tham số tùy chọn (mặc định `None`) |
| `-> None` | Không return gì |

**`__init__` là gì?**
- Hàm đặc biệt được gọi tự động khi tạo object mới
- Dùng để khởi tạo các thuộc tính

**`page_number: int | None = None` là gì?**
- **`int | None`**: Có thể là số nguyên hoặc `None`
- **`= None`**: Nếu không truyền vào, mặc định là `None`

**Ví dụ sử dụng:**
```python
# Cách 1: Truyền cả 2 tham số
chunk1 = DocumentChunk(text="Nội dung trang 1", page_number=1)

# Cách 2: Chỉ truyền text (page_number mặc định None)
chunk2 = DocumentChunk(text="Nội dung")

# Object được tạo:
# chunk1.text = "Nội dung trang 1"
# chunk1.page_number = 1
# chunk2.text = "Nội dung"
# chunk2.page_number = None
```

#### **`self.text = text` và `self.page_number = page_number`**

| Phần | Ý Nghĩa |
|-----|--------|
| `self` | Object hiện tại |
| `.text` | Attribute `text` của object |
| `= text` | Gán giá trị tham số `text` vào attribute |

**Điều này làm gì?**
- Lưu tham số đầu vào vào các attribute của object
- Sau này có thể truy cập: `chunk.text`, `chunk.page_number`

---

## 🔍 PHẦN 3: HÀM `extract_pdf_text()`

```python
def extract_pdf_text(file_path: Path) -> Iterable[DocumentChunk]:
    """Đọc PDF và yield các khối nội dung theo từng trang."""
    reader = PdfReader(str(file_path))
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.replace("\x00", "").strip()
        if not text:
            continue
        yield DocumentChunk(text=text, page_number=idx)
```

### **Cú Pháp Giải Thích:**

#### **`def extract_pdf_text(file_path: Path) -> Iterable[DocumentChunk]:`**

| Phần | Ý Nghĩa |
|-----|--------|
| `file_path: Path` | Tham số: đường dẫn file PDF |
| `-> Iterable[DocumentChunk]` | Trả về một chuỗi `DocumentChunk` |

**`Iterable[DocumentChunk]` là gì?**
- Một "chuỗi" các `DocumentChunk` có thể lặp qua
- Không phải danh sách cố định, mà là "luồng dữ liệu" (stream)
- Dùng `yield` để trả về từng phần tử một

#### **Dòng 1: `reader = PdfReader(str(file_path))`**

| Phần | Ý Nghĩa |
|-----|--------|
| `PdfReader(...)` | Tạo một object đọc PDF |
| `str(file_path)` | Chuyển `Path` object thành string |
| `= reader` | Lưu vào biến `reader` |

**Tại sao `str(file_path)`?**
- `PdfReader` có thể nhận string hoặc Path
- Chuyển thành string để chắc chắn tương thích
- `str(Path("/tmp/file.pdf"))` → `"/tmp/file.pdf"`

**`reader` được tạo là gì?**
- Một object đã mở file PDF
- Bây giờ có thể đọc từng trang qua `reader.pages`

#### **Dòng 2: `for idx, page in enumerate(reader.pages, start=1):`**

| Phần | Ý Nghĩa |
|-----|--------|
| `for ... in` | Lặp qua từng phần tử |
| `enumerate(reader.pages, start=1)` | Lặp qua từng trang, bắt đầu từ 1 |
| `idx, page` | `idx` là số thứ tự (1, 2, 3, ...), `page` là object trang |

**`enumerate(...)` là gì?**
- Hàm Python để lặp và lấy chỉ số (index)
- **`start=1`**: Bắt đầu từ 1 (thay vì 0)

**Ví dụ:**
```python
pages = [page1, page2, page3]
for idx, page in enumerate(pages, start=1):
    # Lần 1: idx=1, page=page1
    # Lần 2: idx=2, page=page2
    # Lần 3: idx=3, page=page3
```

#### **Dòng 3: `text = page.extract_text() or ""`**

| Phần | Ý Nghĩa |
|-----|--------|
| `page.extract_text()` | Gọi phương thức để trích text từ trang |
| `or ""` | Nếu kết quả `None`, dùng `""` (chuỗi rỗng) |

**`or ""` là gì?**
- **`or`**: Toán tử logic "hoặc"
- Nếu `page.extract_text()` trả về `None` (không có text), dùng `""`
- Tránh lỗi khi gọi phương thức trên `None`

**Ví dụ:**
```python
text = None or ""          # text = ""
text = "Hello" or ""       # text = "Hello"
text = "" or ""            # text = ""
```

#### **Dòng 4: `text = text.replace("\x00", "").strip()`**

| Phần | Ý Nghĩa |
|-----|--------|
| `.replace("\x00", "")` | Xoá ký tự null (`\x00`) từ text |
| `.strip()` | Xoá khoảng trắng đầu/cuối |

**`\x00` là ký tự gì?**
- Là ký tự null (ASCII 0)
- Đôi khi PDF chứa ký tự này, cần xoá
- `replace(old, new)`: Thay thế `old` bằng `new`

**Ví dụ:**
```python
text = "Hello\x00World"
text = text.replace("\x00", "")
# text = "HelloWorld"

text = "  Hello World  "
text = text.strip()
# text = "Hello World"
```

#### **Dòng 5-6: `if not text: continue`**

| Phần | Ý Nghĩa |
|-----|--------|
| `if not text:` | Nếu text rỗng |
| `continue` | Bỏ qua lần lặp này, sang trang tiếp theo |

**Tại sao?**
- Nếu trang PDF không có text (ví dụ trang trắng), bỏ qua
- Tránh lưu các chunk rỗng

#### **Dòng 7: `yield DocumentChunk(text=text, page_number=idx)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `yield` | Trả về một phần tử (nhưng không kết thúc hàm) |
| `DocumentChunk(...)` | Tạo một object DocumentChunk |
| `text=text, page_number=idx` | Với text đã trích, trang thứ `idx` |

**`yield` là gì?**
- Khác `return`: `return` kết thúc hàm, `yield` tạm dừng
- Lần gọi hàm tiếp theo, hàm sẽ tiếp tục từ sau `yield`
- Dùng để tạo "generator" (luồng dữ liệu)

**Ví dụ:**
```python
def gen():
    print("1")
    yield 10
    print("2")
    yield 20

for x in gen():
    print(x)

# Output:
# 1
# 10
# 2
# 20
```

### **Tóm Tắt Hàm `extract_pdf_text()`**

```
INPUT: /tmp/document.pdf
  ↓
Mở file PDF bằng PdfReader
  ↓
Lặp qua từng trang (idx, page):
  1. Trích text từ trang
  2. Xoá ký tự null
  3. Xoá khoảng trắng
  4. Nếu text rỗng, bỏ qua
  5. Nếu có text, yield DocumentChunk
  ↓
OUTPUT: Chuỗi DocumentChunk (mỗi phần tử là 1 trang)
```

---

---

# 📄 FILE 2: `src/chunker.py` - CHIA TEXT THÀNH CHUNKS

## 📌 Mục Đích File

File này lấy các `DocumentChunk` lớn (mỗi trang PDF = 1 chunk lớn), chia chúng thành những `TextChunk` nhỏ hơn.

**Analogy:** Giống như bạn có một chương sách (trang), và bạn chia nó thành các đoạn nhỏ (chunks) để dễ hiểu hơn.

---

## 🔍 PHẦN 1: IMPORT

```python
from typing import Iterable, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings
from .text_extractor import DocumentChunk
```

| Import | Tác Dụng |
|--------|---------|
| `Iterable, List` | Type hints |
| `RecursiveCharacterTextSplitter` | Công cụ chia text của LangChain |
| `settings` | Cấu hình (chunk_size, chunk_overlap) |
| `DocumentChunk` | Lớp từ file `text_extractor.py` |

---

## 🔍 PHẦN 2: LỚP `TextChunk` (Mở Rộng)

```python
class TextChunk(DocumentChunk):
    """Mở rộng DocumentChunk để lưu thêm thứ tự và chỉ số chunk."""

    __slots__ = ("text", "page_number", "chunk_index")

    def __init__(self, text: str, page_number: int | None = None, chunk_index: int | None = None) -> None:
        super().__init__(text=text, page_number=page_number)
        self.chunk_index = chunk_index
```

### **Cú Pháp Giải Thích:**

#### **`class TextChunk(DocumentChunk):`**

| Phần | Ý Nghĩa |
|-----|--------|
| `class TextChunk(...)` | Định nghĩa lớp `TextChunk` |
| `(DocumentChunk)` | Kế thừa từ lớp `DocumentChunk` |

**Kế thừa (Inheritance) là gì?**
- `TextChunk` "extends" `DocumentChunk`
- Kế thừa tất cả thuộc tính, phương thức từ lớp cha
- Có thể thêm attributes mới

**Ví dụ:**
```python
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):  # Dog kế thừa từ Animal
    def __init__(self, name, breed):
        super().__init__(name)  # Gọi __init__ của Animal
        self.breed = breed

dog = Dog("Buddy", "Golden")
# dog.name = "Buddy"  (từ Animal)
# dog.breed = "Golden"  (từ Dog)
```

#### **`super().__init__(text=text, page_number=page_number)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `super()` | Tham chiếu đến lớp cha |
| `.`__init__`(...)` | Gọi hàm `__init__` của lớp cha |

**`super()` là gì?**
- Cho phép gọi phương thức của lớp cha từ lớp con
- Tránh phải viết lại code của lớp cha

#### **`self.chunk_index = chunk_index`**

- Lưu attribute mới `chunk_index` (không có ở lớp cha)
- Đây là số thứ tự của chunk

**Tóm Tắt:**
```
DocumentChunk: text, page_number
       ↑ (kế thừa)
TextChunk: text, page_number, chunk_index (thêm mới)
```

---

## 🔍 PHẦN 3: GLOBAL SPLITTER

```python
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", " ", ""],
)
```

### **Cú Pháp Giải Thích:**

#### **`_splitter = RecursiveCharacterTextSplitter(...)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `_splitter` | Tên biến global (dấu `_` = biến private) |
| `RecursiveCharacterTextSplitter(...)` | Công cụ chia text từ LangChain |

**`RecursiveCharacterTextSplitter` là gì?**
- Lớp từ thư viện LangChain
- Dùng để chia text dài thành chunks nhỏ
- "Recursive" = chia lần lượt theo các separator

#### **`chunk_size=settings.chunk_size`**

- Kích thước mỗi chunk (bao nhiêu ký tự)
- VD: 900 ký tự

#### **`chunk_overlap=settings.chunk_overlap`**

- Độ chồng lấp giữa chunks liên tiếp
- VD: 200 ký tự
- **Tại sao?** Để không mất thông tin ở biên giữa chunks

**Ví dụ:**
```
Text: "ABCDEFGHIJ..." (1000 ký tự)
chunk_size=3, chunk_overlap=1

Chunk 1: "ABC"
Chunk 2: "BCD"  (chồng 1 ký tự "B", "C")
Chunk 3: "DEF"
...
```

#### **`separators=["\n\n", "\n", " ", ""]`**

- Danh sách ký tự/chuỗi dùng để chia
- Thứ tự: nếu không chia được bằng `"\n\n"`, thử `"\n"`, rồi `" "`, cuối cùng `""`

**Ý Nghĩa:**
1. **`"\n\n"`**: Chia theo đoạn (double newline) - ưu tiên nhất
2. **`"\n"`**: Chia theo dòng
3. **`" "`**: Chia theo khoảng trắng
4. **`""`**: Chia theo từng ký tự (cuối cùng)

**Ví dụ:**
```
Text: "Đoạn 1\n\nĐoạn 2\n\nĐoạn 3"

Chia bằng "\n\n":
- Chunk 1: "Đoạn 1"
- Chunk 2: "Đoạn 2"
- Chunk 3: "Đoạn 3"
```

### **Tại sao `_splitter` là biến global?**

- Dùng chung cho tất cả hàm trong file
- Tạo một lần (không lãng phí memory)
- Tất cả lệnh gọi `_splitter.split_text()` dùng cùng object

---

## 🔍 PHẦN 4: HÀM `split_chunks()`

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
                    chunk_index=len(output) + 1,
                )
            )
    return output
```

### **Cú Pháp Giải Thích:**

#### **`def split_chunks(chunks: Iterable[DocumentChunk]) -> List[TextChunk]:`**

| Phần | Ý Nghĩa |
|-----|--------|
| `chunks: Iterable[DocumentChunk]` | Input: chuỗi DocumentChunk (từ `extract_pdf_text`) |
| `-> List[TextChunk]` | Output: danh sách TextChunk |

#### **Dòng 1: `output: List[TextChunk] = []`**

- Tạo danh sách rỗng để lưu kết quả

#### **Dòng 2: `for source_idx, chunk in enumerate(chunks):`**

- Lặp qua từng `DocumentChunk` trong input
- `source_idx`: chỉ số (0, 1, 2, ...)
- `chunk`: object DocumentChunk

#### **Dòng 3: `pieces = _splitter.split_text(chunk.text)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `_splitter.split_text(...)` | Gọi công cụ chia text |
| `chunk.text` | Lấy text từ chunk |
| `= pieces` | Lưu danh sách pieces (đoạn nhỏ) |

**Hàm này trả về gì?**
- Một danh sách string (mỗi phần tử là một đoạn nhỏ)
- VD: `["Đoạn 1", "Đoạn 2", "Đoạn 3"]`

#### **Dòng 4-5: `for piece_idx, piece in enumerate(pieces):`**

- Lặp qua từng `piece` (đoạn nhỏ)

#### **Dòng 6-7: `text = piece.strip()` và `if not text: continue`**

- Xoá khoảng trắng đầu/cuối
- Bỏ qua nếu rỗng

#### **Dòng 8-14: `output.append(TextChunk(...))`**

| Phần | Ý Nghĩa |
|-----|--------|
| `output.append(...)` | Thêm phần tử vào danh sách |
| `TextChunk(...)` | Tạo object TextChunk |
| `text=text` | Nội dung text |
| `page_number=chunk.page_number` | Trang từ chunk gốc |
| `chunk_index=len(output) + 1` | Số thứ tự (1, 2, 3, ...) |

**`len(output) + 1` là gì?**
- `len(output)`: Số phần tử trong `output` hiện tại
- `+ 1`: Thêm 1 để bắt đầu từ 1 (thay vì 0)

#### **Dòng 15: `return output`**

- Trả về danh sách `TextChunk` đầy đủ

### **Ví Dụ Cụ Thể:**

**Input:**
```python
chunks = [
    DocumentChunk(text="Trang 1: ABC DEF GHI", page_number=1),
    DocumentChunk(text="Trang 2: JKL MNO", page_number=2),
]
# chunk_size=5, chunk_overlap=1, separator=[" ", ""]
```

**Xử lý:**
```
Chunk 1 (Trang 1):
  Text: "Trang 1: ABC DEF GHI"
  Split by spaces: ["Trang", "1:", "ABC", "DEF", "GHI"]
  Combine to chunk_size=5: 
    - Piece 1: "Trang 1: ABC"  (text="Trang 1: ABC", page=1, index=1)
    - Piece 2: "ABC DEF"       (text="ABC DEF", page=1, index=2)
    - Piece 3: "DEF GHI"       (text="DEF GHI", page=1, index=3)

Chunk 2 (Trang 2):
  ...
```

**Output:**
```python
[
    TextChunk(text="Trang 1: ABC", page_number=1, chunk_index=1),
    TextChunk(text="ABC DEF", page_number=1, chunk_index=2),
    TextChunk(text="DEF GHI", page_number=1, chunk_index=3),
    TextChunk(text="Trang 2: JKL", page_number=2, chunk_index=4),
    ...
]
```

### **Tóm Tắt Hàm `split_chunks()`**

```
INPUT: Chuỗi DocumentChunk
  ↓
Lặp qua từng chunk:
  1. Lấy text từ chunk
  2. Chia thành pieces nhỏ
  3. Lặp qua từng piece:
     - Xoá khoảng trắng
     - Nếu không rỗng, tạo TextChunk mới
  ↓
OUTPUT: Danh sách TextChunk
```

---

---

# 📄 FILE 3: `src/embedder.py` - SINH EMBEDDING VECTOR

## 📌 Mục Đích File

File này lấy các `TextChunk` (đoạn text nhỏ), sinh embedding vector (mảng số đại diện cho ý nghĩa) cho mỗi chunk.

**Analogy:** Giống như bạn có một cuốn sách, và bạn tạo một "bản đồ tư duy" (embedding vector) cho mỗi đoạn để máy tính hiểu ý nghĩa.

---

## 🔍 PHẦN 1: IMPORT

```python
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings
from .chunker import TextChunk
```

| Import | Tác Dụng |
|--------|---------|
| `numpy as np` | Thư viện làm việc với mảng số |
| `SentenceTransformer` | Model AI để sinh embedding |
| `settings` | Cấu hình (tên model) |
| `TextChunk` | Lớp từ file `chunker.py` |

**`numpy` là gì?**
- Thư viện Python mạnh mẽ cho tính toán khoa học
- Làm việc với mảng (arrays) và ma trận

**`SentenceTransformer` là gì?**
- Một model AI đã được huấn luyện sẵn
- Chuyên dùng để sinh embedding (vector đại diện ý nghĩa) cho text
- Là part của thư viện `sentence-transformers`

---

## 🔍 PHẦN 2: LỚP `EmbeddingResult`

```python
class EmbeddingResult:
    """Đóng gói TextChunk cùng vector embedding tương ứng."""
    __slots__ = ("chunk", "vector")

    def __init__(self, chunk: TextChunk, vector: np.ndarray) -> None:
        self.chunk = chunk
        self.vector = vector
```

### **Cú Pháp Giải Thích:**

#### **`__slots__ = ("chunk", "vector")`**

- Object này chỉ chứa 2 attribute:
  - `chunk`: Một object `TextChunk` (đoạn text)
  - `vector`: Một numpy array (embedding vector)

#### **`vector: np.ndarray`**

| Phần | Ý Nghĩa |
|-----|--------|
| `np.ndarray` | Type hint: numpy array (mảng) |

**`np.ndarray` là gì?**
- `np`: Là alias của `numpy`
- `ndarray`: "n-dimensional array" (mảng nhiều chiều)
- Ở đây là 1D array (mảng 1 chiều) chứa số thập phân

**Ví dụ:**
```python
import numpy as np

vector = np.array([0.1, 0.2, 0.3, 0.4, ...])  # 768 số
print(type(vector))  # <class 'numpy.ndarray'>
```

### **Tóm Tắt Lớp `EmbeddingResult`**

```
EmbeddingResult chứa:
  - chunk: TextChunk (text + metadata)
  - vector: np.ndarray (embedding vector)
```

---

## 🔍 PHẦN 3: GLOBAL MODEL

```python
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Khởi tạo (hoặc tái sử dụng) model SentenceTransformer dùng chung."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.hf_model_name)
    return _model
```

### **Cú Pháp Giải Thích:**

#### **`_model: SentenceTransformer | None = None`**

| Phần | Ý Nghĩa |
|-----|--------|
| `_model` | Biến global (dấu `_` = private) |
| `: SentenceTransformer \| None` | Có thể là model hoặc `None` |
| `= None` | Khởi tạo thành `None` (chưa load model) |

#### **`global _model`**

| Phần | Ý Nghĩa |
|-----|--------|
| `global` | Từ khóa: cho phép sửa biến global |
| `_model` | Tên biến global cần sửa |

**`global` là gì?**
- Mặc định, bên trong hàm không thể sửa biến global
- `global` cho phép sửa

**Ví dụ:**
```python
count = 0

def increment():
    global count
    count += 1  # Sửa biến global

increment()
print(count)  # 1
```

#### **`if _model is None: _model = SentenceTransformer(...)`**

- Nếu model chưa được load (`None`), load nó
- **Lazy loading:** Chỉ load khi cần (tiết kiệm memory)

#### **`settings.hf_model_name`**

- Tên model từ cấu hình
- VD: `"sentence-transformers/paraphrase-multilingual-mpnet-base-v2"`

**Tại sao `global _model`?**
- Lần đầu gọi hàm: load model (mất thời gian)
- Lần tiếp theo: tái sử dụng model cũ (nhanh hơn)
- Chỉ load 1 lần duy nhất

### **Tóm Tắt Hàm `_get_model()`**

```
Lần 1 gọi _get_model():
  - _model = None
  - Load model từ HuggingFace
  - Lưu vào _model
  - Return model

Lần 2+ gọi _get_model():
  - _model đã được load
  - Chỉ return _model (không load lại)
```

---

## 🔍 PHẦN 4: HÀM `embed_chunks()`

```python
def embed_chunks(chunks: Iterable[TextChunk]) -> List[EmbeddingResult]:
    """Sinh embedding cho danh sách TextChunk và trả về kết quả dạng list."""
    chunk_list = list(chunks)
    if not chunk_list:
        return []
    model = _get_model()
    embeddings = model.encode([chunk.text for chunk in chunk_list], show_progress_bar=True)
    return [EmbeddingResult(chunk=chunk, vector=np.array(vector, dtype=np.float32)) for chunk, vector in zip(chunk_list, embeddings)]
```

### **Cú Pháp Giải Thích:**

#### **Dòng 1: `chunk_list = list(chunks)`**

- Chuyển từ `Iterable` thành `List`
- **Tại sao?** Để dùng được chỉ số (index) sau này

**Ví dụ:**
```python
# Iterable: không thể truy cập theo index
iterable = (x for x in range(10))
# iterable[0]  # ❌ Error

# List: có thể truy cập theo index
chunk_list = list(iterable)
# chunk_list[0]  # ✅ OK
```

#### **Dòng 2-3: `if not chunk_list: return []`**

- Nếu danh sách rỗng (không có chunks), return danh sách rỗng
- Tránh lỗi khi encoding

#### **Dòng 4: `model = _get_model()`**

- Lấy model SentenceTransformer
- Lần đầu: load từ HuggingFace
- Lần tiếp theo: tái sử dụng

#### **Dòng 5: `embeddings = model.encode([chunk.text for chunk in chunk_list], show_progress_bar=True)`**

**Chia nhỏ:**

##### **`[chunk.text for chunk in chunk_list]`**

| Phần | Ý Nghĩa |
|-----|--------|
| `[... for ... in ...]` | List comprehension (vòng lặp trong list) |
| `chunk.text` | Lấy text từ mỗi chunk |
| `for chunk in chunk_list` | Lặp qua tất cả chunks |

**Ví dụ:**
```python
chunks = [
    TextChunk(text="Nội dung 1", ...),
    TextChunk(text="Nội dung 2", ...),
    TextChunk(text="Nội dung 3", ...),
]

texts = [chunk.text for chunk in chunks]
# Kết quả: ["Nội dung 1", "Nội dung 2", "Nội dung 3"]
```

##### **`model.encode(..., show_progress_bar=True)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `model.encode(...)` | Gọi phương thức sinh embedding |
| `show_progress_bar=True` | Hiển thị thanh tiến độ (progress bar) |

**Hàm này trả về gì?**
- Một numpy array 2D (ma trận)
- Mỗi hàng là embedding vector (768 số) cho một chunk

**Ví dụ:**
```python
texts = ["Hello world", "Goodbye world"]

embeddings = model.encode(texts)
# embeddings.shape = (2, 768)
# embeddings[0] = [0.1, 0.2, 0.3, ...]  (768 số cho "Hello world")
# embeddings[1] = [0.4, 0.5, 0.6, ...]  (768 số cho "Goodbye world")
```

#### **Dòng 6: `return [... for chunk, vector in zip(chunk_list, embeddings)]`**

**Chia nhỏ:**

##### **`zip(chunk_list, embeddings)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `zip(list1, list2)` | Ghép 2 danh sách lại (từng cặp) |

**Ví dụ:**
```python
chunks = [chunk1, chunk2, chunk3]
vectors = [vec1, vec2, vec3]

for chunk, vector in zip(chunks, vectors):
    # Lần 1: chunk=chunk1, vector=vec1
    # Lần 2: chunk=chunk2, vector=vec2
    # Lần 3: chunk=chunk3, vector=vec3
```

##### **`EmbeddingResult(chunk=chunk, vector=np.array(vector, dtype=np.float32))`**

| Phần | Ý Nghĩa |
|-----|--------|
| `np.array(vector, ...)` | Chuyển vector thành numpy array |
| `dtype=np.float32` | Kiểu dữ liệu: số thập phân 32-bit |

**`dtype=np.float32` là gì?**
- `dtype`: "data type"
- `float32`: Số thập phân 32-bit (tiết kiệm memory hơn `float64`)

### **Ví Dụ Cụ Thể:**

**Input:**
```python
chunks = [
    TextChunk(text="Nội dung 1", page_number=1, chunk_index=1),
    TextChunk(text="Nội dung 2", page_number=1, chunk_index=2),
]
```

**Xử lý:**
```
1. chunk_list = list(chunks)
   → [TextChunk1, TextChunk2]

2. texts = ["Nội dung 1", "Nội dung 2"]

3. embeddings = model.encode(texts)
   → [
       [0.1, 0.2, 0.3, ..., 0.768],  (768 số cho chunk 1)
       [0.4, 0.5, 0.6, ..., 0.768],  (768 số cho chunk 2)
     ]

4. zip(chunks, embeddings)
   → [(chunk1, vec1), (chunk2, vec2)]

5. Tạo EmbeddingResult cho mỗi cặp
```

**Output:**
```python
[
    EmbeddingResult(
        chunk=TextChunk(text="Nội dung 1", page_number=1, chunk_index=1),
        vector=np.array([0.1, 0.2, 0.3, ..., 0.768])
    ),
    EmbeddingResult(
        chunk=TextChunk(text="Nội dung 2", page_number=1, chunk_index=2),
        vector=np.array([0.4, 0.5, 0.6, ..., 0.768])
    ),
]
```

### **Tóm Tắt Hàm `embed_chunks()`**

```
INPUT: Chuỗi TextChunk
  ↓
1. Chuyển thành List
2. Kiểm tra không rỗng
3. Load model
4. Trích tất cả texts: ["text1", "text2", ...]
5. Sinh embedding bằng model.encode()
6. Ghép chunks + vectors bằng zip()
7. Tạo EmbeddingResult cho mỗi cặp
  ↓
OUTPUT: Danh sách EmbeddingResult
```

---

## 📊 BẢNG TÓMLỖI 3 FILE

| File | Mục Đích | Input | Output |
|-----|---------|-------|--------|
| **`text_extractor.py`** | Đọc PDF | File path | Chuỗi DocumentChunk (mỗi trang) |
| **`chunker.py`** | Chia chunks | Chuỗi DocumentChunk | Danh sách TextChunk (nhỏ hơn) |
| **`embedder.py`** | Sinh embedding | Chuỗi TextChunk | Danh sách EmbeddingResult (text + vector) |

---

## 💡 CÁC CÚ PHÁP PYTHON CẦN BIẾT

| Cú Pháp | Ý Nghĩa | Ví Dụ |
|--------|--------|-------|
| `class X(Y):` | Kế thừa | `class TextChunk(DocumentChunk):` |
| `super().__init__()` | Gọi __init__ lớp cha | `super().__init__(text=text)` |
| `yield` | Trả về từng phần tử (generator) | `yield DocumentChunk(...)` |
| `enumerate(iterable, start=N)` | Lặp với chỉ số từ N | `for idx, item in enumerate(..., start=1):` |
| `str.replace(old, new)` | Thay thế chuỗi | `text.replace("\x00", "")` |
| `str.strip()` | Xoá khoảng trắng đầu/cuối | `text.strip()` |
| `if not x:` | Nếu x là False/None/rỗng | `if not text: continue` |
| `or default` | Hoặc giá trị mặc định | `text = None or ""` |
| `for x in y: ...` | Vòng lặp | `for chunk in chunks:` |
| `[expr for x in y]` | List comprehension | `[chunk.text for chunk in chunks]` |
| `global var` | Cho phép sửa biến global | `global _model` |
| `zip(list1, list2)` | Ghép 2 danh sách | `for x, y in zip(a, b):` |
| `np.ndarray` | Numpy array | `vector: np.ndarray` |
| `np.array(list, dtype=...)` | Tạo numpy array | `np.array([0.1, 0.2], dtype=np.float32)` |

---

Bạn đã hiểu rõ 3 file này chưa? Có phần nào cần giải thích thêm không?
