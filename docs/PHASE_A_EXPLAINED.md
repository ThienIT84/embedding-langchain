# Phase A: RAG Core (Retrieval-Augmented Generation)

## Tổng Quan

**Phase A** là giai đoạn xây dựng **Python RAG pipeline** hoàn chỉnh, bao gồm:

1. **Text Extraction** - Trích xuất text từ PDF
2. **Text Chunking** - Chia text thành chunks nhỏ
3. **Embedding** - Chuyển chunks thành vectors (768-dim)
4. **Vector Storage** - Lưu vectors vào Supabase pgvector
5. **Retrieval** - Tìm chunks liên quan dựa trên similarity
6. **Prompt Building** - Xây dựng prompt cho LLM
7. **LLM Generation** - Gọi Ollama llama3 để sinh answer

**Output:** Answer + sources + metadata

```
PDF Input
   ↓
[Text Extraction] → Raw text
   ↓
[Text Chunking] → List of chunks (300-500 tokens each)
   ↓
[Embedding] → Vectors (768-dim) via sentence-transformers
   ↓
[Vector Storage] → Supabase pgvector
   ↓
[Retrieval] → Top-K similar chunks (IVFFlat search)
   ↓
[Prompt Building] → System prompt + context + query
   ↓
[LLM Generation] → Ollama llama3 generates answer
   ↓
Answer + Sources + Metadata
```

---

## Architecture (Chi Tiết)

```
┌──────────────────────────────────────────────────────────────┐
│              PHASE A: RAG CORE PIPELINE                      │
│         (Embedding_langchain/src/)                           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  1. text_extractor.py │
│  ┌────────────────────────────────────┐
│  │ extract_text_from_pdf(pdf_path)    │
│  │ → text (str)                       │
│  └────────────────────────────────────┘
└──────────────────────┘
        ↓
┌──────────────────────┐
│  2. chunker.py       │
│  ┌────────────────────────────────────┐
│  │ chunk_text(text, chunk_size, overlap)
│  │ → chunks (List[str])               │
│  └────────────────────────────────────┘
└──────────────────────┘
        ↓
┌──────────────────────┐
│  3. embedder.py      │
│  ┌────────────────────────────────────┐
│  │ embed_chunks(chunks)               │
│  │ → embeddings (numpy array)         │
│  │   Shape: (N, 768)                  │
│  └────────────────────────────────────┘
└──────────────────────┘
        ↓
┌──────────────────────┐
│  4. supabase_client.py
│  ┌────────────────────────────────────┐
│  │ insert_vectors(document_id,        │
│  │   chunks, embeddings, metadata)    │
│  │ → Store in pgvector table          │
│  └────────────────────────────────────┘
└──────────────────────┘
        ↓
┌──────────────────────┐
│  5. retriever.py     │
│  ┌────────────────────────────────────┐
│  │ retrieve_top_k(query_embedding,    │
│  │   top_k, document_id)              │
│  │ → chunks + metadata (List[Dict])   │
│  └────────────────────────────────────┘
└──────────────────────┘
        ↓
┌──────────────────────┐
│  6. prompt_builder.py │
│  ┌────────────────────────────────────┐
│  │ build_prompt(query, context,       │
│  │   system_prompt)                   │
│  │ → full_prompt (str)                │
│  └────────────────────────────────────┘
└──────────────────────┘
        ↓
┌──────────────────────┐
│  7. llm_client.py    │
│  ┌────────────────────────────────────┐
│  │ call_llm(prompt, system_prompt)    │
│  │ → answer (str)                     │
│  │   (Ollama llama3)                  │
│  └────────────────────────────────────┘
└──────────────────────┘
        ↓
┌──────────────────────┐
│  8. rag_service.py   │
│  ┌────────────────────────────────────┐
│  │ rag_query(query, document_id,      │
│  │   top_k, system_prompt)            │
│  │ → result (Dict)                    │
│  │   {answer, sources, metadata}      │
│  └────────────────────────────────────┘
└──────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES                               │
├──────────────────────────────────────────────────────────────┤
│ • Supabase PostgreSQL pgvector (Vector DB)                  │
│ • Ollama llama3 (Local LLM - http://localhost:11434)        │
│ • sentence-transformers (Multilingual embeddings)           │
└──────────────────────────────────────────────────────────────┘
```

