# RAG Modules Explained

Tài liệu này giải thích chi tiết 4 module mới phục vụ quy trình Retrieval-Augmented Generation (RAG) trong thư mục `src/`.

## 1. `retriever.py`
- **Mục tiêu**: Lấy các đoạn văn bản liên quan nhất tới câu hỏi từ bảng `document_embeddings` trong Supabase.
- **Quy trình**:
  1. Dùng cùng mô hình embedding với pipeline (`SentenceTransformer`) để embed câu hỏi.
  2. Lấy toàn bộ embedding của tài liệu (`document_id`) từ Supabase.
  3. Tính cosine similarity giữa query vector và từng chunk.
  4. Sắp xếp theo similarity giảm dần và trả về `top_k` kết quả.
- **Output**: Danh sách `RetrievedChunk` gồm `content`, `chunk_index`, `page_number`, `similarity`.

## 2. `prompt_builder.py`
- **Mục tiêu**: Kết hợp câu hỏi và danh sách chunk thành một prompt hoàn chỉnh.
- **Điểm nổi bật**:
  - Có `system_prompt` mặc định (có thể override).
  - Mỗi chunk được đánh số, hiển thị trang (nếu có) và similarity.
  - Cuối prompt nhấn mạnh việc phải trả lời dựa trên context.
- **Output**: Chuỗi prompt hoàn chỉnh sẵn sàng gửi lên LLM.

## 3. `llm_client.py`
- **Mục tiêu**: Gọi Ollama local (`ollama serve`) để sinh câu trả lời.
- **Hoạt động**:
  - Đọc cấu hình `OLLAMA_URL`, `OLLAMA_MODEL` từ `.env`.
  - Gửi POST tới `/api/generate` với `stream=False`.
  - Trả về `LLMResponse` gồm `answer`, `model`, và `raw` JSON.
- **Xử lý lỗi**: Nếu không kết nối được hoặc response không hợp lệ → ném `LLMClientError` kèm thông tin dễ debug.

## 4. `rag_service.py`
- **Mục tiêu**: Orchestrate toàn bộ flow.
- **Flow**:
  1. `retrieve_similar_chunks` → lấy context.
  2. `build_rag_prompt` → tạo prompt.
  3. `generate_answer` → hỏi LLM.
  4. Tính thời gian thực thi.
- **Output**: Dict gồm `answer`, `sources`, `metadata`, `prompt`, `raw_llm_response`.
  - `metadata`: mô hình, thời gian (ms), số chunk sử dụng.

## 5. `scripts/rag_query.py`
- **Vai trò**: CLI test nhanh quy trình RAG.
- **Usage**:
  ```bash
  python scripts/rag_query.py --query "LangChain là gì?" --document-id <uuid> --top-k 5 --pretty
  ```
- **Tuỳ chọn**:
  - `--show-prompt`: In prompt gửi lên LLM.
  - `--pretty`: In JSON đẹp mắt.

## 6. Các biến môi trường mới
- `OLLAMA_URL`: Mặc định `http://localhost:11434`.
- `OLLAMA_MODEL`: Mặc định `llama3`.

## 7. Kiến thức thêm cho phase tiếp theo
- Backend Express sẽ gọi `rag_service.rag_query` (qua subprocess) để trả về kết quả.
- Frontend sẽ hiển thị `answer` + `sources` và metadata.
- Nếu muốn tối ưu hiệu năng: nên tạo stored procedure để filter vector similarity trực tiếp trong Postgres thay vì tải toàn bộ chunk.
