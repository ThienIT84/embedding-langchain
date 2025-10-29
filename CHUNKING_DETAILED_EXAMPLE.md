# 🔪 Giải Thích Chi Tiết: Cách Chia Chunk Một Trang

## Mục Tiêu
File **chunker.py** lấy một trang PDF dài (ví dụ 5000 ký tự) và chia thành nhiều **chunk nhỏ** (mỗi chunk ~900 ký tự theo config).

---

## 📊 Ví Dụ Cụ Thể

### 1. INPUT: Một trang từ text_extractor.py

Giả sử `text_extractor.py` đã đọc **Trang 5** của PDF, extract được text như sau:

```
Trang 5:
"LangChain là một framework giúp xây dựng ứng dụng AI. 
Nó cung cấp các công cụ để làm việc với LLM (Large Language Models).

RecursiveCharacterTextSplitter là một công cụ của LangChain dùng để chia văn bản thành các đoạn nhỏ.

Cách hoạt động:
1. Đầu tiên, nó cố gắng chia theo '\n\n' (2 dòng trống)
2. Nếu đoạn vẫn quá dài, chia theo '\n' (1 dòng)
3. Nếu vẫn quá dài, chia theo ' ' (khoảng trắng)
4. Nếu còn quá dài, chia từng ký tự

Overlap (chồng lấp) = 200 ký tự: mỗi chunk mới sẽ có 200 ký tự cuối của chunk trước."
```

**Thống kê:**
- Trang: 5
- Độ dài: ~650 ký tự
- Là: 1 `DocumentChunk` từ `text_extractor.py`

---

### 2. CONFIG: Cài đặt chia chunk

Từ `.env`:
```
CHUNK_SIZE=900
CHUNK_OVERLAP=200
```

Trong `chunker.py`:
```python
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,           # Mỗi chunk tối đa 900 ký tự
    chunk_overlap=200,        # Overlap 200 ký tự giữa các chunk
    separators=["\n\n", "\n", " ", ""]  # Thứ tự ưu tiên chia
)
```

---

### 3. PROCESS: Quá trình chia chunk

#### Step 1: Gọi hàm `split_chunks()`

```python
# Text trang 5 (650 ký tự)
page_5_chunk = DocumentChunk(
    text="LangChain là một framework...",
    page_number=5
)

# Gọi hàm
result = split_chunks([page_5_chunk])  # Pass iterable có 1 phần tử
```

#### Step 2: Vòng lặp ngoài - `for source_idx, chunk in enumerate(chunks)`

```python
for source_idx, chunk in enumerate(chunks):  # source_idx = 0
    # chunk = DocumentChunk(text="LangChain là...", page_number=5)
    
    pieces = _splitter.split_text(chunk.text)
    # Gọi RecursiveCharacterTextSplitter.split_text()
```

**RecursiveCharacterTextSplitter làm gì?**

Input: 
```
"LangChain là một framework...[650 ký tự]...chia từng ký tự"
```

Output: Vì 650 < 900, nên **không cần chia**:
```python
pieces = [
    "LangChain là một framework giúp xây dựng ứng dụng AI. Nó cung cấp các công cụ để làm việc với LLM (Large Language Models).\n\nRecursiveCharacterTextSplitter là một công cụ của LangChain dùng để chia văn bản thành các đoạn nhỏ.\n\nCách hoạt động:\n1. Đầu tiên, nó cố gắng chia theo '\n\n' (2 dòng trống)\n2. Nếu đoạn vẫn quá dài, chia theo '\n' (1 dòng)\n3. Nếu vẫn quá dài, chia theo ' ' (khoảng trắng)\n4. Nếu còn quá dài, chia từng ký tự\n\nOverlap (chồng lấp) = 200 ký tự: mỗi chunk mới sẽ có 200 ký tự cuối của chunk trước."
]
# pieces có 1 phần tử (vì text < 900 ký tự)
```

#### Step 3: Vòng lặp trong - `for piece_idx, piece in enumerate(pieces)`

