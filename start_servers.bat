@echo off
REM =======================================================
REM Script khởi động RAG Backend Servers
REM =======================================================
REM Tác giả: DACN MindMapNote
REM Mô tả: Script này khởi động 2 servers:
REM   - RAG Server (Port 8001): Tìm kiếm trong tài liệu của user
REM   - Hybrid RAG Server (Port 8002): Tìm kiếm + Web Search (Tavily)
REM =======================================================

echo.
echo ========================================
echo   RAG BACKEND STARTUP
echo ========================================
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python khong duoc cai dat hoac khong o trong PATH
    echo Vui long cai dat Python 3.8+ tu https://python.org
    pause
    exit /b 1
)

REM Kiểm tra thư mục hiện tại
if not exist "api" (
    echo [ERROR] Khong tim thay thu muc 'api'
    echo Vui long chay script tu thu muc Embedding_langchain
    pause
    exit /b 1
)

REM Kiểm tra .env
if not exist ".env" (
    echo [WARNING] Khong tim thay file .env
    echo Vui long copy tu .env.example va dien thong tin
    echo.
    echo cp .env.example .env
    echo.
    pause
)

echo [1/4] Kich hoat Python virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment da duoc kich hoat
) else (
    echo [WARNING] Khong tim thay virtual environment
    echo Dang su dung Python global...
)

echo.
echo [2/4] Kiem tra dependencies...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FastAPI chua duoc cai dat
    echo Dang cai dat dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Cai dat dependencies that bai
        pause
        exit /b 1
    )
)

echo [OK] Dependencies da san sang
echo.

echo [3/4] Khoi dong RAG Server (Port 8001)...
start "RAG Server" cmd /k "python api\rag_server.py"

timeout /t 3 >nul

echo [4/4] Khoi dong Hybrid RAG Server (Port 8002)...
start "Hybrid RAG Server" cmd /k "python api\hybrid_rag_server.py"

echo.
echo ========================================
echo   KHOI DONG THANH CONG!
echo ========================================
echo.
echo Servers dang chay:
echo   - RAG Server:        http://localhost:8001
echo   - Hybrid RAG Server: http://localhost:8002
echo.
echo Kiem tra health:
echo   - curl http://localhost:8001/health
echo   - curl http://localhost:8002/health
echo.
echo Nhan Ctrl+C trong cac cua so terminal de dung servers
echo.

timeout /t 5
