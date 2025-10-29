# 🚀 ROADMAP: Tích Hợp RAG Vào Frontend (mindmap-notion-interface)

## 📋 HIỆN TRẠNG

### ✅ Bạn Có
1. **Frontend**: React + TypeScript + Shadcn UI (mindmap-notion-interface)
2. **Backend**: Express.js (hoặc Node.js)
3. **Embedding Pipeline**: Python (Embedding_langchain)
4. **Database**: Supabase (pgvector ready)

### ❌ Còn Thiếu
1. **Retriever API**: Backend endpoint để search embeddings
2. **RAG Service**: Backend service để call LLM
3. **Chat UI**: Frontend component cho chatbot/RAG
4. **API Integration**: Frontend gọi backend RAG endpoints

---

## 🎯 3 GIAI ĐOẠN

### **GIAI ĐOẠN 1: Backend RAG Service (Python)**

**Mục đích**: Tạo Python modules để support RAG

**Tasks**:

```
Embedding_langchain/src/
├─ retriever.py          🆕 Search embeddings from DB
├─ prompt_builder.py     🆕 Format context + query
├─ llm_client.py         🆕 Call OpenAI/Ollama
└─ rag_service.py        🆕 Orchestrate RAG flow
```

**Estimated Time**: 2-3 hours

**File Details**:

```python
# src/retriever.py
def retrieve_similar_chunks(
    query: str, 
    document_id: str, 
    top_k: int = 5
) -> list[dict]:
    """Tìm chunks tương tự từ Supabase"""
    pass

# src/prompt_builder.py
def build_rag_prompt(
    query: str, 
    context_chunks: list[dict]
) -> str:
    """Xây dựng prompt cho LLM"""
    pass

# src/llm_client.py
def generate_answer(
    prompt: str,
    model: str = "gpt-3.5-turbo"
) -> str:
    """Gọi OpenAI/Ollama để generate answer"""
    pass

# src/rag_service.py
def rag_query(
    query: str,
    document_id: str,
    top_k: int = 5
) -> dict:
    """End-to-end RAG pipeline"""
    # 1. retrieve_similar_chunks()
    # 2. build_rag_prompt()
    # 3. generate_answer()
    # 4. return formatted response
    pass
```

---

### **GIAI ĐOẠN 2: Backend API Endpoints (Express.js)**

**Mục đích**: Expose RAG functionality thông qua API

**Tasks**:

```
mindmap-notion-interface/backend/src/
├─ routes/
│  └─ rag.routes.ts      🆕 POST /api/rag/chat
├─ controllers/
│  └─ rag.controller.ts  🆕 Call Python rag_service
└─ services/
   └─ ragService.ts      🆕 Python subprocess wrapper
```

**Estimated Time**: 2-3 hours

**Endpoints**:

```typescript
// POST /api/rag/chat
interface RAGRequest {
  query: string;           // "LangChain là gì?"
  document_id: string;     // "doc123"
  top_k?: number;          // default 5
}

interface RAGResponse {
  answer: string;          // Generated answer
  sources: Array<{         // Retrieved chunks
    chunk_index: number;
    page_number: number;
    content: string;
    similarity: number;
  }>;
  metadata: {
    query_time_ms: number;
    model: string;
  };
}
```

**Implementation**:

```typescript
// rag.controller.ts
export async function chatWithRAG(req: Request, res: Response) {
  const { query, document_id, top_k } = req.body;
  
  try {
    // Call Python RAG service
    const result = await ragService.queryRAG(query, document_id, top_k);
    
    res.json({
      answer: result.answer,
      sources: result.sources,
      metadata: {
        query_time_ms: Date.now() - startTime,
        model: 'gpt-3.5-turbo'
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

// rag.routes.ts
router.post('/chat', chatWithRAG);
```

---

### **GIAI ĐOẠN 3: Frontend Chat UI (React)**

**Mục đích**: Tạo chatbot interface cho RAG

**Tasks**:

```
mindmap-notion-interface/src/
├─ components/
│  └─ RAGChat/
│     ├─ ChatInterface.tsx          🆕 Main chat UI
│     ├─ ChatMessage.tsx            🆕 Message bubble
│     ├─ ChatInput.tsx              🆕 Query input
│     ├─ SourcesPanel.tsx           🆕 Retrieved chunks
│     └─ RAGChat.tsx                🆕 Parent component
│
├─ hooks/
│  └─ useRAGChat.ts                 🆕 Query hook
│
└─ services/
   └─ ragAPI.ts                     🆕 API client
```

**Estimated Time**: 2-3 hours

