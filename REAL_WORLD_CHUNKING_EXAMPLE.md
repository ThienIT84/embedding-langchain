# 🎯 Real-World Example: Trang 1 Có 1000 Từ

## ❓ Câu Hỏi
> "Nếu trang 1 có 1000 từ (khoảng 6000 ký tự) thì nó vẫn chia trang 1 thành 2 chunk, với `page_number=1` và `chunk_index` 2 gồm 100 từ đúng không?"

## ✅ Trả Lời: **ĐÚNG 100%!**

---

## 📝 Setup

```python
# .env config
CHUNK_SIZE=900
CHUNK_OVERLAP=200
```

```python
# chunker.py config
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,           # Mỗi chunk tối đa 900 ký tự
    chunk_overlap=200,        # Overlap 200 ký tự
    separators=["\n\n", "\n", " ", ""],
)
```

---

## 🎬 Scenario: Trang 1 Có 1000 Từ

### INPUT: Text Trang 1

```
Text Trang 1:
"LangChain là một framework được thiết kế để giúp nhà phát triển xây dựng các ứng dụng
sử dụng Large Language Models (LLM). Framework này cung cấp một tập hợp các công cụ
và thư viện để tương tác với LLM một cách dễ dàng. 

Một trong những thành phần chính của LangChain là RecursiveCharacterTextSplitter.
Đây là một công cụ được sử dụng để chia văn bản thành các đoạn nhỏ hơn. Điều này 
rất quan trọng vì các LLM có giới hạn về số lượng tokens mà chúng có thể xử lý 
trong một lần gọi.

Khi bạn có một tài liệu dài như một bài báo hoặc một cuốn sách, bạn cần chia nó 
thành các phần nhỏ hơn. Mỗi phần này sẽ được chuyển đổi thành một embedding vector.
Embedding vector là một biểu diễn toán học của văn bản trong không gian đa chiều.

RecursiveCharacterTextSplitter hoạt động theo cách sau: đầu tiên, nó cố gắng chia 
văn bản theo các paragraph (chia theo '\\n\\n'). Nếu một paragraph vẫn còn quá dài,
nó sẽ chia tiếp theo các dòng (chia theo '\\n'). Nếu một dòng vẫn còn quá dài, nó 
sẽ chia theo các từ (chia theo ' '). Cuối cùng, nếu vẫn còn quá dài, nó sẽ chia 
từng ký tự một (chia theo '').

Quá trình overlap được áp dụng để đảm bảo rằng ngữ cảnh được giữ lại giữa các chunks.
Khi bạn tạo một chunk mới, 200 ký tự cuối cùng của chunk trước được thêm vào đầu 
của chunk hiện tại. Điều này giúp duy trì sự liên tục về ngữ cảnh.

[... (tiếp tục ~1000 từ tổng cộng = khoảng 6000 ký tự) ...]"

Tổng: ~1000 từ = ~6000 ký tự
```

### Step 1: text_extractor.py Trích Xuất

```python
# text_extractor.py: PdfReader đọc trang 1
chunk = DocumentChunk(
    text="LangChain là một framework...[6000 ký tự]...",
    page_number=1
)
```

---

### Step 2: chunker.py - Gọi `split_chunks()`

```python
# Input
chunks_input = [chunk]  # 1 phần tử: DocumentChunk(text=..., page_number=1)

# Gọi hàm
result = split_chunks(chunks_input)
```

---

### Step 3: RecursiveCharacterTextSplitter.split_text()

**Kiểm tra kích thước:**
```python
text_length = len(chunk.text)  # 6000 ký tự
chunk_size = 900

if text_length >= 900:  # 6000 >= 900 → TRUE
    # Cần chia!
    pieces = _splitter.split_text(chunk.text)
```

**Quá trình chia (Recursive):**

```
Bước 1: Tìm "\n\n" (paragraph)
├─ Tìm thấy 3 paragraphs
├─ Para 1: ~1500 ký tự (>= 900) → Chia tiếp
├─ Para 2: ~2000 ký tự (>= 900) → Chia tiếp
└─ Para 3: ~2500 ký tự (>= 900) → Chia tiếp

Bước 2: Chia mỗi paragraph theo "\n" (dòng)
├─ Para 1 chia thành: dòng 1a (800), dòng 1b (700)
├─ Para 2 chia thành: dòng 2a (900), dòng 2b (1100) → Vẫn quá dài!
└─ Para 3 chia thành: dòng 3a (850), dòng 3b (1650) → Vẫn quá dài!

Bước 3: Chia những phần vẫn >= 900 theo " " (từ)
├─ Dòng 2b (1100) chia thành: chunk 2b1 (850), chunk 2b2 (250)
└─ Dòng 3b (1650) chia thành: chunk 3b1 (900), chunk 3b2 (750)

Final pieces:
[
    "LangChain là...dòng 1a" (800 ký tự),
    "[200 overlap]...dòng 1b" (800 ký tự),
    "[200 overlap]...chunk 2a" (900 ký tự),
    "[200 overlap]...chunk 2b1" (850 ký tự),
    "[200 overlap]...chunk 2b2" (250 ký tự),
    "[200 overlap]...chunk 3a" (850 ký tự),
    "[200 overlap]...chunk 3b1" (900 ký tự),
    "[200 overlap]...chunk 3b2" (750 ký tự),
]
```