---

## Module Chi Tiết

### 1. **text_extractor.py** - Trích xuất Text từ PDF

```python
import PyPDF2
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        pdf_path: Absolute path to PDF file
        
    Returns:
        Extracted text (str)
        
    Raises:
        FileNotFoundError: PDF không tồn tại
        RuntimeError: Lỗi đọc PDF
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    text_parts = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Add metadata
                text_parts.append(f"[Page {page_num + 1}]\n{text}")
        
        full_text = "\n".join(text_parts)
        return full_text
        
    except Exception as e:
        raise RuntimeError(f"Error reading PDF: {str(e)}")
```

**Input:** PDF file path
**Output:** Full text từ all pages
**Issues xử lý:**
- ✅ Non-existent files
- ✅ Invalid PDF format
- ✅ Vietnamese text extraction

---

### 2. **chunker.py** - Chia Text thành Chunks

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(
    text: str,
    chunk_size: int = 500,  # tokens
    chunk_overlap: int = 100  # tokens
) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text
        chunk_size: Tokens per chunk (default 500)
        chunk_overlap: Overlap between chunks (default 100)
        
    Returns:
        List of chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = splitter.split_text(text)
    
    # Filter out empty/very short chunks
    chunks = [c.strip() for c in chunks if len(c.strip()) > 50]
    
    return chunks
```

**Algorithm:**
1. Try split by "\n\n" (paragraph)
2. If chunk still too long, split by "\n" (line)
3. If chunk still too long, split by "." (sentence)
4. If chunk still too long, split by " " (word)
5. Finally, split by character if needed

**Overlap:** 100 tokens between chunks → tránh mất context

**Example:**
```
Original text: "Machine learning is... Deep learning is... Neural networks are..."

Chunk 1: "Machine learning is... Deep learning is..."
Chunk 2: "Deep learning is... Neural networks are..."  ← 100 token overlap
Chunk 3: "Neural networks are... Transformers are..."  ← 100 token overlap
```

---

### 3. **embedder.py** - Tạo Vector Embeddings

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class Embedder:
    def __init__(self, model_name: str = "paraphrase-multilingual-mpnet-base-v2"):
        """
        Initialize embedder with multilingual model.
        
        Args:
            model_name: HuggingFace model ID
                - "paraphrase-multilingual-mpnet-base-v2" (768-dim, 125M params)
                - Good for Vietnamese + English
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 768
    
    def embed_chunks(self, chunks: list[str]) -> np.ndarray:
        """
        Embed multiple chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Embeddings array (N, 768) where N = len(chunks)
        """
        embeddings = self.model.encode(
            chunks,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        # embeddings shape: (N, 768)
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query string.
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector (768,)
        """
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding
```

**Model:** `paraphrase-multilingual-mpnet-base-v2`
- ✅ 768-dimensional vectors
- ✅ Supports 50+ languages (including Vietnamese)
- ✅ Semantic similarity (not keyword matching)

**Vector Similarity:**
```
Query: "Machine learning là gì?"
Chunk A: "Machine learning là một nhánh của AI..."  → similarity: 0.95
Chunk B: "Deep learning sử dụng neural networks..."  → similarity: 0.82
Chunk C: "Pyhon là một ngôn ngữ lập trình..."  → similarity: 0.15
```

---

### 4. **supabase_client.py** - Lưu Vectors vào DB

