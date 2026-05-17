"""
xml_builder.py
--------------
Builds TDL (Tally Definition Language) XML request strings.

Every function returns a raw XML string ready to POST to TallyPrime.
We use plain string templates (not ElementTree) because TDL XML is
sometimes non-standard and string templates are easier to read/extend.
"""


def _envelope(body: str) -> str:
    """Wrap a body fragment in the standard Tally envelope."""
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        {body}
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def _collection_envelope(collection_xml: str) -> str:
    """Wrap a collection request (used for lists of objects)."""
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Accounts</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        {collection_xml}
      </REQUESTDATA>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

def get_active_company_xml() -> str:
    return """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Companies</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


# ---------------------------------------------------------------------------
# Ledgers
# ---------------------------------------------------------------------------

def get_all_ledgers_xml() -> str:
    return """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Accounts</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <ACCOUNTTYPE>Ledgers</ACCOUNTTYPE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def get_ledger_xml(name: str) -> str:
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Ledger Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <LEDGERNAME>{name}</LEDGERNAME>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def get_all_groups_xml() -> str:
    return """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Accounts</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <ACCOUNTTYPE>Groups</ACCOUNTTYPE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def create_ledger_xml(name: str, group: str, opening_balance: float = 0.0) -> str:
    bal_tag = ""
    if opening_balance != 0.0:
        dr_cr = "Dr" if opening_balance > 0 else "Cr"
        bal_tag = f"<OPENINGBALANCE>{abs(opening_balance)} {dr_cr}</OPENINGBALANCE>"

    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Import Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>All Masters</REPORTNAME>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <LEDGER NAME="{name}" ACTION="Create">
            <NAME>{name}</NAME>
            <PARENT>{group}</PARENT>
            {bal_tag}
          </LEDGER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>"""


# ---------------------------------------------------------------------------
# Vouchers — read
# ---------------------------------------------------------------------------

def get_vouchers_xml(from_date: str, to_date: str, voucher_type: str = "") -> str:
    """
    from_date / to_date: YYYYMMDD strings
    voucher_type: e.g. "Sales", "Purchase", "" for all
    """
    vtype_tag = f"<VOUCHERTYPENAME>{voucher_type}</VOUCHERTYPENAME>" if voucher_type else ""
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Day Book</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVFROMDATE>{from_date}</SVFROMDATE>
          <SVTODATE>{to_date}</SVTODATE>
          {vtype_tag}
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


# ---------------------------------------------------------------------------
# Vouchers — create
# ---------------------------------------------------------------------------

def _voucher_import_envelope(voucher_xml: str) -> str:
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Import Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          {voucher_xml}
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>"""


def create_sales_voucher_xml(
    date: str,
    party_ledger: str,
    sales_ledger: str,
    amount: float,
    narration: str = "",
    tax_ledger: str = "",
    tax_amount: float = 0.0,
) -> str:
    total = amount + tax_amount
    tax_entry = ""
    if tax_ledger and tax_amount:
        tax_entry = f"""<ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{tax_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{tax_amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>"""

    voucher = f"""<VOUCHER ACTION="Create" VCHTYPE="Sales">
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
          <NARRATION>{narration}</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{party_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{total}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{sales_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          {tax_entry}
        </VOUCHER>"""
    return _voucher_import_envelope(voucher)


def create_purchase_voucher_xml(
    date: str,
    party_ledger: str,
    purchase_ledger: str,
    amount: float,
    narration: str = "",
    tax_ledger: str = "",
    tax_amount: float = 0.0,
) -> str:
    total = amount + tax_amount
    tax_entry = ""
    if tax_ledger and tax_amount:
        tax_entry = f"""<ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{tax_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{tax_amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>"""

    voucher = f"""<VOUCHER ACTION="Create" VCHTYPE="Purchase">
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
          <NARRATION>{narration}</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{party_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{total}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{purchase_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          {tax_entry}
        </VOUCHER>"""
    return _voucher_import_envelope(voucher)


def create_payment_voucher_xml(
    date: str,
    bank_ledger: str,
    expense_ledger: str,
    amount: float,
    narration: str = "",
) -> str:
    voucher = f"""<VOUCHER ACTION="Create" VCHTYPE="Payment">
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
          <NARRATION>{narration}</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{expense_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{bank_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>"""
    return _voucher_import_envelope(voucher)


def create_receipt_voucher_xml(
    date: str,
    bank_ledger: str,
    party_ledger: str,
    amount: float,
    narration: str = "",
) -> str:
    voucher = f"""<VOUCHER ACTION="Create" VCHTYPE="Receipt">
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
          <NARRATION>{narration}</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{bank_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{party_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>"""
    return _voucher_import_envelope(voucher)


def create_journal_voucher_xml(
    date: str,
    debit_ledger: str,
    credit_ledger: str,
    amount: float,
    narration: str = "",
) -> str:
    voucher = f"""<VOUCHER ACTION="Create" VCHTYPE="Journal">
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
          <NARRATION>{narration}</NARRATION>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{debit_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{credit_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{amount}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>"""
    return _voucher_import_envelope(voucher)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def get_trial_balance_xml(from_date: str, to_date: str) -> str:
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Trial Balance</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVFROMDATE>{from_date}</SVFROMDATE>
          <SVTODATE>{to_date}</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def get_balance_sheet_xml(as_of_date: str) -> str:
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Balance Sheet</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVTODATE>{as_of_date}</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def get_profit_loss_xml(from_date: str, to_date: str) -> str:
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Profit and Loss</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVFROMDATE>{from_date}</SVFROMDATE>
          <SVTODATE>{to_date}</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def get_stock_summary_xml(as_of_date: str) -> str:
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Stock Summary</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVTODATE>{as_of_date}</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""


def get_outstanding_receivables_xml(as_of_date: str, party_name: str = "") -> str:
    party_tag = f"<PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>" if party_name else ""
    return f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Bills Receivable</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVTODATE>{as_of_date}</SVTODATE>
          {party_tag}
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
