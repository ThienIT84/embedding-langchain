from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Literal
from concurrent.futures import ThreadPoolExecutor

from langchain_community.retrievers import TavilySearchAPIRetriever
from .retriever import RetrievedChunk, retrieve_similar_chunks_by_user

# Thiết lập logging
logger = logging.getLogger(__name__)

@dataclass
class HybridRetrievalResult:
    """Kết quả retrieval từ nhiều nguồn."""
    sources: List[RetrievedChunk]
    metadata: Dict[str, Any]

WebSearchMode = Literal["auto", "force-on", "force-off"]

class HybridRetriever:
    """
    Hybrid Retriever kết hợp:
    1. Internal Knowledge Base (Supabase vector search)
    2. External Web Search (Tavily AI)
    
    NEW: Smart web search mode với auto-detection
    """
    
    # Keywords indicating document-specific questions
    DOC_SPECIFIC_KEYWORDS = [
    # --- Tiếng Việt ---
    r"bài (báo|viết|nghiên cứu|survey)",
    r"theo (bài|bài báo|tài liệu)",
    r"trong (bài|bài báo|tài liệu)",
    r"tác giả (cho rằng|nêu|trình bày|đề xuất)",
    r"mục \d+",
    r"hình \d+",
    r"bảng \d+",
    r"phần \d+",
    r"chương \d+",

    # --- Tiếng Anh ---
    r"this (paper|document|article|study|research|survey)",
    r"the (paper|document|article|study|survey)",
    r"according to (this|the)",
    r"author(s)? (state|claim|argue|propose|describe)",
    r"in (section|chapter|page)",
    r"figure \d+",
    r"table \d+",
]

    
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not self.tavily_api_key:
            logger.warning("⚠️ TAVILY_API_KEY not found. Web search will be disabled.")
            self.tavily_retriever = None
        else:
            self.tavily_retriever = TavilySearchAPIRetriever(
                k=3,  # Default web results
                api_key=self.tavily_api_key,
                search_depth="advanced"
            )

    def _should_enable_web_search(
        self,
        mode: WebSearchMode,
        query: str,
        document_id: Optional[str]
    ) -> bool:
        """
        Smart resolution: Quyết định có nên bật tìm kiếm web không.
        
        Logic:
        - force-on: Luôn bật tìm kiếm web
        - force-off: Luôn tắt tìm kiếm web
        - auto: Phát hiện thông minh dựa trên document_id và từ khóa trong query
        """
        if mode == "force-on":
            logger.info("🌐 Tìm kiếm web: BẬT (người dùng chọn)")
            return True
        
        if mode == "force-off":
            logger.info("📚 Tìm kiếm web: TẮT (người dùng chọn)")
            return False
        
        # Auto mode: Phát hiện thông minh
        # Rule 1: Document lock - Nếu đang xem tài liệu cụ thể → tắt web
        if document_id:
            logger.info(f"📄 Tìm kiếm web: TẮT (khóa tài liệu cho {document_id})")
            return False
        
        # Rule 2: Query intent detection - Kiểm tra từ khóa
        query_lower = query.lower()
        for pattern in self.DOC_SPECIFIC_KEYWORDS:
            if re.search(pattern, query_lower):
                logger.info(f"📄 Tìm kiếm web: TẮT (phát hiện từ khóa đặc thù tài liệu: '{pattern}')")
                return False
        
        # Default: Bật tìm kiếm web
        logger.info("🌐 Tìm kiếm web: BẬT (mặc định chế độ tự động)")
        return True
    
    def retrieve(
        self, 
        query: str, 
        user_id: str, 
        document_id: Optional[str] = None,
        web_search_mode: WebSearchMode = "auto",  # ⭐ NEW: Smart mode control
        top_k: int = 5,
        web_max_results: int = 3,
        internal_max_results: int = 5
    ) -> HybridRetrievalResult:
        """
        HYBRID RETRIEVAL với Kiểm Soát Tìm Kiếm Web Thông Minh.
        
        Args:
            query: Câu hỏi của người dùng
            user_id: ID người dùng (cho tìm kiếm nội bộ)
            document_id: Nếu có, CHỈ tìm trong tài liệu này (khóa tài liệu)
            web_search_mode: ⭐ MỚI - "auto" (thông minh), "force-on", "force-off"
            top_k: Tổng số kết quả mong muốn (sau khi gộp)
            web_max_results: Số kết quả web tối đa
            internal_max_results: Số kết quả nội bộ tối đa
            
        Returns:
            HybridRetrievalResult chứa sources và metadata
        """
        # Resolve web search based on mode
        enable_web = self._should_enable_web_search(web_search_mode, query, document_id)
        
        all_chunks: List[RetrievedChunk] = []
        metadata = {
            "internal_results": 0,
            "web_results": 0,
            "total_results": 0,
            "web_search_mode": web_search_mode,
            "web_enabled": enable_web,
        }

        # --- HÀM HỖ TRỢ cho thực thi song song ---
        def _retrieve_internal():
            """Hàm tìm kiếm nội bộ"""
            try:
                if document_id:
                    from .retriever import retrieve_similar_chunks_by_document
                    chunks = retrieve_similar_chunks_by_document(
                        query=query,
                        document_id=document_id,
                        top_k=internal_max_results
                    )
                    logger.info(f"📄 Tìm kiếm trong tài liệu cụ thể: tìm thấy {len(chunks)} đoạn từ tài liệu {document_id}")
                else:
                    chunks = retrieve_similar_chunks_by_user(
                        query=query,
                        user_id=user_id,
                        top_k=internal_max_results
                    )
                    logger.info(f"📚 Tìm kiếm nội bộ: tìm thấy {len(chunks)} đoạn")
                return chunks
            except Exception as e:
                logger.error(f"❌ Tìm kiếm nội bộ thất bại: {e}")
                return []

        def _retrieve_web():
            """Hàm tìm kiếm web"""
            if not enable_web or not self.tavily_retriever:
                return []
            
            try:
                self.tavily_retriever.k = web_max_results
                web_docs = self.tavily_retriever.invoke(query)
                
                web_chunks = []
                for i, doc in enumerate(web_docs):
                    sim_score = 0.45 - (i * 0.05)  # Lower than internal to prioritize docs
                    
                    source_url = doc.metadata.get('source', 'Unknown URL')
                    title = doc.metadata.get('title', 'Web Result')
                    
                    chunk = RetrievedChunk(
                        content=doc.page_content,
                        chunk_index=i,
                        page_number=None,
                        similarity=sim_score,
                        metadata={
                            'source': 'web',
                            'url': source_url,
                            'title': title
                        }
                    )
                    web_chunks.append(chunk)
                
                logger.info(f"🌐 Tìm kiếm web: tìm thấy {len(web_chunks)} kết quả")
                return web_chunks
            except Exception as e:
                logger.error(f"❌ Tìm kiếm web thất bại: {e}")
                return []

        # --- ⚡ THỰC THI SONG SONG: Nội bộ + Web đồng thời ---
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_internal = executor.submit(_retrieve_internal)
            future_web = executor.submit(_retrieve_web)
            
            internal_chunks = future_internal.result()
            web_chunks = future_web.result()
            
            all_chunks.extend(internal_chunks)
            all_chunks.extend(web_chunks)
            
            metadata["internal_results"] = len(internal_chunks)
            metadata["web_results"] = len(web_chunks)

        # 3. Re-ranking / Sorting (Simple merge based on similarity)
        # Internal chunks có cosine similarity thực (0-1).
        # Web chunks có giả lập similarity (0.85 xuống).
        # Sort lại toàn bộ list
        all_chunks.sort(key=lambda x: x.similarity, reverse=True)
        
        # Cắt top_k
        final_chunks = all_chunks[:top_k]
        metadata["total_results"] = len(final_chunks)

        return HybridRetrievalResult(
            sources=final_chunks,
            metadata=metadata
        )

# Singleton instance
hybrid_retriever = HybridRetriever()
