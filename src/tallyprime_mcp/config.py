"""
Central config — reads from environment / .env file.
Import this everywhere instead of reading os.environ directly.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env if present; no-op if missing

TALLY_URL     = os.getenv("TALLY_URL", "http://localhost:9000")
TALLY_TIMEOUT = int(os.getenv("TALLY_TIMEOUT", "30"))

MCP_HOST      = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT      = int(os.getenv("MCP_PORT", "8000"))
MCP_API_KEY   = os.getenv("MCP_API_KEY", "")  # empty = auth disabled
