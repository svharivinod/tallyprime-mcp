"""tools/vouchers.py — voucher read and create tools"""
from ..tally_client import TallyClient, TallyError


def register(mcp, client: TallyClient):

    @mcp.tool()
    async def get_vouchers(from_date: str, to_date: str, voucher_type: str = "") -> str:
        """
        Fetch vouchers from TallyPrime Day Book for a date range.

        Args:
            from_date: Start date YYYYMMDD (e.g. '20250401').
            to_date: End date YYYYMMDD (e.g. '20250430').
            voucher_type: Filter — 'Sales', 'Purchase', 'Payment', 'Receipt', 'Journal'. Empty = all.
        """
        try:
            vouchers = await client.get_vouchers(from_date, to_date, voucher_type)
            if not vouchers:
                return "No vouchers found for the given period."
            label = f" ({voucher_type})" if voucher_type else ""
            text = f"Found {len(vouchers)} vouchers{label} from {from_date} to {to_date}:\n\n"
            for v in vouchers:
                text += (
                    f"  [{v['date']}]  {v['type']}  #{v['number']}"
                    f"  Amount: {v['amount']}"
                    + (f"  -- {v['narration']}" if v["narration"] else "")
                    + "\n"
                )
            return text
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def create_sales_voucher(
        date: str,
        party_ledger: str,
        sales_ledger: str,
        amount: float,
        narration: str = "",
        tax_ledger: str = "",
        tax_amount: float = 0.0,
    ) -> str:
        """
        Create a sales invoice in TallyPrime.

        Args:
            date: Voucher date YYYYMMDD.
            party_ledger: Customer ledger name (must exist in Tally).
            sales_ledger: Sales account ledger name.
            amount: Invoice amount excluding tax.
            narration: Optional description or invoice number.
            tax_ledger: GST or tax ledger name (optional).
            tax_amount: Tax amount (optional, default 0).
        """
        try:
            result = await client.create_sales_voucher(
                date=date, party_ledger=party_ledger, sales_ledger=sales_ledger,
                amount=amount, narration=narration, tax_ledger=tax_ledger, tax_amount=tax_amount,
            )
            if result["success"]:
                total = amount + tax_amount
                msg = f"Sales voucher created. Party: {party_ledger}, Amount: {amount:.2f}"
                if tax_amount:
                    msg += f" + Tax: {tax_amount:.2f}"
                msg += f", Total: {total:.2f}, Date: {date}"
                return msg
            return f"Failed: {result['message']}"
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def create_purchase_voucher(
        date: str,
        party_ledger: str,
        purchase_ledger: str,
        amount: float,
        narration: str = "",
        tax_ledger: str = "",
        tax_amount: float = 0.0,
    ) -> str:
        """
        Create a purchase invoice in TallyPrime.

        Args:
            date: Voucher date YYYYMMDD.
            party_ledger: Supplier ledger name.
            purchase_ledger: Purchase account ledger name.
            amount: Invoice amount excluding tax.
            narration: Optional description.
            tax_ledger: GST or tax ledger name (optional).
            tax_amount: Tax amount (optional, default 0).
        """
        try:
            result = await client.create_purchase_voucher(
                date=date, party_ledger=party_ledger, purchase_ledger=purchase_ledger,
                amount=amount, narration=narration, tax_ledger=tax_ledger, tax_amount=tax_amount,
            )
            if result["success"]:
                total = amount + tax_amount
                msg = f"Purchase voucher created. Supplier: {party_ledger}, Amount: {amount:.2f}"
                if tax_amount:
                    msg += f" + Tax: {tax_amount:.2f}"
                msg += f", Total: {total:.2f}, Date: {date}"
                return msg
            return f"Failed: {result['message']}"
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def create_payment_voucher(
        date: str,
        bank_ledger: str,
        expense_ledger: str,
        amount: float,
        narration: str = "",
    ) -> str:
        """
        Create a payment voucher in TallyPrime (money going out).

        Args:
            date: Voucher date YYYYMMDD.
            bank_ledger: Bank or cash ledger to pay from.
            expense_ledger: Expense or party ledger to debit.
            amount: Payment amount.
            narration: Optional description or reference.
        """
        try:
            result = await client.create_payment_voucher(
                date=date, bank_ledger=bank_ledger,
                expense_ledger=expense_ledger, amount=amount, narration=narration,
            )
            if result["success"]:
                return f"Payment voucher created. Paid from: {bank_ledger}, To: {expense_ledger}, Amount: {amount:.2f}, Date: {date}"
            return f"Failed: {result['message']}"
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def create_receipt_voucher(
        date: str,
        bank_ledger: str,
        party_ledger: str,
        amount: float,
        narration: str = "",
    ) -> str:
        """
        Create a receipt voucher in TallyPrime (money coming in).

        Args:
            date: Voucher date YYYYMMDD.
            bank_ledger: Bank or cash ledger receiving the payment.
            party_ledger: Customer ledger to credit.
            amount: Receipt amount.
            narration: Optional description or reference.
        """
        try:
            result = await client.create_receipt_voucher(
                date=date, bank_ledger=bank_ledger,
                party_ledger=party_ledger, amount=amount, narration=narration,
            )
            if result["success"]:
                return f"Receipt voucher created. Received in: {bank_ledger}, From: {party_ledger}, Amount: {amount:.2f}, Date: {date}"
            return f"Failed: {result['message']}"
        except TallyError as e:
            return f"Error: {e}"

    @mcp.tool()
    async def create_journal_voucher(
        date: str,
        debit_ledger: str,
        credit_ledger: str,
        amount: float,
        narration: str = "",
    ) -> str:
        """
        Create a journal voucher in TallyPrime (adjustment or contra entry).

        Args:
            date: Voucher date YYYYMMDD.
            debit_ledger: Ledger to debit.
            credit_ledger: Ledger to credit.
            amount: Journal amount.
            narration: Optional description.
        """
        try:
            result = await client.create_journal_voucher(
                date=date, debit_ledger=debit_ledger,
                credit_ledger=credit_ledger, amount=amount, narration=narration,
            )
            if result["success"]:
                return f"Journal voucher created. Dr: {debit_ledger}, Cr: {credit_ledger}, Amount: {amount:.2f}, Date: {date}"
            return f"Failed: {result['message']}"
        except TallyError as e:
            return f"Error: {e}"
