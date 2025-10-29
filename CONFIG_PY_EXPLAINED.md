# 🔌 FILE 5: `src/config.py` - CẤU HÌNH TOÀN CỤC

## 📌 Mục Đích File

File này **đọc các biến môi trường** từ file `.env`, xử lý giá trị mặc định, và expose một **Settings object** duy nhất (singleton pattern) để dùng chung toàn ứng dụng.

**Analogy:** Giống như bạn có một "file cấu hình chính" (settings.ini) và Python tự động đọc nó khi khởi động.

---

## 🔍 PHẦN 1: IMPORT

```python
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv
```

| Import | Tác Dụng |
|--------|---------|
| `dataclass` | Decorator để tạo class với `__init__` tự động |
| `Path` | Làm việc với đường dẫn file (object-oriented) |
| `os` | Để truy cập biến môi trường |
| `load_dotenv` | Đọc file `.env` vào `os.environ` |

---

## 🔍 PHẦN 2: `load_dotenv()`

```python
load_dotenv()
```

### **Cú Pháp Giải Thích:**

#### **`load_dotenv()` là gì?**

| Phần | Ý Nghĩa |
|-----|--------|
| `load_dotenv()` | Hàm từ thư viện `python-dotenv` |
| **Tác dụng** | Đọc file `.env` và thêm các biến vào `os.environ` |

**Quy trình:**

```
1. Tìm file ".env" trong thư mục hiện tại
2. Đọc các dòng: KEY=VALUE
3. Thêm vào os.environ
4. Bây giờ os.getenv("KEY") hoạt động
```

**Ví dụ file `.env`:**
```
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
CHUNK_SIZE=900
TEMP_DIR=tmp
```

**Sau `load_dotenv()`:**
```python
os.getenv("SUPABASE_URL")  # "https://xyz.supabase.co"
os.getenv("CHUNK_SIZE")    # "900" (string!)
```

**Tại sao dùng `.env`?**
- Không hardcode credential trong code
- Dễ thay đổi cấu hình mà không sửa code
- An toàn (có thể .gitignore file này)

---

## 🔍 PHẦN 3: HÀM `_get_env()`

```python
def _get_env(name: str, default: str | None = None, required: bool = True) -> str:
    """Đọc biến môi trường, cho phép giá trị mặc định và đánh dấu bắt buộc."""
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value if value is not None else ""
```

### **Cú Pháp Giải Thích:**

#### **Dòng 1: `def _get_env(name: str, default: str | None = None, required: bool = True) -> str:`**

| Phần | Ý Nghĩa |
|-----|--------|
| `_get_env` | Tên hàm (dấu `_` = private, chỉ dùng trong file này) |
| `name: str` | Tên biến môi trường (ví dụ: "SUPABASE_URL") |
| `default: str \| None = None` | Giá trị mặc định nếu biến không tồn tại |
| `required: bool = True` | Có bắt buộc không? (nếu True, sẽ raise error nếu thiếu) |
| `-> str` | Trả về string |

#### **Dòng 2: `value = os.getenv(name, default)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `os.getenv(name, default)` | Lấy biến môi trường, dùng `default` nếu không có |

**Ví dụ:**
```python
# Nếu SUPABASE_URL tồn tại
os.getenv("SUPABASE_URL", "default_url")  # "https://xyz.supabase.co"

# Nếu SUPABASE_URL không tồn tại
os.getenv("SUPABASE_URL", "default_url")  # "default_url"

# Nếu không có default
os.getenv("SUPABASE_URL")  # None
```

#### **Dòng 3-4: Kiểm Tra Bắt Buộc**

```python
if required and not value:
    raise RuntimeError(f"Missing required environment variable: {name}")
```

| Phần | Ý Nghĩa |
|-----|--------|
| `required and not value` | Nếu bắt buộc AND giá trị trống |
| `raise RuntimeError(...)` | Ném lỗi (dừng chương trình) |