```python
from supabase import create_client, Client
from postgrest.exceptions import APIError
import numpy as np

class SupabaseClient:
    def __init__(self, url: str, key: str):
        """Initialize Supabase client."""
        self.client: Client = create_client(url, key)
    
    def insert_vectors(
        self,
        document_id: int,
        chunks: list[str],
        embeddings: np.ndarray,
        metadata: dict = None
    ) -> dict:
        """
        Insert chunks and embeddings into pgvector table.
        
        Args:
            document_id: Document ID (tham chiếu)
            chunks: List of text chunks
            embeddings: Array of shape (N, 768)
            metadata: Additional metadata per chunk
            
        Returns:
            Insert result dict
        """
        records = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            record = {
                'document_id': document_id,
                'chunk_text': chunk,
                'embedding': embedding.tolist(),  # Convert to list
                'chunk_index': i,
                'metadata': metadata or {'source': 'document'},
                'created_at': 'now()'
            }
            records.append(record)
        
        # Batch insert
        result = self.client.table('document_chunks').insert(records).execute()
        
        return {
            'inserted_count': len(records),
            'document_id': document_id
        }
    
    def search_vectors(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        document_id: int = None
    ) -> list[dict]:
        """
        Search vectors using pgvector similarity.
        
        Args:
            query_embedding: Query vector (768,)
            top_k: Number of results
            document_id: Filter by document (optional)
            
        Returns:
            List of chunks with similarity scores
        """
        # Convert to pgvector format [1, 2, 3]
        vector_str = f"[{','.join(str(x) for x in query_embedding)}]"
        
        query = self.client.table('document_chunks').select(
            'id, chunk_text, metadata, chunk_index, embedding'
        ).order(
            'embedding',
            desc=False
        ).rpc('search_documents', {
            'query_embedding': vector_str,
            'match_count': top_k,
            'document_filter_id': document_id
        })
        
        results = query.execute()
        return results.data
```

**Database Schema (PostgreSQL):**
```sql
CREATE TABLE document_chunks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    document_id INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768) NOT NULL,  -- pgvector extension
    chunk_index INT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

-- Create IVFFlat index for fast similarity search
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

### 5. **retriever.py** - Tìm Chunks Liên Quan

```python
from .embedder import Embedder
from .supabase_client import SupabaseClient
from typing import Optional

class Retriever:
    def __init__(self, embedder: Embedder, db: SupabaseClient):
        self.embedder = embedder
        self.db = db
    
    def retrieve_top_k(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[int] = None
    ) -> list[dict]:
        """
        Retrieve top-K similar chunks for a query.
        
        Args:
            query: User query text
            top_k: Number of chunks to retrieve
            document_id: Filter by document
            
        Returns:
            List of chunks with metadata:
            [
                {
                    'chunk_text': '...',
                    'similarity': 0.92,
                    'metadata': {...},
                    'chunk_index': 0
                },
                ...
            ]
        """
        # 1. Embed query
        query_embedding = self.embedder.embed_query(query)
        
        # 2. Search database
        results = self.db.search_vectors(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=document_id
        )
        
        # 3. Format results
        retrieved_chunks = []
        for result in results:
            retrieved_chunks.append({
                'chunk_text': result['chunk_text'],
                'similarity': result['similarity'],
                'metadata': result['metadata'],
                'chunk_index': result['chunk_index']
            })
        
        return retrieved_chunks
```

**Flow:**
```
Query: "Machine learning là gì?"
    ↓
[Embed query] → vector (768,)
    ↓
[Search DB with IVFFlat index] → Top 5 similar chunks
    ↓