**Kết quả: 8 pieces** (không phải 2! Nhưng nếu trang chỉ có 1000 từ/~6000 ký tự, sẽ ít hơn)

---

### Step 4: Vòng Lặp Trong split_chunks()

```python
def split_chunks(chunks: Iterable[DocumentChunk]) -> List[TextChunk]:
    output: List[TextChunk] = []
    
    # Vòng lặp ngoài: for chunk in chunks
    for source_idx, chunk in enumerate(chunks):  # source_idx=0, chunk là trang 1
        pieces = _splitter.split_text(chunk.text)  # pieces = [piece1, piece2, ...]
        
        # Vòng lặp trong: for piece in pieces
        for piece_idx, piece in enumerate(pieces):  # piece_idx=0,1,2,...
            text = piece.strip()
            
            if not text:  # Bỏ qua phần trống
                continue
            
            output.append(
                TextChunk(
                    text=text,
                    page_number=chunk.page_number,      # = 1 (luôn là 1!)
                    chunk_index=len(output) + 1,        # = 1, 2, 3, ...
                )
            )
    
    return output
```

---

### Step 5: Loop Detail - Duyệt Từng Piece

```python
# Iteration 1: piece_idx=0
piece = pieces[0]  # "LangChain là...dòng 1a" (800 ký tự)
text = piece.strip()  # "LangChain là...dòng 1a"
if not text:  # False (có text)
    continue

output.append(TextChunk(
    text="LangChain là...dòng 1a",
    page_number=1,                    # 👈 page_number luôn là 1
    chunk_index=len(output) + 1,      # len(output)=0, chunk_index=1
))
# output = [TextChunk(..., page_number=1, chunk_index=1)]

# Iteration 2: piece_idx=1
piece = pieces[1]  # "[200 overlap]...dòng 1b" (800 ký tự)
text = piece.strip()
if not text:  # False
    continue

output.append(TextChunk(
    text="[200 overlap]...dòng 1b",
    page_number=1,                    # 👈 page_number luôn là 1
    chunk_index=len(output) + 1,      # len(output)=1, chunk_index=2
))
# output = [TextChunk(..., page_number=1, chunk_index=1), TextChunk(..., page_number=1, chunk_index=2)]

# Iteration 3: piece_idx=2
piece = pieces[2]  # "[200 overlap]...chunk 2a"
text = piece.strip()
if not text:  # False
    continue

output.append(TextChunk(
    text="[200 overlap]...chunk 2a",
    page_number=1,                    # 👈 page_number luôn là 1
    chunk_index=len(output) + 1,      # len(output)=2, chunk_index=3
))

# ... (tiếp tục với iteration 4, 5, 6, 7, 8 ...)

# Iteration 8: piece_idx=7
piece = pieces[7]  # "[200 overlap]...chunk 3b2" (750 ký tự)
text = piece.strip()
if not text:  # False
    continue

output.append(TextChunk(
    text="[200 overlap]...chunk 3b2",
    page_number=1,                    # 👈 page_number luôn là 1
    chunk_index=len(output) + 1,      # len(output)=7, chunk_index=8
))
```

---

## 📊 FINAL OUTPUT

```python
[
    TextChunk(
        text="LangChain là...dòng 1a",
        page_number=1,
        chunk_index=1
    ),
    TextChunk(
        text="[200 overlap]...dòng 1b",
        page_number=1,
        chunk_index=2  # ✅ ĐÚng! Vẫn page_number=1
    ),
    TextChunk(
        text="[200 overlap]...chunk 2a",
        page_number=1,
        chunk_index=3
    ),
    TextChunk(
        text="[200 overlap]...chunk 2b1",
        page_number=1,
        chunk_index=4
    ),
    TextChunk(
        text="[200 overlap]...chunk 2b2",
        page_number=1,
        chunk_index=5
    ),
    TextChunk(
        text="[200 overlap]...chunk 3a",
        page_number=1,
        chunk_index=6
    ),
    TextChunk(
        text="[200 overlap]...chunk 3b1",
        page_number=1,
        chunk_index=7
    ),
    TextChunk(
        text="[200 overlap]...chunk 3b2",
        page_number=1,
        chunk_index=8
    ),
]
```

