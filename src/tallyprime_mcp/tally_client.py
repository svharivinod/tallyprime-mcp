import xml.etree.ElementTree as ET
from typing import Any
import httpx
from .config import TALLY_URL, TALLY_TIMEOUT


class TallyError(Exception):
    pass


class TallyClient:

    def __init__(self, url: str = TALLY_URL, timeout: int = TALLY_TIMEOUT):
        self.url = url.rstrip("/")
        self.timeout = timeout
        self._client = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *_):
        if self._client:
            await self._client.aclose()

    async def send_xml(self, xml: str) -> str:
        try:
            if self._client is not None:
                response = await self._client.post(
                    self.url,
                    content=xml.encode("utf-8"),
                    headers={"Content-Type": "application/xml"},
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as tmp:
                    response = await tmp.post(
                        self.url,
                        content=xml.encode("utf-8"),
                        headers={"Content-Type": "application/xml"},
                    )
            response.raise_for_status()
            return response.text
        except httpx.ConnectError:
            raise TallyError(f"Cannot connect to TallyPrime at {self.url}.")
        except httpx.TimeoutException:
            raise TallyError(f"TallyPrime did not respond within {self.timeout}s.")
        except httpx.HTTPStatusError as e:
            raise TallyError(f"TallyPrime HTTP error: {e.response.status_code}")

    @staticmethod
    def _parse(xml_text: str) -> ET.Element:
        import re
        # Remove invalid XML characters that TallyPrime sometimes includes
        clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_text)
        try:
            return ET.fromstring(clean)
        except ET.ParseError as e:
            raise TallyError(f"Could not parse Tally XML: {e}")

    @staticmethod
    def _check_import_result(root: ET.Element) -> dict:
        created = root.findtext(".//CREATED") or "0"
        altered = root.findtext(".//ALTERED") or "0"
        error = root.findtext(".//LINEERROR") or root.findtext(".//ERROR")
        if error:
            return {"success": False, "message": error.strip()}
        return {"success": True, "created": int(created), "altered": int(altered), "message": f"Created: {created}, Altered: {altered}"}

    @staticmethod
    def _elem_to_dict(elem: ET.Element) -> dict:
        result = {}
        for child in elem:
            tag = child.tag
            value = TallyClient._elem_to_dict(child) if len(child) else (child.text or "").strip()
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(value)
            else:
                result[tag] = value
        return result

    async def get_active_company(self) -> dict:
        import re
        from .xml_builder import get_all_ledgers_xml
        raw = await self.send_xml(get_all_ledgers_xml())
        match = re.search(r"<SVCURRENTCOMPANY>(.*?)</SVCURRENTCOMPANY>", raw)
        name = match.group(1).strip() if match else "Unknown"
        return {"company": name}

    async def get_all_ledgers(self) -> list:
        from .xml_builder import get_all_ledgers_xml
        raw = await self.send_xml(get_all_ledgers_xml())
        root = self._parse(raw)
        return [{"name": (l.findtext("NAME") or l.get("NAME") or "").strip(), "group": (l.findtext("PARENT") or "").strip(), "closing": (l.findtext("CLOSINGBALANCE") or "0").strip()} for l in root.iter("LEDGER")]

    async def get_ledger(self, name: str) -> dict:
        from .xml_builder import get_ledger_xml
        return self._elem_to_dict(self._parse(await self.send_xml(get_ledger_xml(name))))

    async def get_all_groups(self) -> list:
        from .xml_builder import get_all_groups_xml
        raw = await self.send_xml(get_all_groups_xml())
        root = self._parse(raw)
        return [{"name": (g.findtext("NAME") or g.get("NAME") or "").strip(), "parent": (g.findtext("PARENT") or "").strip()} for g in root.iter("GROUP")]

    async def create_ledger(self, name: str, group: str, opening_balance: float = 0.0) -> dict:
        from .xml_builder import create_ledger_xml
        return self._check_import_result(self._parse(await self.send_xml(create_ledger_xml(name, group, opening_balance))))

    async def get_vouchers(self, from_date: str, to_date: str, voucher_type: str = "") -> list:
        from .xml_builder import get_vouchers_xml
        raw = await self.send_xml(get_vouchers_xml(from_date, to_date, voucher_type))
        root = self._parse(raw)
        return [{"date": (v.findtext("DATE") or "").strip(), "type": (v.findtext("VOUCHERTYPENAME") or "").strip(), "number": (v.findtext("VOUCHERNUMBER") or "").strip(), "narration": (v.findtext("NARRATION") or "").strip(), "amount": (v.findtext("AMOUNT") or "0").strip()} for v in root.iter("VOUCHER")]

    async def create_sales_voucher(self, **kwargs) -> dict:
        from .xml_builder import create_sales_voucher_xml
        return self._check_import_result(self._parse(await self.send_xml(create_sales_voucher_xml(**kwargs))))

    async def create_purchase_voucher(self, **kwargs) -> dict:
        from .xml_builder import create_purchase_voucher_xml
        return self._check_import_result(self._parse(await self.send_xml(create_purchase_voucher_xml(**kwargs))))

    async def create_payment_voucher(self, **kwargs) -> dict:
        from .xml_builder import create_payment_voucher_xml
        return self._check_import_result(self._parse(await self.send_xml(create_payment_voucher_xml(**kwargs))))

    async def create_receipt_voucher(self, **kwargs) -> dict:
        from .xml_builder import create_receipt_voucher_xml
        return self._check_import_result(self._parse(await self.send_xml(create_receipt_voucher_xml(**kwargs))))

    async def create_journal_voucher(self, **kwargs) -> dict:
        from .xml_builder import create_journal_voucher_xml
        return self._check_import_result(self._parse(await self.send_xml(create_journal_voucher_xml(**kwargs))))

    async def get_trial_balance(self, from_date: str, to_date: str) -> dict:
        from .xml_builder import get_trial_balance_xml
        return self._elem_to_dict(self._parse(await self.send_xml(get_trial_balance_xml(from_date, to_date))))

    async def get_balance_sheet(self, as_of_date: str) -> dict:
        from .xml_builder import get_balance_sheet_xml
        return self._elem_to_dict(self._parse(await self.send_xml(get_balance_sheet_xml(as_of_date))))

    async def get_profit_loss(self, from_date: str, to_date: str) -> dict:
        from .xml_builder import get_profit_loss_xml
        return self._elem_to_dict(self._parse(await self.send_xml(get_profit_loss_xml(from_date, to_date))))

    async def get_stock_summary(self, as_of_date: str) -> dict:
        from .xml_builder import get_stock_summary_xml
        return self._elem_to_dict(self._parse(await self.send_xml(get_stock_summary_xml(as_of_date))))

    async def get_outstanding_receivables(self, as_of_date: str, party_name: str = "") -> dict:
        from .xml_builder import get_outstanding_receivables_xml
        return self._elem_to_dict(self._parse(await self.send_xml(get_outstanding_receivables_xml(as_of_date, party_name))))