[Format results] → [{chunk_text, similarity, metadata}, ...]
```

**Similarity Scoring:**
- Uses **cosine similarity** (range: -1 to 1, higher = more similar)
- pgvector with IVFFlat index: O(√N) instead of O(N)

---

### 6. **prompt_builder.py** - Xây dựng Prompt cho LLM

```python
class PromptBuilder:
    @staticmethod
    def build_prompt(
        query: str,
        retrieved_chunks: list[dict],
        system_prompt: str = None
    ) -> str:
        """
        Build a prompt for LLM from query and context.
        
        Args:
            query: User query
            retrieved_chunks: Context chunks from retrieval
            system_prompt: Custom system instruction
            
        Returns:
            Full prompt text
        """
        # Default system prompt nếu không cung cấp
        if not system_prompt:
            system_prompt = """Bạn là trợ lý AI giúp tóm tắt và trả lời câu hỏi về tài liệu.
Hãy trả lời dựa trên bối cảnh được cung cấp.
Nếu không tìm thấy thông tin, hãy nói "Tôi không tìm thấy thông tin trong tài liệu"."""
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks):
            similarity = chunk['similarity']
            text = chunk['chunk_text']
            context_parts.append(
                f"[Chunk {i+1} - Similarity: {similarity:.3f}]\n{text}"
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build full prompt
        prompt = f"""System: {system_prompt}

Context:
{context}

Question: {query}

Answer:"""
        
        return prompt
    
    @staticmethod
    def get_prompt_metadata(prompt: str) -> dict:
        """Get metadata about the prompt."""
        return {
            'prompt_length': len(prompt),
            'prompt_tokens': len(prompt.split()),
            'num_contexts': prompt.count('[Chunk ')
        }
```

**Example Prompt:**
```
System: Bạn là trợ lý AI giúp tóm tắt và trả lời câu hỏi về tài liệu.

Context:
[Chunk 1 - Similarity: 0.950]
Machine learning là một nhánh của trí tuệ nhân tạo (AI) 
cho phép máy tính học từ dữ liệu...

[Chunk 2 - Similarity: 0.920]
Các thuật toán machine learning phổ biến bao gồm:
- Regression, Classification, Clustering...

[Chunk 3 - Similarity: 0.880]
Deep learning sử dụng neural networks với nhiều layers...

Question: Machine learning là gì?

Answer:
```

---

### 7. **llm_client.py** - Gọi Ollama llama3

```python
import requests
import json
from typing import Iterator

class LLMClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize LLM client.
        
        Args:
            base_url: Ollama server URL (default localhost:11434)
        """
        self.base_url = base_url
        self.model = "llama3"  # or other models
    
    def call_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        Call Ollama LLM to generate answer.
        
        Args:
            prompt: Full prompt with context
            system_prompt: System instruction
            temperature: Creativity (0-1, higher = more creative)
            top_p: Nucleus sampling threshold
            
        Returns:
            Generated answer (str)
            
        Raises:
            ConnectionError: Cannot connect to Ollama
            RuntimeError: LLM error
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "temperature": temperature,
            "top_p": top_p
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            answer = result.get('response', '')
            
            return answer
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except Exception as e:
            raise RuntimeError(f"LLM error: {str(e)}")
    
    def call_llm_stream(
        self,
        prompt: str,
        system_prompt: str = None
    ) -> Iterator[str]:
        """
        Call LLM with streaming response.
        
        Args:
            prompt: Full prompt
            system_prompt: System instruction
            
        Yields:
            Chunks of generated text
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": True
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    yield chunk.get('response', '')
                    
        except Exception as e:
            raise RuntimeError(f"LLM streaming error: {str(e)}")
```

**Ollama API:**
- Model: `llama3` (7B params, ~4GB)
- Endpoint: `http://localhost:11434/api/generate`
- Format: JSON request, JSON response
- Temperature: 0.7 (balanced creativity)

---

### 8. **rag_service.py** - Orchestrator (Main Entry Point)

```python
from .text_extractor import extract_text_from_pdf
from .chunker import chunk_text
from .embedder import Embedder
from .supabase_client import SupabaseClient
from .retriever import Retriever
from .prompt_builder import PromptBuilder
from .llm_client import LLMClient
from .config import Config
from typing import Optional
import time

class RAGService:
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize components
        self.embedder = Embedder()
        self.db = SupabaseClient(config.supabase_url, config.supabase_key)
        self.retriever = Retriever(self.embedder, self.db)
        self.prompt_builder = PromptBuilder()
        self.llm_client = LLMClient(config.ollama_url)
    
    def ingest_document(
        self,
        document_id: int,
        pdf_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> dict:
        """
        Ingest a PDF document into the system.
        
        Steps:
        1. Extract text from PDF
        2. Split into chunks
        3. Embed chunks
        4. Store in pgvector
        
        Args:
            document_id: Document ID
            pdf_path: Path to PDF file
            chunk_size: Tokens per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            Ingestion result
        """
        start_time = time.time()
        
        try:
            # Step 1: Extract text
            print(f"[1/4] Extracting text from {pdf_path}...")
            text = extract_text_from_pdf(pdf_path)
            
            # Step 2: Chunk text
            print(f"[2/4] Chunking text ({len(text)} chars)...")
            chunks = chunk_text(text, chunk_size, chunk_overlap)
            print(f"      Created {len(chunks)} chunks")
            
            # Step 3: Embed chunks
            print(f"[3/4] Embedding {len(chunks)} chunks...")
            embeddings = self.embedder.embed_chunks(chunks)
            
            # Step 4: Store in database
            print(f"[4/4] Storing in Supabase pgvector...")
            result = self.db.insert_vectors(
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata={'source': pdf_path}
            )
            
            elapsed = time.time() - start_time
            
            return {
                'success': True,
                'document_id': document_id,
                'chunks_created': len(chunks),
                'embeddings_stored': result['inserted_count'],
                'processing_time_ms': int(elapsed * 1000)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }
    
    def rag_query(
        self,
        query: str,
        document_id: int,
        top_k: int = 5,
        system_prompt: Optional[str] = None
    ) -> dict:
        """
        Execute RAG query.
        
        Steps:
        1. Embed query
        2. Retrieve top-k chunks
        3. Build prompt
        4. Call LLM
        5. Format answer
        
        Args:
            query: User query
            document_id: Document to search
            top_k: Number of chunks to retrieve
            system_prompt: Custom system instruction
            
        Returns:
            RAG result with answer + sources
        """
        start_time = time.time()
        
        try:
            # Step 1-2: Retrieve relevant chunks
            retrieved_chunks = self.retriever.retrieve_top_k(
                query=query,
                top_k=top_k,
                document_id=document_id
            )
            
            if not retrieved_chunks:
                return {
                    'success': False,
                    'error': 'No relevant chunks found'
                }
            
            # Step 3: Build prompt
            full_prompt = self.prompt_builder.build_prompt(
                query=query,
                retrieved_chunks=retrieved_chunks,
                system_prompt=system_prompt
            )
            
            # Step 4: Call LLM
            answer = self.llm_client.call_llm(
                prompt=full_prompt,
                system_prompt=system_prompt
            )
            
            elapsed = time.time() - start_time
            
            # Step 5: Format result
            return {
                'success': True,
                'answer': answer,
                'sources': [
                    {
                        'chunk': chunk['chunk_text'],
                        'similarity': chunk['similarity'],
                        'metadata': chunk['metadata']
                    }
                    for chunk in retrieved_chunks
                ],
                'metadata': {
                    'query': query,
                    'document_id': document_id,
                    'chunks_retrieved': len(retrieved_chunks),
                    'processing_time_ms': int(elapsed * 1000)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }

# Singleton instance
_rag_service: Optional[RAGService] = None

def get_rag_service(config: Config = None) -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(config or Config())
    return _rag_service

# Convenience function for direct RAG queries
def rag_query(
    query: str,
    document_id: int,
    top_k: int = 5,
    system_prompt: Optional[str] = None
) -> dict:
    """Direct function to execute RAG query."""
    service = get_rag_service()
    return service.rag_query(query, document_id, top_k, system_prompt)
```

**Workflow:**
```
Input: {query, document_id, top_k, system_prompt}
    ↓
[Retrieve] → Top-k chunks
    ↓
[Build Prompt] → System + context + query
    ↓
[LLM] → Generate answer
    ↓
Output: {answer, sources, metadata, processing_time}
```

---

## Configuration (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Ollama
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
    
    # Embedding
    EMBEDDING_MODEL = os.getenv(
        'EMBEDDING_MODEL',
        'paraphrase-multilingual-mpnet-base-v2'
    )
    EMBEDDING_DIM = 768
    
    # Chunking
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '500'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))
    
    # RAG
    DEFAULT_TOP_K = int(os.getenv('DEFAULT_TOP_K', '5'))
    DEFAULT_SYSTEM_PROMPT = """Bạn là trợ lý AI giúp tóm tắt và trả lời 
    câu hỏi về tài liệu. Hãy trả lời dựa trên bối cảnh được cung cấp."""
