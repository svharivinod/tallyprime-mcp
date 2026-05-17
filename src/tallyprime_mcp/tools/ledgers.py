"""tools/ledgers.py — ledger and group tools"""
import json
from ..tally_client import TallyClient, TallyError


def register(mcp, client: TallyClient):

    @mcp.tool()
    async def get_all_ledgers() -> str:
        """Get all ledgers in TallyPrime with their group and closing balance."""
        try:
            ledgers = await client.get_all_ledgers()
            if not ledgers:
                return "No ledgers found."
            text = f"Found {len(ledgers)} ledgers:\n\n"
            for l in ledgers:
                text += f"  * {l['name']}  (Group: {l['group']},  Balance: {l['closing']})\n"
            return text
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def get_ledger(name: str) -> str:
        """
        Get details and recent vouchers for a specific ledger.

        Args:
            name: Exact ledger name as it appears in TallyPrime (case-sensitive).
        """
        try:
            data = await client.get_ledger(name)
            return json.dumps(data, indent=2)
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def get_all_groups() -> str:
        """Get all account groups defined in TallyPrime."""
        try:
            groups = await client.get_all_groups()
            if not groups:
                return "No groups found."
            text = f"Found {len(groups)} groups:\n\n"
            for g in groups:
                parent = f"  (under: {g['parent']})" if g["parent"] else ""
                text += f"  * {g['name']}{parent}\n"
            return text
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def create_ledger(name: str, group: str, opening_balance: float = 0.0) -> str:
        """
        Create a new ledger in TallyPrime.

        Args:
            name: Name for the new ledger.
            group: Parent group (e.g. 'Sundry Debtors', 'Bank Accounts').
            opening_balance: Opening balance. Positive=Debit, Negative=Credit. Default 0.
        """
        try:
            result = await client.create_ledger(name, group, opening_balance)
            if result["success"]:
                return f"Ledger '{name}' created successfully under '{group}'."
            return f"Failed to create ledger: {result['message']}"
        except TallyError as e:
            return f"Error: {e}"
