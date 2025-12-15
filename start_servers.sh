#!/bin/bash
# =======================================================
# Script khởi động RAG Backend Servers (Linux/Mac)
# =======================================================
# Tác giả: DACN MindMapNote
# Mô tả: Script này khởi động 2 servers:
#   - RAG Server (Port 8001): Tìm kiếm trong tài liệu của user
#   - Hybrid RAG Server (Port 8002): Tìm kiếm + Web Search (Tavily)
# =======================================================

echo ""
echo "========================================"
echo "  RAG BACKEND STARTUP"
echo "========================================"
echo ""

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 không được cài đặt"
    echo "Vui lòng cài đặt Python 3.8+ từ https://python.org"
    exit 1
fi

# Kiểm tra thư mục hiện tại
if [ ! -d "api" ]; then
    echo "[ERROR] Không tìm thấy thư mục 'api'"
    echo "Vui lòng chạy script từ thư mục Embedding_langchain"
    exit 1
fi

# Kiểm tra .env
if [ ! -f ".env" ]; then
    echo "[WARNING] Không tìm thấy file .env"
    echo "Vui lòng copy từ .env.example và điền thông tin"
    echo ""
    echo "cp .env.example .env"
    echo ""
fi

echo "[1/4] Kích hoạt Python virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "[OK] Virtual environment đã được kích hoạt"
else
    echo "[WARNING] Không tìm thấy virtual environment"
    echo "Đang sử dụng Python global..."
fi

echo ""
echo "[2/4] Kiểm tra dependencies..."
python3 -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARNING] FastAPI chưa được cài đặt"
    echo "Đang cài đặt dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Cài đặt dependencies thất bại"
        exit 1
    fi
fi

echo "[OK] Dependencies đã sẵn sàng"
echo ""

echo "[3/4] Khởi động RAG Server (Port 8001)..."
python3 api/rag_server.py &
RAG_PID=$!
echo "[OK] RAG Server PID: $RAG_PID"

sleep 3

echo "[4/4] Khởi động Hybrid RAG Server (Port 8002)..."
python3 api/hybrid_rag_server.py &
HYBRID_PID=$!
echo "[OK] Hybrid RAG Server PID: $HYBRID_PID"

echo ""
echo "========================================"
echo "  KHỞI ĐỘNG THÀNH CÔNG!"
echo "========================================"
echo ""
echo "Servers đang chạy:"
echo "  - RAG Server:        http://localhost:8001 (PID: $RAG_PID)"
echo "  - Hybrid RAG Server: http://localhost:8002 (PID: $HYBRID_PID)"
echo ""
echo "Kiểm tra health:"
echo "  - curl http://localhost:8001/health"
echo "  - curl http://localhost:8002/health"
echo ""
echo "Để dừng servers:"
echo "  - kill $RAG_PID"
echo "  - kill $HYBRID_PID"
echo ""

# Giữ script chạy
wait