**Ví dụ:**
```python
# Trường hợp 1: Bắt buộc, nhưng không có
_get_env("SUPABASE_URL", required=True)  # ❌ RuntimeError!

# Trường hợp 2: Không bắt buộc, không có
_get_env("SUPABASE_URL", required=False)  # ✓ Trả về ""

# Trường hợp 3: Có giá trị mặc định
_get_env("SUPABASE_URL", default="default", required=True)  # ✓ "default"
```

#### **Dòng 5: `return value if value is not None else ""`**

| Phần | Ý Nghĩa |
|-----|--------|
| `value if condition else ""` | Ternary operator (ba ngôi) |
| `if value is not None` | Nếu value không phải None |
| `else ""` | Ngược lại trả về chuỗi rỗng |

**Ví dụ:**
```python
x = 10 if True else 5   # x = 10
x = 10 if False else 5  # x = 5
x = "hello" if "hello" is not None else ""  # x = "hello"
x = None if None is not None else ""  # x = ""
```

### **Tóm Tắt Hàm `_get_env()`**

```
INPUT: tên biến + giá trị mặc định + yêu cầu bắt buộc
  ↓
1. Đọc os.getenv(name, default)
2. Nếu bắt buộc mà không có → raise error
3. Nếu None → trả về ""
4. Ngược lại → trả về value
  ↓
OUTPUT: string (hoặc error)
```

**Ví dụ Sử Dụng:**

```python
# Bắt buộc (sẽ error nếu không có)
url = _get_env("SUPABASE_URL")

# Không bắt buộc (trả về giá trị mặc định)
bucket = _get_env("SUPABASE_BUCKET", "documents", required=False)

# Không bắt buộc (mặc định "" nếu không có)
token = _get_env("HF_API_TOKEN", required=False)
```

---

## 🔍 PHẦN 4: DECORATOR `@dataclass`

```python
@dataclass(frozen=True)
class Settings:
    ...
```

### **Cú Pháp Giải Thích:**

#### **`@dataclass` là gì?**

| Phần | Ý Nghĩa |
|-----|--------|
| `@` | Decorator (sửa đổi class) |
| `dataclass` | Từ module `dataclasses` |

**Decorator `@dataclass` tự động tạo gì?**

1. **`__init__` tự động**: Nhận tất cả attributes làm parameters
2. **`__repr__` tự động**: Cách hiển thị object (ví dụ: `Settings(url=..., key=...)`)
3. **`__eq__` tự động**: So sánh 2 objects

**Ví dụ:**

```python
# Không dùng @dataclass
class Settings:
    def __init__(self, url, key):
        self.url = url
        self.key = key
    
    def __repr__(self):
        return f"Settings(url={self.url}, key={self.key})"

# Dùng @dataclass (tự động)
@dataclass
class Settings:
    url: str
    key: str
```

**Kết quả giống nhau!**

#### **`frozen=True` là gì?**

| Phần | Ý Nghĩa |
|-----|--------|
| `frozen=True` | Làm class "bất biến" (immutable) |

**Bất biến = Không thể sửa đổi attribute:**

```python
settings = Settings(url="...", key="...")

# ✓ OK: Đọc
print(settings.url)

# ❌ ERROR: Sửa
settings.url = "new_url"  # FrozenInstanceError!
```

**Tại sao dùng `frozen=True`?**
- Tránh vô tình sửa cấu hình
- Settings là bất biến (từ đầu đến cuối chương trình)
- An toàn hơn

---

## 🔍 PHẦN 5: CLASS `Settings`

```python
@dataclass(frozen=True)
class Settings:
    supabase_url: str = _get_env("SUPABASE_URL")
    supabase_service_key: str = _get_env("SUPABASE_SERVICE_KEY")
    supabase_bucket: str = _get_env("SUPABASE_BUCKET", "documents")
    hf_model_name: str = _get_env(
        "HF_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2", required=False
    )
    hf_api_token: str = _get_env("HF_API_TOKEN", required=False)
    chunk_size: int = int(_get_env("CHUNK_SIZE", "900", required=False) or 900)
    chunk_overlap: int = int(_get_env("CHUNK_OVERLAP", "200", required=False) or 200)
    temp_dir: Path = Path(_get_env("TEMP_DIR", "tmp", required=False) or "tmp")
```