```

**.env file:**
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...

OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3

CHUNK_SIZE=500
CHUNK_OVERLAP=100
DEFAULT_TOP_K=5
```

---

## Usage Scripts

### **ingest_document.py** - Ingest PDF vào Database

```python
from src.rag_service import get_rag_service
from src.config import Config
import sys

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python ingest_document.py <document_id> <pdf_path>")
        sys.exit(1)
    
    document_id = int(sys.argv[1])
    pdf_path = sys.argv[2]
    
    service = get_rag_service(Config())
    result = service.ingest_document(document_id, pdf_path)
    
    print(f"Ingestion result: {result}")
```

**Run:**
```bash
python scripts/ingest_document.py 1 "documents/my_document.pdf"
```

---

### **rag_query.py** - Query Document

```python
from src.rag_service import rag_query
import sys
import json

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python rag_query.py <document_id> <query>")
        sys.exit(1)
    
    document_id = int(sys.argv[1])
    query = sys.argv[2]
    
    result = rag_query(
        query=query,
        document_id=document_id,
        top_k=5
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

**Run:**
```bash
python scripts/rag_query.py 1 "Machine learning là gì?"
```

**Output:**
```json
{
  "success": true,
  "answer": "Machine learning là một nhánh của AI cho phép...",
  "sources": [
    {
      "chunk": "Machine learning là...",
      "similarity": 0.950,
      "metadata": {"source": "documents/my_document.pdf"}
    }
  ],
  "metadata": {
    "processing_time_ms": 2340
  }
}
```

---

## Performance Characteristics

| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| PDF text extraction | 100-500 | Depends on PDF size |
| Text chunking | 50-200 | Quick operation |
| Embedding (100 chunks) | 500-1000 | Depends on model |
| Vector storage | 200-500 | Database write |
| **Total Ingestion** | **1000-3000** | ~3 sec for 100 chunks |
| Query embedding | 50-100 | Single query |
| Vector search (IVFFlat) | 50-150 | Fast index lookup |
| Prompt building | 10-20 | String manipulation |
| LLM generation | 10000-30000 | Ollama on CPU |
| **Total RAG Query** | **10200-30400** | ~20 sec for generation |

---

## Vector Similarity Concepts

### Cosine Similarity
```
sim(A, B) = (A · B) / (||A|| ||B||)