**Component Structure**:

```
RAGChat (Parent)
├─ ChatInterface (Main)
│  ├─ ChatMessages
│  │  ├─ ChatMessage (User)
│  │  ├─ ChatMessage (Assistant)
│  │  └─ ChatMessage (Loading)
│  │
│  └─ ChatInput
│     ├─ TextField
│     └─ SendButton
│
└─ SourcesPanel (Sidebar)
   ├─ SourceCard
   │  ├─ PageNumber
   │  ├─ ChunkIndex
   │  ├─ Content
   │  └─ SimilarityScore
   └─ ShowMore
```

**UI Mockup**:

```
┌─────────────────────────────────────────────────────┐
│  RAG Chat Interface                            [×]  │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│ Retrieved    │  Chat Messages                       │
│ Sources      │                                      │
│              │  User: "LangChain là gì?"           │
│ • Chunk 3    │  [⏳ Loading...]                     │
│   LangChain  │                                      │
│   is ...     │  Assistant: "LangChain là framework" │
│   Score: 0.9 │                                      │
│              │                                      │
│ • Chunk 5    │  Input: [________________] [Send]   │
│   ...        │                                      │
└──────────────┴──────────────────────────────────────┘
```

---

## 📊 INTEGRATION FLOW

```
Frontend (React)
    ↓ (POST /api/rag/chat)
    │ { query, document_id }
    ▼
Backend (Express)
    ↓ (spawn Python subprocess)
    ▼
Python RAG Service
    ├─ retriever.py: Search embeddings
    ├─ prompt_builder.py: Format context
    ├─ llm_client.py: Call OpenAI/Ollama
    └─ return { answer, sources }
    ▼
Backend (Response)
    ↓ (200 OK with RAG response)
    ▼
Frontend (Display)
    ├─ Show answer in chat
    ├─ Show sources in sidebar
    └─ User can ask follow-up
```

---

## 🔄 STEP-BY-STEP IMPLEMENTATION

### **STEP 1: Create Python RAG Modules (2-3 hours)**

```bash
cd Embedding_langchain

# 1. Create retriever.py
# - Embed query
# - Query Supabase pgvector
# - Return top-k chunks

# 2. Create prompt_builder.py
# - Format context chunks
# - Build system prompt + context + question

# 3. Create llm_client.py
# - Support OpenAI (or Ollama)
# - Call LLM API
# - Return generated answer

# 4. Create rag_service.py
# - Orchestrate all 3 modules above
# - Error handling
# - Return formatted response

# 5. Create requirements.txt updates
pip install openai  # if using OpenAI
# or
pip install requests  # if using Ollama
```

**Test Python RAG**:

```bash
python -c "
from src.rag_service import rag_query
result = rag_query(
    query='LangChain là gì?',
    document_id='doc123',
    top_k=5
)
print(result)
"
```

---

### **STEP 2: Create Backend Express Endpoints (2-3 hours)**

```bash
cd mindmap-notion-interface/backend

# 1. Create rag.routes.ts
# - POST /api/rag/chat

# 2. Create rag.controller.ts
# - Parse request
# - Call Python service
# - Return response

# 3. Create ragService.ts
# - Spawn Python subprocess
# - Handle stdin/stdout
# - Error handling

# 4. Update main server file
# - Import rag.routes
# - Register routes
```

**Express Handler Pattern**:

```typescript
// rag.controller.ts
export async function chatWithRAG(req: Request, res: Response) {
  const { query, document_id, top_k } = req.body;
  
  // Validate input
  if (!query || !document_id) {
    return res.status(400).json({ error: 'Missing fields' });
  }
  
  try {
    // Call Python service
    const result = await ragService.queryRAG(query, document_id, top_k);
    
    // Return response
    res.json({
      success: true,
      data: {
        answer: result.answer,
        sources: result.sources,
        metadata: {
          model: 'gpt-3.5-turbo',
          timestamp: new Date().toISOString()
        }
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
```

**Test Backend**:

```bash
curl -X POST http://localhost:3000/api/rag/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "LangChain là gì?",
    "document_id": "doc123"
  }'
```

---

### **STEP 3: Create React Chat Component (2-3 hours)**

```bash
cd mindmap-notion-interface/src

# 1. Create components/RAGChat/ChatInterface.tsx
# - Main chat UI
# - Message list
# - Input field

# 2. Create components/RAGChat/SourcesPanel.tsx
# - Display retrieved chunks
# - Show similarity scores

# 3. Create hooks/useRAGChat.ts
# - Manage chat state
# - Handle API calls
# - Loading states

# 4. Create services/ragAPI.ts
# - Fetch wrapper
# - Type-safe requests
```

