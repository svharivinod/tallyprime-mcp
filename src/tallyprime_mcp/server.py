"""
server.py — stdio mode for Claude Desktop.
Entry point: tallyprime-mcp
"""
from mcp.server.fastmcp import FastMCP
from .tally_client import TallyClient
from .tools import register_all
from .config import TALLY_URL, TALLY_TIMEOUT

mcp = FastMCP("tallyprime-mcp")

_client = TallyClient(url=TALLY_URL, timeout=TALLY_TIMEOUT)
register_all(mcp, _client)

def main():
    mcp.run()

if __name__ == "__main__":
    main()