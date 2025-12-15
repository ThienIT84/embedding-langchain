from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from langchain_community.retrievers import TavilySearchAPIRetriever
from .retriever import RetrievedChunk, retrieve_similar_chunks_by_user

# Thiết lập logging
logger = logging.getLogger(__name__)

@dataclass
class HybridRetrievalResult:
    """Kết quả retrieval từ nhiều nguồn."""
    sources: List[RetrievedChunk]
    metadata: Dict[str, Any]

class HybridRetriever:
    """
    Hybrid Retriever kết hợp:
    1. Internal Knowledge Base (Supabase vector search)
    2. External Web Search (Tavily AI)
    """
    
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

    def retrieve(
        self, 
        query: str, 
        user_id: str, 
        document_id: Optional[str] = None,  # ⭐ NEW: Nếu có = chỉ tìm trong file này
        top_k: int = 5,
        include_web: bool = True,
        web_max_results: int = 3,
        internal_max_results: int = 5
    ) -> HybridRetrievalResult:
        """
        QUY TRÌNH HYBRID RETRIEVAL:
        
        1. INTERNAL SEARCH (Supabase):
           - Tìm kiếm trong database documents của user.
           - Dùng Vector Search (pgvector) để tìm các chunk tương đồng.
           
        2. WEB SEARCH (Tavily):
           - Nếu include_web=True -> Gọi Tavily API.
           - Tìm kiếm thông tin mới nhất trên internet.
           
        3. MERGE & RANK:
           - Gộp kết quả từ cả 2 nguồn.
           - Sắp xếp lại theo điểm số (Similarity Score).
           - Cắt lấy top_k kết quả tốt nhất.
        """
        all_chunks: List[RetrievedChunk] = []
        metadata = {
            "internal_results": 0,
            "web_results": 0,
            "total_results": 0
        }

        # --- BƯỚC 1: INTERNAL RETRIEVAL (Vector Search) ---
        try:
            if document_id:
                # ⭐ Use case: Chat trong context của 1 file cụ thể
                # VD: User đang xem file PDF và hỏi "Bài báo này nói về gì?"
                from .retriever import retrieve_similar_chunks_by_document
                internal_chunks = retrieve_similar_chunks_by_document(
                    query=query,
                    document_id=document_id,
                    top_k=internal_max_results
                )
                logger.info(f"📄 Document-specific retrieval: found {len(internal_chunks)} chunks from document {document_id}")
            else:
                # Use case: Global chat - tìm trong TẤT CẢ documents của user
                internal_chunks = retrieve_similar_chunks_by_user(
                    query=query,
                    user_id=user_id,
                    top_k=internal_max_results
                )
                logger.info(f"📚 Internal retrieval: found {len(internal_chunks)} chunks")
                
            all_chunks.extend(internal_chunks)
            metadata["internal_results"] = len(internal_chunks)
        except Exception as e:
            logger.error(f"❌ Internal retrieval failed: {e}")

        # --- BƯỚC 2: EXTERNAL RETRIEVAL (Tavily Web Search) ---
        if include_web and self.tavily_retriever:
            try:
                # Update k for this request
                self.tavily_retriever.k = web_max_results
                
                # Tavily trả về List[Document] của LangChain
                web_docs = self.tavily_retriever.invoke(query)
                
                # Convert sang RetrievedChunk format
                web_chunks = []
                for i, doc in enumerate(web_docs):
                    # Tính giả lập similarity score (thấp hơn internal một chút để ưu tiên internal)
                    # Hoặc dùng rank để suy ra score: 0.8 - (rank * 0.05)
                    sim_score = 0.85 - (i * 0.05)
                    
                    # Lấy metadata từ Tavily doc
                    source_url = doc.metadata.get('source', 'Unknown URL')
                    title = doc.metadata.get('title', 'Web Result')
                    
                    chunk = RetrievedChunk(
                        content=doc.page_content,
                        chunk_index=i,
                        page_number=None,
                        similarity=sim_score,
                        metadata={
                            'source': 'web',  # Đánh dấu đây là web source
                            'url': source_url,
                            'title': title
                        }
                    )
                    
                    web_chunks.append(chunk)

                all_chunks.extend(web_chunks)
                metadata["web_results"] = len(web_chunks)
                logger.info(f"🌐 Web retrieval: found {len(web_chunks)} results")
                
            except Exception as e:
                logger.error(f"❌ Web retrieval failed: {e}")

        # --- BƯỚC 3: RE-RANKING / SORTING (Simple merge based on similarity) ---
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
