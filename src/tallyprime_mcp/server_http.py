"""
server_http.py — HTTP/SSE mode for Claude.ai cloud.
Entry point: tallyprime-mcp-http

Endpoints:
  GET  /health   — health check
  GET  /sse      — MCP SSE stream
  POST /messages — MCP message handler
"""
import logging
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware

from .tally_client import TallyClient
from .tools import register_all
from .config import TALLY_URL, TALLY_TIMEOUT, MCP_HOST, MCP_PORT, MCP_API_KEY

logger = logging.getLogger(__name__)


def build_app():
    mcp = FastMCP("tallyprime-mcp")
    client = TallyClient(url=TALLY_URL, timeout=TALLY_TIMEOUT)
    register_all(mcp, client)

    # Mount MCP's built-in SSE app at /
    sse_app = mcp.sse_app()

    # Add /health on top
    async def health(request: Request):
        return JSONResponse({"status": "ok", "tally_url": TALLY_URL})

    # Auth middleware
    class AuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if request.url.path == "/health":
                return await call_next(request)
            if MCP_API_KEY:
                token = request.headers.get("Authorization", "")
                if token != f"Bearer {MCP_API_KEY}":
                    return JSONResponse({"error": "Unauthorized"}, status_code=401)
            return await call_next(request)

    app = Starlette(routes=[
        Route("/health", health),
        # SSE app handles /sse and /messages internally
        Route("/{path:path}", sse_app),
    ])

    if MCP_API_KEY:
        app.add_middleware(AuthMiddleware)

    return app


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info(f"TallyPrime MCP HTTP server")
    logger.info(f"Tally : {TALLY_URL}")
    logger.info(f"Listen: http://{MCP_HOST}:{MCP_PORT}")
    logger.info(f"Auth  : {'enabled' if MCP_API_KEY else 'disabled'}")
    uvicorn.run(build_app(), host=MCP_HOST, port=MCP_PORT)

if __name__ == "__main__":
    main()