**React Component Pattern**:

```typescript
// components/RAGChat/ChatInterface.tsx
export function ChatInterface({ documentId }: { documentId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  
  const handleSendMessage = async (query: string) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setLoading(true);
    
    try {
      // Call backend RAG
      const response = await ragAPI.chat(query, documentId);
      
      // Add assistant message
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.answer 
      }]);
      
      // Set sources
      setSources(response.sources);
    } catch (error) {
      // Show error
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: 'Failed to get answer' 
      }]);
    } finally {
      setLoading(false);
      setInput('');
    }
  };
  
  return (
    <div className="flex gap-4 h-full">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 p-4">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))}
          {loading && <ChatMessage role="assistant" loading />}
        </div>
        
        {/* Input Area */}
        <ChatInput 
          value={input}
          onChange={setInput}
          onSend={handleSendMessage}
          disabled={loading}
        />
      </div>
      
      {/* Sources Sidebar */}
      <SourcesPanel sources={sources} />
    </div>
  );
}

// hooks/useRAGChat.ts
export function useRAGChat(documentId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  
  const sendMessage = async (query: string) => {
    setLoading(true);
    try {
      const response = await ragAPI.chat(query, documentId);
      return response;
    } finally {
      setLoading(false);
    }
  };
  
  return { messages, loading, sendMessage };
}

// services/ragAPI.ts
export const ragAPI = {
  async chat(query: string, documentId: string, topK = 5) {
    const response = await fetch('/api/rag/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, document_id: documentId, top_k: topK })
    });
    
    if (!response.ok) throw new Error('RAG chat failed');
    
    return response.json();
  }
};
```

**Test Frontend**:

```bash
npm run dev
# Navigate to RAG Chat page
# Send a query
# See answer + sources
```

---

## 📁 FINAL PROJECT STRUCTURE

```
DACN_MindMapNote/
├─ Embedding_langchain/                ✅ Embedding pipeline
│  ├─ src/
│  │  ├─ config.py
│  │  ├─ text_extractor.py
│  │  ├─ chunker.py
│  │  ├─ embedder.py
│  │  ├─ supabase_client.py
│  │  ├─ pipeline.py
│  │  ├─ retriever.py              🆕 RAG
│  │  ├─ prompt_builder.py          🆕 RAG
│  │  ├─ llm_client.py              🆕 RAG
│  │  └─ rag_service.py             🆕 RAG
│  ├─ scripts/
│  │  └─ ingest_document.py
│  └─ requirements.txt               📝 Update
│
└─ mindmap-notion-interface/           ✅ Frontend
   ├─ backend/
   │  ├─ src/
   │  │  ├─ routes/
   │  │  │  ├─ documents.routes.ts
   │  │  │  ├─ groups.routes.ts
   │  │  │  └─ rag.routes.ts        🆕 RAG
   │  │  ├─ controllers/
   │  │  │  ├─ documents.controller.ts
   │  │  │  ├─ groups.controller.ts
   │  │  │  └─ rag.controller.ts     🆕 RAG
   │  │  ├─ services/
   │  │  │  ├─ authService.ts
   │  │  │  └─ ragService.ts         🆕 RAG
   │  │  └─ index.ts                 📝 Update
   │  └─ package.json                📝 Update
   │
   └─ src/
      ├─ components/
      │  ├─ UploadDocument.tsx
      │  ├─ documents/
      │  ├─ groups/
      │  ├─ layout/
      │  ├─ notifications/
      │  ├─ ui/
      │  └─ RAGChat/                 🆕 RAG
      │     ├─ ChatInterface.tsx
      │     ├─ ChatMessage.tsx
      │     ├─ ChatInput.tsx
      │     ├─ SourcesPanel.tsx
      │     └─ RAGChat.tsx
      │
      ├─ hooks/
      │  ├─ use-mobile.tsx
      │  ├─ use-toast.ts
      │  ├─ useAuth.tsx
      │  └─ useRAGChat.ts            🆕 RAG
      │
      ├─ pages/
      │  ├─ Auth.tsx
      │  ├─ Categories.tsx
      │  ├─ Chatbot.tsx              ✅ Có rồi?
      │  ├─ Documents.tsx
      │  ├─ Groups.tsx
      │  ├─ Home.tsx
      │  ├─ Search.tsx
      │  ├─ Settings.tsx
      │  ├─ Statistics.tsx
      │  ├─ NotFound.tsx
      │  └─ RAGPage.tsx              🆕 RAG
      │
      └─ services/
         ├─ api.ts                    📝 Update
         └─ ragAPI.ts                 🆕 RAG
```

