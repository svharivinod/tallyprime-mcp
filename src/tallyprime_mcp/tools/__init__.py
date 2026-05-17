"""Register all MCP tools onto the FastMCP instance."""
from mcp.server.fastmcp import FastMCP
from ..tally_client import TallyClient
from . import company, ledgers, vouchers, reports


def register_all(mcp: FastMCP, client: TallyClient):
    company.register(mcp, client)
    ledgers.register(mcp, client)
    vouchers.register(mcp, client)
    reports.register(mcp, client)