Range: [-1, 1]
- 1.0  = identical
- 0.0  = orthogonal
- -1.0 = opposite
```

### IVFFlat Index
- Approximate Nearest Neighbor (ANN) search
- Divides vectors into clusters
- O(√N) complexity instead of O(N)
- Small accuracy loss for huge speed gain

**Example:**
```
Query vector → Find nearest cluster → Search within cluster
10M vectors → Search ~√10M ≈ 3000 vectors instead of 10M
```

---

## Debugging & Troubleshooting

### Issue: Ollama Connection Error
```python
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running:
# Windows: ollama.exe serve
# Mac/Linux: ollama serve
```

### Issue: Vietnamese Text Encoding Error
```
Error: 'charmap' codec can't encode character...

Solution: Set environment variables
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
```

### Issue: Low Similarity Scores
- Check if chunks are too long/short (ideal: 300-500 tokens)
- Verify embeddings model is multilingual
- Try increasing `top_k` to get more candidates

### Issue: Slow Vector Search
- Verify IVFFlat index exists: `\d document_chunks`
- Check query performance: `EXPLAIN ANALYZE SELECT ...`
- Consider increasing `lists` parameter in index (100 → 200)

---

## Summary

**Phase A** provides **complete RAG pipeline**:

1. ✅ **Text extraction** - PDF → text
2. ✅ **Chunking** - Text → chunks (with overlap)
3. ✅ **Embedding** - Chunks → vectors (multilingual)
4. ✅ **Storage** - Vectors → Supabase pgvector
5. ✅ **Retrieval** - Query → top-K similar chunks
6. ✅ **Prompt building** - Context + query → prompt
7. ✅ **LLM generation** - Prompt → answer
8. ✅ **Integration** - All pieces orchestrated via RAGService

**Next:** Phase B wraps Phase A with HTTP API (Express backend).

---

## Key Dependencies

```
numpy<2.0.0                    # ← CRITICAL VERSION PIN
sentence-transformers==3.x     # Multilingual embeddings
supabase==2.x                  # pgvector client
langchain-text-splitters       # Recursive chunking
PyPDF2                         # PDF extraction
requests                       # HTTP calls to Ollama
python-dotenv                  # Environment variables
```

**Why numpy<2.0.0?**
- NumPy 2.0 broke compatibility with Torch/TensorFlow
- sentence-transformers uses Torch under the hood
- Only safe after all libraries update (likely 2026+)
