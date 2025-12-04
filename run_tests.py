#!/usr/bin/env python
"""Script chạy tests với coverage report."""
import sys
import subprocess
from pathlib import Path

def main():
    """Run pytest with coverage."""
    # Change to Embedding_langchain directory
    project_root = Path(__file__).parent
    
    # Build pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=60",
    ]
    
    # Add any additional arguments from command line
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    print("=" * 60)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("📊 Coverage report: htmlcov/index.html")
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