---

## 🎯 Câu Trả Lời Chi Tiết

### Q: "Nếu trang 1 có 1000 từ (6000 ký tự) thì nó vẫn chia trang 1 thành 2 chunk, với `page_number=1` và `chunk_index=2` gồm 100 từ đúng không?"

### A: **GẦN ĐÚNG, nhưng chi tiết cần uốn cong:**

1. ✅ **Trang 1 vẫn được chia thành NHIỀU chunks** (không chỉ 2)
   - Nếu 6000 ký tự, sẽ chia thành ~6-8 chunks (tùy cấu trúc paragraph)

2. ✅ **Tất cả chunks vẫn có `page_number=1`**
   - Chunk 1, 2, 3, 4, ... đều có `page_number=1`
   - Vì chúng đều từ trang 1

3. ✅ **`chunk_index` tăng dần: 1, 2, 3, 4, ...**
   - Chunk thứ 2 có `chunk_index=2`
   - Chunk thứ 8 có `chunk_index=8`

4. ❓ **Chunk cuối cùng của trang 1 có `~100 từ`?**
   - **Có thể ĐÚNG!** Nếu 6000 ký tự / 8 chunks ≈ 750 ký tự/chunk
   - Chunk cuối cùng có thể < 900 ký tự, ví dụ 100-200 từ

---

## 📌 Visualize Flow

```
┌─ PDF Trang 1 ─────────────────────────────────────┐
│ 1000 từ = 6000 ký tự                              │
│ (có 3 paragraphs, nhiều dòng)                      │
└──────────────────────────────────────────────────┘
                    │
                    ▼
      ┌────────────────────────┐
      │ text_extractor.py      │
      │ extract_pdf_text()     │
      │ →DocumentChunk         │
      │ (text, page_number=1)  │
      └────────────────────────┘
                    │
                    ▼
      ┌────────────────────────┐
      │ chunker.py             │
      │ split_chunks()         │
      │ RecursiveCharacterText │
      │ Splitter.split_text()  │
      │ → pieces (8 phần)      │
      └────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────┐
    │ Loop: for piece in pieces        │
    │ ├─ Chunk 1 (900 ký tự, 150 từ)  │
    │ ├─ Chunk 2 (900 ký tự, 150 từ)  │
    │ ├─ Chunk 3 (900 ký tự, 150 từ)  │
    │ ├─ ...                           │
    │ └─ Chunk 8 (600 ký tự, 100 từ)  │
    │                                  │
    │ ALL: page_number=1               │
    │ ALL: chunk_index=1,2,3,...,8     │
    └──────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────┐
    │ OUTPUT: List[TextChunk]          │
    │ 8 chunks, tất cả trang 1         │
    └──────────────────────────────────┘
                    │
                    ▼
      ┌────────────────────────┐
      │ embedder.py            │
      │ embed_chunks()         │
      │ → 8 embeddings 768-dim │
      └────────────────────────┘
                    │
                    ▼
      ┌────────────────────────┐
      │ Supabase DB            │
      │ (8 rows)               │
      └────────────────────────┘
```

---

## 🔄 Bảng So Sánh: Trang 1 vs Trang 2

| Đặc Tính | Trang 1 (6000 ký tự) | Trang 2 (2000 ký tự) |
|----------|-----|-----|
| Số chunks | 8 | 2-3 |
| `page_number` | 1, 1, 1, 1, 1, 1, 1, 1 | 2, 2, 2 |
| `chunk_index` | 1, 2, 3, 4, 5, 6, 7, 8 | 9, 10, 11 |
| Ký tự/chunk | ~750 | ~700-900 |
| Từ/chunk | ~125 | ~120-150 |

**Khi xử lý Trang 2:**
```python
# Trang 2 cũng được xử lý tương tự
for chunk in chunks:  # chunk từ trang 2
    pieces = _splitter.split_text(chunk.text)  # chia thành 2-3 pieces
    
    for piece in pieces:
        output.append(TextChunk(
            text=piece,
            page_number=2,               # 👈 page_number=2
            chunk_index=len(output)+1,   # 👈 chunk_index tiếp tục tăng: 9, 10, 11
        ))
```

---

## 💡 Kết Luận

✅ **Bạn đã hiểu ĐÚNG:**
- Trang 1 chia thành NHIỀU chunks (mỗi chunk ~900 ký tự)
- Tất cả chunks đều có `page_number=1`
- `chunk_index` tăng dần (1, 2, 3, ...)
- Chunk cuối cùng của trang 1 có thể < 900 ký tự (ví dụ 100-200 từ)

**Đó chính là cách chunker hoạt động!** 🎉