```python
for piece_idx, piece in enumerate(pieces):  # piece_idx = 0
    text = piece.strip()  # Xóa khoảng trắng đầu/cuối
    
    if not text:  # Nếu text rỗng thì bỏ qua
        continue
    
    # Nếu text không rỗng, thêm vào output
    output.append(
        TextChunk(
            text=text,
            page_number=chunk.page_number,  # = 5
            chunk_index=len(output) + 1,    # = 0 + 1 = 1
        )
    )
```

#### Step 4: OUTPUT

```python
output = [
    TextChunk(
        text="LangChain là một framework...",
        page_number=5,
        chunk_index=1  # Đây là chunk thứ 1 trong toàn bộ output
    )
]

return output
```

---

## 🔴 Ví Dụ 2: Trang Dài Cần Chia Nhiều Lần

### INPUT: Trang 10 có 3000 ký tự

```
Trang 10:
"LangChain cung cấp nhiều thành phần... [3000 ký tự]... ứng dụng AI hiệu quả"
```

### PROCESS:

**RecursiveCharacterTextSplitter.split_text()** sẽ:
1. Chia theo `"\n\n"` (paragraph)
2. Nếu paragraphs vẫn > 900, chia tiếp theo `"\n"` (dòng)
3. Nếu vẫn quá dài, chia theo `" "` (từ)
4. Nếu còn quá dài, chia từng ký tự

**Result:**
```python
pieces = [
    "LangChain cung cấp nhiều thành phần...[900 ký tự]...",           # Chunk 1
    "[200 overlap ký tự từ chunk 1]...LangChain hỗ trợ...[900 ký tự]",  # Chunk 2
    "[200 overlap ký tự từ chunk 2]...ứng dụng AI hiệu quả"           # Chunk 3
]
# pieces có 3 phần tử
```

### LOOP:

```python
# Iteration 1: piece_idx = 0
output.append(TextChunk(
    text="LangChain cung cấp...",
    page_number=10,
    chunk_index=1  # len(output=0) + 1
))

# Iteration 2: piece_idx = 1
output.append(TextChunk(
    text="[200 overlap]...LangChain hỗ trợ...",
    page_number=10,
    chunk_index=2  # len(output=1) + 1
))

# Iteration 3: piece_idx = 2
output.append(TextChunk(
    text="[200 overlap]...ứng dụng AI hiệu quả",
    page_number=10,
    chunk_index=3  # len(output=2) + 1
))
```

### OUTPUT:

```python
[
    TextChunk(text="...", page_number=10, chunk_index=1),
    TextChunk(text="...", page_number=10, chunk_index=2),
    TextChunk(text="...", page_number=10, chunk_index=3),
]
```

---

## 🧮 Hiểu Rõ Các Biến

### `chunk_index = len(output) + 1`

**Tại sao dùng `len(output) + 1`?**

```python
output = []

# Thêm chunk 1
output.append(TextChunk(..., chunk_index=len(output) + 1))  # len=0, chunk_index=1

# Thêm chunk 2
output.append(TextChunk(..., chunk_index=len(output) + 1))  # len=1, chunk_index=2

# Thêm chunk 3
output.append(TextChunk(..., chunk_index=len(output) + 1))  # len=2, chunk_index=3
```

**Result:**
```python
output = [
    TextChunk(..., chunk_index=1),  # position 0, chunk_index 1
    TextChunk(..., chunk_index=2),  # position 1, chunk_index 2
    TextChunk(..., chunk_index=3),  # position 2, chunk_index 3
]
```

**Ý nghĩa:**
- `chunk_index` = số thứ tự chunk (bắt đầu từ 1, không phải 0)
- Là **global index** (tính trên toàn bộ document, không riêng từng trang)

---

### `piece.strip()`

```python
piece = "   LangChain là framework   \n"
text = piece.strip()  # Xóa khoảng trắng + \n đầu/cuối
# text = "LangChain là framework"
```

**Các hàm .strip() tương tự:**
- `.strip()` - xóa đầu + cuối
- `.lstrip()` - xóa đầu
- `.rstrip()` - xóa cuối

---

### `if not text: continue`

