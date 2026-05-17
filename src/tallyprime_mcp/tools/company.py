"""tools/company.py — get_active_company"""
from ..tally_client import TallyClient, TallyError


def register(mcp, client: TallyClient):

    @mcp.tool()
    async def get_active_company() -> str:
        """Get the currently active company open in TallyPrime."""
        try:
            result = await client.get_active_company()
            return f"Active company: {result['company']}"
        except TallyError as e:
            return f"Error: {e}"