---

## 🎯 TOTAL TIMELINE

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Python RAG modules | 2-3h | 🆕 TODO |
| 2 | Backend API endpoints | 2-3h | 🆕 TODO |
| 3 | React Chat UI | 2-3h | 🆕 TODO |
| 4 | Integration testing | 1-2h | 🆕 TODO |
| 5 | Styling & Polish | 1h | 🆕 TODO |
| **TOTAL** | | **8-12h** | **~1-2 days** |

---

## ✅ CHECKLIST: IMPLEMENTATION

### **Phase 1: Python (Embedding_langchain/)**
- [ ] `src/retriever.py` - Query Supabase pgvector
- [ ] `src/prompt_builder.py` - Format context
- [ ] `src/llm_client.py` - Call OpenAI/Ollama
- [ ] `src/rag_service.py` - Orchestrate RAG
- [ ] `requirements.txt` - Add openai/requests
- [ ] Test: `python -c "from src.rag_service import rag_query; rag_query(...)"`

### **Phase 2: Backend (mindmap-notion-interface/backend/)**
- [ ] `src/routes/rag.routes.ts` - POST /api/rag/chat
- [ ] `src/controllers/rag.controller.ts` - Handle requests
- [ ] `src/services/ragService.ts` - Call Python subprocess
- [ ] `src/index.ts` - Register RAG routes
- [ ] `package.json` - Add dependencies (if any)
- [ ] Test: `curl -X POST http://localhost:3000/api/rag/chat ...`

### **Phase 3: Frontend (mindmap-notion-interface/src/)**
- [ ] `components/RAGChat/ChatInterface.tsx` - Main UI
- [ ] `components/RAGChat/ChatMessage.tsx` - Message bubbles
- [ ] `components/RAGChat/ChatInput.tsx` - Input field
- [ ] `components/RAGChat/SourcesPanel.tsx` - Sources display
- [ ] `components/RAGChat/RAGChat.tsx` - Parent component
- [ ] `hooks/useRAGChat.ts` - State management
- [ ] `services/ragAPI.ts` - API client
- [ ] `pages/RAGPage.tsx` - Page component
- [ ] Test: `npm run dev` → navigate to RAG page

### **Phase 4: Integration**
- [ ] E2E testing (UI → Backend → Python → DB)
- [ ] Error handling
- [ ] Loading states
- [ ] Response formatting

---

## 🔧 TECH STACK REQUIREMENTS

**Backend**:
- Node.js + Express
- child_process (spawn Python)

**Frontend**:
- React + TypeScript
- Tanstack Query (optional, for caching)
- Shadcn UI (already have)

**Python**:
- sentence-transformers
- supabase-py
- openai (or requests for Ollama)

---

## 🚀 PRIORITY ORDER

### **Recommended**: 
1. ✅ **FIRST**: Implement Python RAG modules
   - Lowest risk
   - Can test independently
   - Foundation for everything else

2. ✅ **SECOND**: Implement Backend endpoints
   - Moderate risk
   - Can mock Python if needed
   - Test with Postman/curl

3. ✅ **THIRD**: Implement Frontend UI
   - Highest risk
   - But can iterate quickly
   - Most visible to user

---

## 💡 TIPS

1. **Start with CLI Test**: Before frontend, test Python RAG locally
   ```bash
   python -c "from src.rag_service import rag_query; print(rag_query('LangChain là gì?', 'doc123'))"
   ```

2. **Use Postman**: Test backend endpoints before wiring frontend
   ```
   POST http://localhost:3000/api/rag/chat
   Body: { "query": "...", "document_id": "doc123" }
   ```

3. **Mock API First**: Build React UI with mock data, then wire real API
   ```typescript
   const mockResponse = {
     answer: "LangChain là...",
     sources: [...]
   };
   ```

4. **Deploy Python as Service**: Don't spawn subprocess for prod
   - Better: Run Python as separate service
   - Call via HTTP (FastAPI/Flask wrapper)

---

## 📚 NEXT STEPS

Bạn muốn tôi giúp cái gì trước?

**A) Implement Python RAG Modules**
→ Tôi tạo files + test scripts

**B) Implement Backend API** 
→ Tôi tạo Express routes + controllers

**C) Implement React Chat UI**
→ Tôi tạo components + hooks

**D) All 3 at once (comprehensive)**
→ Tôi tạo tất cả files + integration guide

Chọn hướng nào? 🚀
