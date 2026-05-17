"""tools/reports.py — financial report tools"""
import json
from datetime import date as _date
from ..tally_client import TallyClient, TallyError


def _today() -> str:
    return _date.today().strftime("%Y%m%d")


def register(mcp, client: TallyClient):

    @mcp.tool()
    async def get_trial_balance(from_date: str, to_date: str) -> str:
        """
        Get the Trial Balance from TallyPrime.

        Args:
            from_date: Start date YYYYMMDD (e.g. '20250401').
            to_date: End date YYYYMMDD (e.g. '20250930').
        """
        try:
            data = await client.get_trial_balance(from_date, to_date)
            return f"Trial Balance ({from_date} to {to_date}):\n\n" + json.dumps(data, indent=2)
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def get_balance_sheet(as_of_date: str) -> str:
        """
        Get the Balance Sheet from TallyPrime as of a specific date.

        Args:
            as_of_date: Date YYYYMMDD (e.g. '20250331').
        """
        try:
            data = await client.get_balance_sheet(as_of_date)
            return f"Balance Sheet as of {as_of_date}:\n\n" + json.dumps(data, indent=2)
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def get_profit_loss(from_date: str, to_date: str) -> str:
        """
        Get the Profit and Loss statement from TallyPrime.

        Args:
            from_date: Start date YYYYMMDD (e.g. '20250401').
            to_date: End date YYYYMMDD (e.g. '20260331').
        """
        try:
            data = await client.get_profit_loss(from_date, to_date)
            return f"Profit & Loss ({from_date} to {to_date}):\n\n" + json.dumps(data, indent=2)
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def get_stock_summary(as_of_date: str) -> str:
        """
        Get the Stock Summary (inventory) from TallyPrime as of a date.

        Args:
            as_of_date: Date YYYYMMDD (e.g. '20260516').
        """
        try:
            data = await client.get_stock_summary(as_of_date)
            return f"Stock Summary as of {as_of_date}:\n\n" + json.dumps(data, indent=2)
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def get_daybook(from_date: str, to_date: str) -> str:
        """
        Get the Day Book (all vouchers) from TallyPrime for a date range.

        Args:
            from_date: Start date YYYYMMDD.
            to_date: End date YYYYMMDD.
        """
        try:
            vouchers = await client.get_vouchers(from_date, to_date, voucher_type="")
            if not vouchers:
                return "No entries found in the Day Book for this period."
            text = f"Day Book ({from_date} to {to_date}) -- {len(vouchers)} entries:\n\n"
            for v in vouchers:
                text += (
                    f"  [{v['date']}]  {v['type']:<12}  #{v['number']:<10}"
                    f"  {v['amount']:>14}"
                    + (f"  {v['narration']}" if v["narration"] else "")
                    + "\n"
                )
            return text
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def get_outstanding_receivables(as_of_date: str = "", party_name: str = "") -> str:
        """
        Get outstanding receivables (money owed to you) from TallyPrime.

        Args:
            as_of_date: Date YYYYMMDD. Defaults to today if not provided.
            party_name: Filter by a specific customer name (optional).
        """
        try:
            if not as_of_date:
                as_of_date = _today()
            data = await client.get_outstanding_receivables(as_of_date, party_name)
            party_note = f" for '{party_name}'" if party_name else ""
            return f"Outstanding Receivables as of {as_of_date}{party_note}:\n\n" + json.dumps(data, indent=2)
        except TallyError as e:
            return f"Error: {e}"