### **Các Attributes:**

#### **1. `supabase_url: str = _get_env("SUPABASE_URL")`**

| Phần | Ý Nghĩa |
|-----|--------|
| `supabase_url` | Tên attribute |
| `: str` | Type: string |
| `= _get_env("SUPABASE_URL")` | Giá trị mặc định (đọc từ .env) |

**Bắt buộc** (required=True mặc định)

**Ví dụ:**
```
File .env:
SUPABASE_URL=https://xyz.supabase.co

Code:
settings.supabase_url  # "https://xyz.supabase.co"
```

---

#### **2. `supabase_bucket: str = _get_env("SUPABASE_BUCKET", "documents")`**

- Không bắt buộc (có mặc định)
- Nếu không có trong `.env` → dùng `"documents"`

```
File .env (trường hợp 1):
SUPABASE_BUCKET=my_bucket

settings.supabase_bucket  # "my_bucket"

File .env (trường hợp 2 - không có):
# SUPABASE_BUCKET không tồn tại

settings.supabase_bucket  # "documents" (mặc định)
```

---

#### **3. `hf_model_name: str = _get_env(..., required=False)`**

- Không bắt buộc
- Có giá trị mặc định: `"sentence-transformers/paraphrase-multilingual-mpnet-base-v2"`

**Tại sao required=False?**
- User có thể chỉ định model khác trong `.env`
- Nếu không, dùng model mặc định

---

#### **4. `chunk_size: int = int(_get_env("CHUNK_SIZE", "900", required=False) or 900)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `_get_env("CHUNK_SIZE", "900", required=False)` | Đọc giá trị string |
| `or 900` | Nếu string rỗng → dùng 900 |
| `int(...)` | Chuyển string thành số nguyên |

**Breakdown:**

```python
# Nếu CHUNK_SIZE=1200 trong .env
_get_env("CHUNK_SIZE", ...) = "1200"  # string
"1200" or 900 = "1200"  # true (string khác rỗng)
int("1200") = 1200  # int

# Nếu CHUNK_SIZE không có
_get_env("CHUNK_SIZE", "900", ...) = "900"  # mặc định
"900" or 900 = "900"  # true
int("900") = 900  # int

# Nếu CHUNK_SIZE="" (rỗng)
_get_env("CHUNK_SIZE", "900", ...) = ""  # rỗng
"" or 900 = 900  # false (string rỗng), dùng 900
int(900) = 900  # int
```

**Tại sao `int()`?**
- `.env` là text, tất cả giá trị là string
- Cần chuyển thành int cho code logic

---

#### **5. `temp_dir: Path = Path(_get_env("TEMP_DIR", "tmp", required=False) or "tmp")`**

| Phần | Ý Nghĩa |
|-----|--------|
| `_get_env("TEMP_DIR", "tmp", ...)` | Đọc string từ .env |
| `or "tmp"` | Nếu rỗng → "tmp" |
| `Path(...)` | Chuyển string thành Path object |

**Tại sao `Path`?**
- Object-oriented cách để làm việc với đường dẫn
- Có các method hữu ích: `.mkdir()`, `.exists()`, `.name`, etc.

**Ví dụ:**
```python
temp_dir = Path("tmp")
temp_dir.mkdir(parents=True, exist_ok=True)  # Tạo folder
temp_dir.exists()  # Check có tồn tại
temp_dir / "file.txt"  # Kết hợp đường dẫn
```

---

## 🔍 PHẦN 6: INSTANTIATE & MKDIR

```python
settings = Settings()
settings.temp_dir.mkdir(parents=True, exist_ok=True)
```

