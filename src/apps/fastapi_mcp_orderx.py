from fastmcp import FastMCP
from src.apps.fastapi_orderx import app

# Register the FastAPI app with fastmcp for MCP integration.
mcp = FastMCP.from_fastapi(app=app)

# Expose the app object for uvicorn startup as both a FastAPI and MCP-enabled server.
# To run:
# PYTHONPATH=/Users/jbander/Documents/git/wayflow-agents /Users/jbander/.virtualenvs/wayflow-agents/bin/python -m uvicorn src.apps.fastapi_mcp_orderx:app --reload --host 0.0.0.0 --port 8084
