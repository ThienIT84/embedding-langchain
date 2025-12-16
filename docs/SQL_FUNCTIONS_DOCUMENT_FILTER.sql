-- =====================================================
-- METADATA FILTERING: match_embeddings_by_document
-- =====================================================
-- Tạo function tìm kiếm CHỈ trong 1 document cụ thể
-- Giải quyết vấn đề: Lẫn lộn knowledge giữa các files
-- =====================================================

CREATE OR REPLACE FUNCTION public.match_embeddings_by_document(
    query_embedding vector(768),     -- Vector embedding của câu hỏi
    document_id_filter uuid,         -- ⭐ ID của document cụ thể
    match_count int DEFAULT 5        -- Số kết quả trả về
)
RETURNS TABLE (
    content text,
    chunk_index int,
    page_number int,
    similarity float,
    document_id uuid,
    document_title text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.content,
        de.chunk_index,
        de.page_number,
        1 - (de.embedding <=> query_embedding) AS similarity,
        de.document_id,
        d.title AS document_title
    FROM
        public.document_embeddings de
    INNER JOIN
        public.documents d ON de.document_id = d.id
    WHERE
        de.document_id = document_id_filter  -- ⭐ CHỈ tìm trong document này
    ORDER BY
        de.embedding <=> query_embedding ASC
    LIMIT
        match_count;
END;
$$;

-- Grant quyền execute
GRANT EXECUTE ON FUNCTION public.match_embeddings_by_document(vector(768), uuid, int) TO authenticated;
GRANT EXECUTE ON FUNCTION public.match_embeddings_by_document(vector(768), uuid, int) TO anon;

-- Comment documentation
COMMENT ON FUNCTION public.match_embeddings_by_document IS 
'Tìm chunks văn bản CHỈ trong 1 document cụ thể.
Use case: User đang chat về 1 file cụ thể (VD: "Bài báo này nói về gì?").
Tránh lẫn lộn knowledge giữa các documents khác nhau.';

-- =====================================================
-- Test Query
-- =====================================================
-- SELECT * FROM match_embeddings_by_document(
--     '<embedding_vector>'::vector(768),
--     '<document_uuid>'::uuid,
--     5
-- );
