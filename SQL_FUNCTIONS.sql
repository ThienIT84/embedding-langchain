-- =====================================================
-- RPC FUNCTION: match_embeddings_by_user
-- =====================================================
-- Mục đích: Tìm các chunks tương đồng nhất với query từ TẤT CẢ documents của user
-- Sử dụng pgvector extension để tính cosine similarity
-- =====================================================

-- Bước 1: Enable pgvector extension (nếu chưa có)
CREATE EXTENSION IF NOT EXISTS vector;

-- Bước 2: Tạo RPC function
CREATE OR REPLACE FUNCTION public.match_embeddings_by_user(
    query_embedding vector(768),     -- Vector embedding của câu hỏi (768 chiều)
    user_id_filter uuid,              -- UUID của user
    match_count int DEFAULT 5         -- Số lượng kết quả trả về (mặc định 5)
)
RETURNS TABLE (
    content text,                     -- Nội dung chunk
    chunk_index int,                  -- Thứ tự chunk trong document
    page_number int,                  -- Số trang (có thể NULL)
    similarity float,                 -- Điểm tương đồng (0-1)
    document_id uuid,                 -- ID của document chứa chunk
    document_title text               -- Tên document (optional, để biết chunk từ file nào)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.content,
        de.chunk_index,
        de.page_number,
        -- Tính cosine similarity bằng pgvector
        -- 1 - cosine distance = cosine similarity
        -- pgvector dùng <=> operator để tính cosine distance
        1 - (de.embedding <=> query_embedding) AS similarity,
        de.document_id,
        d.title AS document_title
    FROM
        public.document_embeddings de
    INNER JOIN
        public.documents d ON de.document_id = d.id
    WHERE
        -- Filter theo user: chỉ lấy documents của user này
        d.created_by = user_id_filter
        -- Optional: Có thể thêm filter theo category, group, etc.
        -- AND d.category_id = some_category_id
        -- AND d.group_id = some_group_id
    ORDER BY
        -- Sort theo similarity giảm dần (cao nhất → thấp nhất)
        de.embedding <=> query_embedding ASC
    LIMIT
        match_count;
END;
$$;

-- Bước 3: Grant quyền execute cho authenticated users
GRANT EXECUTE ON FUNCTION public.match_embeddings_by_user(vector(768), uuid, int) TO authenticated;

-- Bước 4: Comment cho function (documentation)
COMMENT ON FUNCTION public.match_embeddings_by_user IS 
'Tìm các chunks văn bản tương đồng nhất với query từ tất cả documents của user. 
Sử dụng cosine similarity với pgvector extension.
Trả về top_k chunks với similarity score cao nhất.';


-- =====================================================
-- BONUS: Variant function cho search trong 1 document cụ thể
-- =====================================================

CREATE OR REPLACE FUNCTION public.match_embeddings_by_document(
    query_embedding vector(768),     -- Vector embedding của câu hỏi
    document_id_filter uuid,         -- UUID của document cần search
    match_count int DEFAULT 5        -- Số lượng kết quả
)
RETURNS TABLE (
    content text,
    chunk_index int,
    page_number int,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.content,
        de.chunk_index,
        de.page_number,
        1 - (de.embedding <=> query_embedding) AS similarity
    FROM
        public.document_embeddings de
    WHERE
        de.document_id = document_id_filter
    ORDER BY
        de.embedding <=> query_embedding ASC
    LIMIT
        match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION public.match_embeddings_by_document(vector(768), uuid, int) TO authenticated;


-- =====================================================
-- BONUS: Function với threshold filtering
-- =====================================================
-- Chỉ trả về chunks có similarity >= ngưỡng tối thiểu

CREATE OR REPLACE FUNCTION public.match_embeddings_by_user_with_threshold(
    query_embedding vector(768),
    user_id_filter uuid,
    match_count int DEFAULT 5,
    similarity_threshold float DEFAULT 0.5  -- Ngưỡng tối thiểu (0.5 = 50%)
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
        d.created_by = user_id_filter
        -- Filter theo similarity threshold
        AND (1 - (de.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY
        de.embedding <=> query_embedding ASC
    LIMIT
        match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION public.match_embeddings_by_user_with_threshold(vector(768), uuid, int, float) TO authenticated;


-- =====================================================
-- BONUS: Function search trong group (cho collaborative workspace)
-- =====================================================

CREATE OR REPLACE FUNCTION public.match_embeddings_by_group(
    query_embedding vector(768),
    group_id_filter uuid,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    content text,
    chunk_index int,
    page_number int,
    similarity float,
    document_id uuid,
    document_title text,
    created_by_email text  -- Email của người tạo document
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
        d.title AS document_title,
        u.email AS created_by_email
    FROM
        public.document_embeddings de
    INNER JOIN
        public.documents d ON de.document_id = d.id
    LEFT JOIN
        public.users u ON d.created_by = u.id
    WHERE
        d.group_id = group_id_filter
    ORDER BY
        de.embedding <=> query_embedding ASC
    LIMIT
        match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION public.match_embeddings_by_group(vector(768), uuid, int) TO authenticated;


-- =====================================================
-- TEST QUERIES (Chạy để test function)
-- =====================================================

-- Test 1: Search trong documents của 1 user cụ thể
-- SELECT * FROM match_embeddings_by_user(
--     '[0.1, 0.2, ..., 0.768]'::vector(768),  -- Query embedding (fake data)
--     '123e4567-e89b-12d3-a456-426614174000'::uuid,  -- User ID
--     5  -- Top 5 kết quả
-- );

-- Test 2: Search với similarity threshold
-- SELECT * FROM match_embeddings_by_user_with_threshold(
--     '[0.1, 0.2, ..., 0.768]'::vector(768),
--     '123e4567-e89b-12d3-a456-426614174000'::uuid,
--     10,   -- Top 10
--     0.7   -- Chỉ lấy chunks có similarity >= 70%
-- );

-- Test 3: Search trong group
-- SELECT * FROM match_embeddings_by_group(
--     '[0.1, 0.2, ..., 0.768]'::vector(768),
--     'group-uuid-here'::uuid,
--     5
-- );


-- =====================================================
-- PERFORMANCE OPTIMIZATION
-- =====================================================

-- Tạo index cho embedding column để tăng tốc vector search
-- IVFFlat index: Approximate Nearest Neighbor (ANN) search
-- Nhanh hơn nhiều so với brute-force search

-- Option 1: IVFFlat index (cân bằng tốc độ và độ chính xác)
CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx 
ON public.document_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Số lượng clusters (100 phù hợp cho dataset vừa)

-- Option 2: HNSW index (nhanh hơn nhưng tốn RAM hơn)
-- CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx 
-- ON public.document_embeddings 
-- USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- Analyze table để optimize query planner
ANALYZE public.document_embeddings;


-- =====================================================
-- NOTES & BEST PRACTICES
-- =====================================================

/*
1. PGVECTOR OPERATORS:
   - <=> : Cosine distance (0 = giống hệt, 2 = ngược hướng)
   - <-> : Euclidean distance (L2 distance)
   - <#> : Inner product distance

2. SIMILARITY vs DISTANCE:
   - Cosine similarity = 1 - Cosine distance
   - Similarity càng cao → càng giống (0-1)
   - Distance càng thấp → càng giống

3. INDEX TYPES:
   - IVFFlat: Approximate search, cân bằng tốc độ/độ chính xác
   - HNSW: Nhanh hơn nhưng tốn RAM hơn
   - Brute-force (no index): Chậm nhưng chính xác 100%

4. PERFORMANCE TIPS:
   - Luôn dùng index cho production
   - Tune `lists` parameter (IVFFlat) theo dataset size:
     * Small (<10K vectors): lists = 10-50
     * Medium (10K-100K): lists = 100-500
     * Large (>100K): lists = 500-1000
   - ANALYZE table sau mỗi lần insert bulk data

5. SECURITY:
   - Function dùng SECURITY DEFINER nếu cần bypass RLS
   - Validate input parameters (avoid SQL injection)
   - Grant minimal permissions (chỉ EXECUTE cho authenticated)

6. DEBUGGING:
   - Dùng EXPLAIN ANALYZE để check query performance
   - Monitor similarity distribution để tune threshold
   - Log slow queries (> 100ms)
*/
