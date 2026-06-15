#!/usr/bin/env sh
# Install MCP server deps after core requirements (avoids pip resolution-too-deep).
set -e
cd "$(dirname "$0")/.."
python -m pip install -r requirements.txt
python -m pip install fastmcp==3.4.2
# fastmcp upgrades starlette/uvicorn; pin back for FastAPI 0.115.x compatibility
python -m pip install 'starlette==0.46.2' 'uvicorn[standard]==0.34.2' 'python-multipart==0.0.20'