### **Dòng 1: `settings = Settings()`**

- Tạo object `Settings` duy nhất (singleton pattern)
- Tất cả các attributes được khởi tạo từ `.env`

### **Dòng 2: `settings.temp_dir.mkdir(...)`**

| Phần | Ý Nghĩa |
|-----|--------|
| `.mkdir()` | Tạo folder |
| `parents=True` | Tạo folder cha nếu không tồn tại |
| `exist_ok=True` | Nếu folder đã tồn tại, không error |

**Ví dụ:**
```python
# temp_dir = "tmp/sub1/sub2"
# Tạo tất cả: tmp → sub1 → sub2
settings.temp_dir.mkdir(parents=True, exist_ok=True)
```

---

## 📊 BẢNG TÓM TẮT: Settings Attributes

| Attribute | Type | Bắt Buộc | Mặc Định | Nguồn |
|-----------|------|---------|---------|-------|
| `supabase_url` | str | ✅ Yes | - | .env |
| `supabase_service_key` | str | ✅ Yes | - | .env |
| `supabase_bucket` | str | ❌ No | `"documents"` | .env |
| `hf_model_name` | str | ❌ No | `"paraphrase-multilingual-mpnet-base-v2"` | .env |
| `hf_api_token` | str | ❌ No | `""` | .env |
| `chunk_size` | int | ❌ No | `900` | .env (convert to int) |
| `chunk_overlap` | int | ❌ No | `200` | .env (convert to int) |
| `temp_dir` | Path | ❌ No | `"tmp"` | .env (convert to Path) |

---

## 🎯 Cách Sử Dụng (Ở Các File Khác)

```python
# Ở chunker.py
from .config import settings

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,  # 900
    chunk_overlap=settings.chunk_overlap,  # 200
)

# Ở embedder.py
model = SentenceTransformer(settings.hf_model_name)

# Ở supabase_client.py
client = create_client(settings.supabase_url, settings.supabase_service_key)
```

---

## 💡 Các CÚ PHÁP PYTHON CẦN BIẾT

| Cú Pháp | Ý Nghĩa | Ví Dụ |
|--------|--------|-------|
| `@decorator` | Sửa đổi class/function | `@dataclass(frozen=True)` |
| `@dataclass` | Tạo `__init__`, `__repr__`, `__eq__` tự động | Tương tự namedtuple |
| `frozen=True` | Làm class immutable (không sửa được) | `@dataclass(frozen=True)` |
| `name: Type = default` | Attribute với type hint + mặc định | `chunk_size: int = 900` |
| `os.getenv(name, default)` | Lấy biến môi trường | `os.getenv("KEY", "default")` |
| `condition and not value` | Logic AND | `if required and not value:` |
| `raise RuntimeError(msg)` | Ném lỗi | `raise RuntimeError("Missing var")` |
| `x if condition else y` | Ternary operator (3 ngôi) | `return value if value else ""` |
| `x or y` | Hoặc (nếu x False/None, dùng y) | `"" or 900` = 900 |
| `int(string)` | Chuyển string → int | `int("900")` = 900 |
| `Path(string)` | Chuyển string → Path object | `Path("tmp")` |
| `path.mkdir(parents=True, exist_ok=True)` | Tạo folder | `settings.temp_dir.mkdir(...)` |

---

## ✅ Kết Luận

**`config.py` làm 3 việc chính:**

1. **Đọc `.env`** → `load_dotenv()`
2. **Xử lý biến** → `_get_env()` (mặc định, bắt buộc)
3. **Tạo Settings object** → `@dataclass(frozen=True)`

**Singleton Pattern:** Tạo `settings` duy nhất, import ở các file khác, dùng chung toàn ứng dụng.

**Lợi Ích:**
- Cấu hình tập trung (1 chỗ)
- An toàn (bất biến, type-hinted)
- Dễ thay đổi (chỉ cần sửa `.env`)
