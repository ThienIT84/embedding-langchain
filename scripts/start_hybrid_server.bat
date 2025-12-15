@echo off
REM Start Hybrid RAG Server on port 8002
cd /d %~dp0\..
echo Starting Hybrid RAG Server...
python api/hybrid_rag_server.py
pause
