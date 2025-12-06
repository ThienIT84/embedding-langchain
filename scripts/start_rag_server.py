#!/usr/bin/env python
"""
Khởi động RAG FastAPI server.

Usage:
    python scripts/start_rag_server.py              # Default: port 8001
    python scripts/start_rag_server.py --port 8002  # Custom port
    python scripts/start_rag_server.py --reload     # Development mode với auto-reload

Server URL: http://localhost:8001
API Docs: http://localhost:8001/docs
"""

import sys
from pathlib import Path

# Thêm project root vào sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import uvicorn

def main():
    parser = argparse.ArgumentParser(description='Start RAG FastAPI Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8001, help='Port to bind (default: 8001)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload on code changes')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 Starting RAG FastAPI Server")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"🔄 Auto-reload: {'ON' if args.reload else 'OFF'}")
    print(f"👷 Workers: {args.workers}")
    print("=" * 80)
    print()
    print("💡 TIP: Mở Node.js backend để kết nối:")
    print("   cd mindmapnote2/backend && npm start")
    print()
    print("📚 Endpoints:")
    print(f"   Health check:     http://localhost:{args.port}/health")
    print(f"   RAG query (full): http://localhost:{args.port}/rag/query")
    print(f"   RAG retrieve:     http://localhost:{args.port}/rag/retrieve (FAST - no LLM)")
    print()
    print("=" * 80)
    print()
    
    # Run server
    uvicorn.run(
        "api.rag_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # reload chỉ hoạt động với 1 worker
        log_level="info"
    )

if __name__ == "__main__":
    main()
