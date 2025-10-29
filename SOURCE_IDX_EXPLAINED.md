# 🔍 Giải Thích: source_idx và Enumerate

## ❓ Câu Hỏi
> "for source_idx, chunk in enumerate(chunks): - dòng này mỗi source_idx tương đương với 1 trang đúng không?"

## ✅ Trả Lời: **ĐÚNG 100%!**

---

## 📝 Giải Thích Chi Tiết

### Dòng Code:
```python
for source_idx, chunk in enumerate(chunks):
```

### Breakdown:

```python
chunks = [
    DocumentChunk(text="Trang 1", page_number=1),     # ← source_idx = 0
    DocumentChunk(text="Trang 2", page_number=2),     # ← source_idx = 1
    DocumentChunk(text="Trang 3", page_number=3),     # ← source_idx = 2
]

# enumerate(chunks) tạo ra:
[
    (0, DocumentChunk(text="Trang 1", page_number=1)),
    (1, DocumentChunk(text="Trang 2", page_number=2)),
    (2, DocumentChunk(text="Trang 3", page_number=3)),
]
```

---

## 🎬 Loop Visualization

### Iteration 1:
```python
source_idx = 0
chunk = DocumentChunk(text="Trang 1", page_number=1)
```

### Iteration 2:
```python
source_idx = 1
chunk = DocumentChunk(text="Trang 2", page_number=2)
```

### Iteration 3:
```python
source_idx = 2
chunk = DocumentChunk(text="Trang 3", page_number=3)
```

---

## 📊 Bảng So Sánh: source_idx vs chunk

| Iteration | source_idx | chunk | page_number | Ý Nghĩa |
|-----------|-----------|-------|------------|---------|
| 1 | 0 | Trang 1 | 1 | Trang thứ 1 |
| 2 | 1 | Trang 2 | 2 | Trang thứ 2 |
| 3 | 2 | Trang 3 | 3 | Trang thứ 3 |

---

## 💡 Khác Biệt: source_idx vs page_number

### `source_idx`:
- **0-based** (bắt đầu từ 0)
- **Vị trí trong danh sách** chunks
- `source_idx = 0` → trang thứ 1
- `source_idx = 1` → trang thứ 2

### `page_number`:
- **1-based** (bắt đầu từ 1)
- **Số trang thực tế** trong PDF
- `page_number = 1` → trang thứ 1
- `page_number = 2` → trang thứ 2

### Ví Dụ:
```python
# Nếu file PDF có 3 trang:
chunks = [
    DocumentChunk(text="...", page_number=1),
    DocumentChunk(text="...", page_number=2),
    DocumentChunk(text="...", page_number=3),
]

# Loop:
for source_idx, chunk in enumerate(chunks):
    print(f"source_idx={source_idx}, page_number={chunk.page_number}")

# Output:
# source_idx=0, page_number=1
# source_idx=1, page_number=2
# source_idx=2, page_number=3
```

---

## 🎯 Tại Sao Cần source_idx?

### Trong Code Hiện Tại (chunker.py):

```python
for source_idx, chunk in enumerate(chunks):
    pieces = _splitter.split_text(chunk.text)
    for piece_idx, piece in enumerate(pieces):
        text = piece.strip()
        if not text:
            continue
        output.append(
            TextChunk(
                text=text,
                page_number=chunk.page_number,      # ← Dùng page_number từ chunk
                chunk_index=len(output) + 1,       # ← Dùng global index
            )
        )
```

**`source_idx` không được sử dụng** (dòng này có thể viết lại):

```python
for chunk in chunks:  # Bỏ source_idx nếu không dùng
    pieces = _splitter.split_text(chunk.text)
    # ...
```

---

## 🔄 Ví Dụ Thực Tế: 3 Trang

### Input: PDF có 3 trang

```
Trang 1: "LangChain là framework..." (500 ký tự)
Trang 2: "Embedding là biểu diễn..." (1500 ký tự)
Trang 3: "Supabase là database..." (800 ký tự)
```

### text_extractor.py Output:

```python
chunks = [
    DocumentChunk(text="LangChain là framework...", page_number=1),
    DocumentChunk(text="Embedding là biểu diễn...", page_number=2),
    DocumentChunk(text="Supabase là database...", page_number=3),
]
```

### chunker.py - Loop chi tiết:

```python
# Iteration 1:
source_idx = 0
chunk = DocumentChunk(text="LangChain là framework...", page_number=1)
pieces = _splitter.split_text("LangChain là framework...")
# Trang 1 có 500 ký tự < 900 → pieces = [1 phần]
# Tạo: TextChunk(..., page_number=1, chunk_index=1)

# Iteration 2:
source_idx = 1
chunk = DocumentChunk(text="Embedding là biểu diễn...", page_number=2)
pieces = _splitter.split_text("Embedding là biểu diễn...")
# Trang 2 có 1500 ký tự > 900 → pieces = [2 phần]
# Tạo: TextChunk(..., page_number=2, chunk_index=2)
# Tạo: TextChunk(..., page_number=2, chunk_index=3)

# Iteration 3:
source_idx = 2
chunk = DocumentChunk(text="Supabase là database...", page_number=3)
pieces = _splitter.split_text("Supabase là database...")
# Trang 3 có 800 ký tự < 900 → pieces = [1 phần]
# Tạo: TextChunk(..., page_number=3, chunk_index=4)
```

### Final Output:

```python
[
    TextChunk(..., page_number=1, chunk_index=1),
    TextChunk(..., page_number=2, chunk_index=2),
    TextChunk(..., page_number=2, chunk_index=3),
    TextChunk(..., page_number=3, chunk_index=4),
]
```

---

## 🎯 Để Nhớ

| Biến | Giá Trị | Ý Nghĩa | 0-based hay 1-based |
|------|--------|--------|-------------------|
| `source_idx` | 0, 1, 2, ... | Vị trí trong danh sách chunks | **0-based** |
| `chunk` | DocumentChunk object | Dữ liệu trang | N/A |
| `page_number` | 1, 2, 3, ... | Số trang thực tế | **1-based** |

---

## 💡 Thêm Một Cách Hiểu

**`enumerate(chunks)` = "Đánh số từng phần tử"**

```python
chunks = ["Trang 1", "Trang 2", "Trang 3"]

for source_idx, chunk in enumerate(chunks):
    print(f"{source_idx}: {chunk}")

# Output:
# 0: Trang 1
# 1: Trang 2
# 2: Trang 3
```

**So Sánh:**

```python
# Cách 1: Dùng enumerate (hiện tại)
for source_idx, chunk in enumerate(chunks):
    print(f"source_idx={source_idx}, chunk={chunk}")

# Cách 2: Dùng range + len (cũ hơn)
for source_idx in range(len(chunks)):
    chunk = chunks[source_idx]
    print(f"source_idx={source_idx}, chunk={chunk}")

# Cách 3: Không cần index (nếu không dùng)
for chunk in chunks:
    print(f"chunk={chunk}")
```

---

## ✅ Kết Luận

✅ **`source_idx` tương đương với vị trí trang trong danh sách (0-based)**
- `source_idx = 0` → Trang 1
- `source_idx = 1` → Trang 2
- `source_idx = 2` → Trang 3

✅ **`page_number` trong chunk là số trang thực tế (1-based)**
- `page_number = 1` → Trang 1
- `page_number = 2` → Trang 2
- `page_number = 3` → Trang 3

✅ **Trong code hiện tại, `source_idx` không được dùng** (có thể bỏ)
- Chỉ cần dùng `chunk` và `chunk.page_number`

**Bạn hiểu đúng rồi!** 🎉