```python
if not text:  # Nếu text rỗng
    continue  # Bỏ qua, không add vào output

# Ví dụ:
piece = "   \n   "
text = piece.strip()  # ""
if not text:  # True
    continue  # Bỏ qua phần tử này
```

---

## 📈 Sơ Đồ Quá Trình

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Iterable[DocumentChunk] (từ text_extractor.py)          │
│ Trang 5: 650 ký tự                                              │
│ Trang 10: 3000 ký tự                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  for chunk in... │
                    └──────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
    Trang 5           RecursiveCharacterTextSplitter    Trang 10
    650 ký tự         (split_text)                     3000 ký tự
        │                     │                         │
        ▼                     ▼                         ▼
   pieces = [1 item]       pieces = [1 item]         pieces = [3 items]
   (650 < 900)             (650 < 900)               (3000 > 900)
        │                     │                         │
        ▼                     ▼                         ▼
    ┌──────────────────────────────────────────────────────┐
    │  for piece in pieces:                               │
    │    text = piece.strip()                             │
    │    if not text: continue                            │
    │    output.append(TextChunk(..., chunk_index=N))    │
    └──────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: List[TextChunk]                                        │
│ [                                                               │
│   TextChunk(..., chunk_index=1),  # Trang 5                    │
│   TextChunk(..., chunk_index=2),  # Trang 10, phần 1           │
│   TextChunk(..., chunk_index=3),  # Trang 10, phần 2           │
│   TextChunk(..., chunk_index=4),  # Trang 10, phần 3           │
│ ]                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Points - Những Điểm Quan Trọng

| Khái Niệm | Ý Nghĩa |
|-----------|--------|
| **chunk_size=900** | Mỗi chunk tối đa 900 ký tự |
| **chunk_overlap=200** | Chunk tiếp theo bắt đầu 200 ký tự từ cuối chunk trước |
| **separators** | Ưu tiên chia: paragraph → dòng → từ → ký tự |
| **for chunk in chunks** | Vòng lặp qua từng trang/phần từ text_extractor |
| **pieces = _splitter.split_text(...)** | Thực hiện việc chia |
| **for piece in pieces** | Vòng lặp qua từng đoạn sau khi chia |
| **chunk_index = len(output) + 1** | Số thứ tự chunk (1-based) |
| **.strip()** | Xóa khoảng trắng và newline đầu/cuối |
| **if not text: continue** | Bỏ qua các chunk trống |

---

## 💡 Tại Sao Cần Chunk?

1. **LLM token limit**: Model AI chỉ có thể xử lý tối đa ~4096 token. Văn bản quá dài phải chia nhỏ.
2. **Embedding model input**: SentenceTransformer cũng có giới hạn độ dài.
3. **Similarity search tốt hơn**: Chunk nhỏ → tìm kiếm chính xác hơn (khi user hỏi câu hỏi, sẽ match được chunk đúng).

---

## 🎯 Tóm Lại

**Chunker làm công việc sau:**

1. **Nhận input**: Mỗi trang từ text_extractor (một DocumentChunk)
2. **Chia nhỏ**: Dùng RecursiveCharacterTextSplitter chia theo mục (nhất) → dòng → từ → ký tự
3. **Add vào output**: Mỗi đoạn trở thành TextChunk với:
   - `text`: nội dung
   - `page_number`: số trang gốc
   - `chunk_index`: số thứ tự global
4. **Return**: List[TextChunk] - tất cả chunks từ toàn bộ document

**Kết quả:** Một document 10 trang có thể trở thành 50-100 chunks nhỏ, mỗi chunk ~900 ký tự, sẵn sàng cho embedding.

---

## 🎬 Flow Hoàn Chỉnh

```
PDF File
    │
    ▼
[text_extractor.py] → Iterable[DocumentChunk]
    (Mỗi trang = 1 chunk)
    │
    ▼
[chunker.py] → List[TextChunk]
    (Mỗi chunk trang được chia thành nhiều chunks nhỏ)
    │
    ▼
[embedder.py] → List[EmbeddingResult]
    (Mỗi chunk có embedding vector 768 chiều)
    │
    ▼
[pipeline.py → supabase_client.py] → Supabase DB
    (Lưu trữ)
```
