# TallyPrime MCP Server

> Talk to your TallyPrime accounting data using plain English — powered by Claude AI.

---

## What is this?

If you've ever used TallyPrime, you know the drill — open the app, navigate through menus, set date ranges, find the right report, and read through dense numbers. It works, but it's not exactly conversational.

This project changes that.

**TallyPrime MCP Server** connects TallyPrime to Claude (Anthropic's AI assistant) using a protocol called MCP (Model Context Protocol). Once set up, you can simply ask Claude things like:

- *"What are my outstanding receivables as of today?"*
- *"Create a sales invoice for ABC Traders for ₹50,000 with 18% GST"*
- *"Show me the P&L for FY 2025-26"*
- *"Which company is currently open in Tally?"*

And Claude will fetch the answer directly from your TallyPrime data — no menu navigation needed.

---

## Why do we need this?

TallyPrime is powerful, but it was designed for accountants who know exactly where every report lives. For everyone else — business owners, managers, founders — it can feel like a maze.

Here are the real problems this project solves:

**Getting information is slow.** To check outstanding receivables you need to open Tally, navigate to the right report, set the date, wait for it to load, and read through rows of numbers. With this project, you just ask. Claude fetches it in seconds.

**You need to know Tally's language.** Tally has its own terminology — voucher types, ledger groups, TDL reports. Most people just want answers, not a lesson in accounting software navigation.

**Tally has no modern API.** Unlike modern software, TallyPrime doesn't have a REST API or webhook system. It communicates over an old XML protocol called TDL. This project handles all of that complexity so you never have to think about it.

**AI cannot access desktop software.** Claude is a cloud-based AI — it has no way to open TallyPrime or read your data directly. This MCP server acts as the secure bridge between them.

**Creating entries is repetitive.** Typing the same kind of voucher every day — same ledgers, same format — is tedious. With this project you can describe the transaction in plain English and Claude creates it in Tally.

In short: this project removes the friction between your brain and your accounting data.

---

## How it works

TallyPrime has a built-in Gateway Server that accepts XML requests on port 9000. This project acts as the bridge — it translates Claude's tool calls into the XML that TallyPrime understands, sends them, parses the response, and returns clean readable text back to Claude.

### Architecture

```
┌─────────────────────────────────────────┐
│                  You                    │
│          (ask in plain English)         │
└──────────────────┬──────────────────────┘
                   │
       ┌───────────┴───────────┐
       │                       │
┌──────▼───────┐       ┌───────▼──────┐
│    Claude    │       │   Claude.ai  │
│   Desktop   │       │  (web/cloud) │
│ (stdio mode) │       │  (SSE mode)  │
└──────┬───────┘       └───────┬──────┘
       │    MCP Protocol       │
       └───────────┬───────────┘
                   │
┌──────────────────▼──────────────────────┐
│         TallyPrime MCP Server           │
│                                         │
│  ┌────────────┐   ┌─────────────────┐   │
│  │ server.py  │   │ server_http.py  │   │
│  │  (stdio)   │   │   (HTTP/SSE)    │   │
│  └─────┬──────┘   └────────┬────────┘   │
│        └─────────┬─────────┘            │
│                  │                      │
│      ┌───────────▼──────────────┐       │
│      │       17 MCP Tools       │       │
│      │  Company · Ledgers ·     │       │
│      │  Vouchers · Reports      │       │
│      └───────────┬──────────────┘       │
│                  │                      │
│   ┌──────────────┴──────────────┐       │
│   │                             │       │
│ ┌─▼────────────┐  ┌─────────────▼──┐   │
│ │tally_client  │  │  xml_builder   │   │
│ │ (HTTP calls) │  │ (TDL XML)      │   │
│ └──────────────┘  └────────────────┘   │
└──────────────────┬──────────────────────┘
                   │ XML over HTTP (port 9000)
        [Cloudflare Tunnel for cloud mode]
                   │
┌──────────────────▼──────────────────────┐
│        TallyPrime Gateway Server        │
│          (your Windows machine)         │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│          Your accounting data           │
└─────────────────────────────────────────┘
```

**Local mode (Claude Desktop):** Everything runs on your machine. Claude Desktop launches the MCP server as a subprocess and communicates over stdio. Your Tally data never leaves your computer.

**Cloud mode (Claude.ai):** The MCP server runs on a cloud host. A Cloudflare Tunnel exposes your local TallyPrime to the internet securely so the cloud server can reach it.

---

## Architecture Components Explained

Here is what each piece in the architecture diagram actually does and why it exists.

### You
The starting point. You type a plain English question or instruction in Claude Desktop or Claude.ai. You don't need to know anything about XML, TDL, or how TallyPrime works internally.

### Claude Desktop
Anthropic's official desktop app for Windows and Mac. It supports MCP servers — meaning it can launch local tools and connect to them. In this project, Claude Desktop reads `claude_desktop_config.json` and automatically starts the `tallyprime-mcp` server every time it opens. Communication happens over stdio (stdin/stdout) — completely local, no internet required.

### Claude.ai (web)
The browser version of Claude at claude.ai. It can also connect to MCP servers, but only ones hosted on the internet. This is why the cloud mode requires a running HTTP server and a Cloudflare Tunnel.

### server.py (stdio mode)
The entry point for Claude Desktop. When Claude Desktop launches `tallyprime-mcp`, this file is what runs. It uses FastMCP's stdio transport to read tool calls from Claude and send responses back. Think of it as the local receptionist — it receives Claude's requests and routes them to the right tool.

### server_http.py (HTTP/SSE mode)
The entry point for Claude.ai cloud. It runs a lightweight web server using uvicorn and starlette, exposing three endpoints — `/health`, `/sse`, and `/messages`. Claude.ai connects via SSE (Server-Sent Events) — a persistent HTTP connection that stays open while Claude is working.

### 17 MCP Tools
Each tool is a Python function that Claude can call by name. Claude reads the tool's description and decides on its own when to use it and what parameters to pass. The tools are organized into four files — `company.py`, `ledgers.py`, `vouchers.py`, and `reports.py`. Every tool catches errors gracefully and returns a clean text response to Claude.

### tally_client.py
The async HTTP client that actually talks to TallyPrime. It sends XML requests to `http://localhost:9000`, reads the response, and parses it into Python dictionaries. It also handles all the error scenarios — connection failures, timeouts, malformed XML, and TallyPrime error responses.

### xml_builder.py
A library of functions that build TDL (Tally Definition Language) XML strings. TallyPrime only understands XML in a very specific format — this file knows all those formats so the rest of the code doesn't have to. Every Tally operation (get ledgers, create voucher, fetch report) has its own XML builder function here.

### Cloudflare Tunnel
Only needed for cloud mode. TallyPrime runs on your local Windows machine behind a firewall — the internet can't reach it directly. Cloudflare Tunnel creates a secure outbound connection from your machine to Cloudflare's network, giving you a public URL (like `https://xyz.trycloudflare.com`) that forwards traffic to your local port 9000. Free to use, no account required for temporary tunnels.

### TallyPrime Gateway Server
TallyPrime's built-in server that listens on port 9000. You enable it via F12 → Advanced Configuration → Enable ODBC Server. It accepts XML requests and responds with XML data from your active company. This is the only part of the architecture that Tally itself provides — everything else in this repo is built around it.

### Your accounting data
The ledgers, vouchers, and reports stored in TallyPrime's database on your machine. This is what everything in this project is ultimately trying to make accessible through natural language.

---

## The 17 MCP Tools

This project registers 17 tools that Claude can call. Each tool is a Python function with a name, description, and input parameters. Claude reads the descriptions and decides on its own which tool to use based on what you ask.

### Company (1 tool)

| Tool | What it does |
|---|---|
| `get_active_company` | Returns the name of the company currently open in TallyPrime |

### Ledgers & Groups (4 tools)

| Tool | What it does |
|---|---|
| `get_all_ledgers` | Lists all ledgers with their parent group and closing balance |
| `get_ledger` | Gets details and voucher history for a specific ledger by name |
| `get_all_groups` | Lists all account groups with their parent hierarchy |
| `create_ledger` | Creates a new ledger under a specified group with optional opening balance |

### Vouchers (6 tools)

| Tool | What it does |
|---|---|
| `get_vouchers` | Fetches vouchers from the Day Book for a date range, with optional type filter |
| `create_sales_voucher` | Creates a sales invoice with party, sales ledger, amount, and optional GST |
| `create_purchase_voucher` | Creates a purchase invoice with supplier, purchase ledger, amount, and optional GST |
| `create_payment_voucher` | Creates a payment entry (money going out) from a bank/cash ledger |
| `create_receipt_voucher` | Creates a receipt entry (money coming in) into a bank/cash ledger |
| `create_journal_voucher` | Creates a journal entry with a debit ledger and credit ledger |

### Reports (6 tools)

| Tool | What it does |
|---|---|
| `get_trial_balance` | Returns the trial balance for a given date range |
| `get_balance_sheet` | Returns the balance sheet as of a specific date |
| `get_profit_loss` | Returns the profit and loss statement for a date range |
| `get_stock_summary` | Returns the stock/inventory summary as of a specific date |
| `get_daybook` | Returns all vouchers across all types for a date range |
| `get_outstanding_receivables` | Returns bills receivable — money owed to you — as of a date |

### Example prompts for each category

```
Company:
  "Which company is currently open in Tally?"

Ledgers:
  "Show me all ledgers"
  "Get details for ABC Traders ledger"
  "Create a ledger called XYZ Suppliers under Sundry Creditors"

Vouchers:
  "Show all sales vouchers for April 2025"
  "Create a sales invoice for ABC Traders for ₹50,000 + 18% GST dated today"
  "Record a payment of ₹15,000 from HDFC Bank to Office Rent"
  "Pass a journal entry: debit Depreciation, credit Machinery, ₹10,000"

Reports:
  "Get the P&L for FY 2025-26"
  "Show balance sheet as of 31 March 2026"
  "What are my outstanding receivables as of today?"
  "Show day book for last week"
```

---

## What can it do?

### Company
| What you ask | What happens |
|---|---|
| "Which company is open in Tally?" | Returns the active company name |

### Ledgers & Groups
| What you ask | What happens |
|---|---|
| "Show me all ledgers" | Lists all ledgers with group and closing balance |
| "Get details for ledger ABC Traders" | Returns voucher history for that ledger |
| "Show all account groups" | Lists all groups with parent hierarchy |
| "Create a new ledger called XYZ under Sundry Debtors" | Creates the ledger in Tally |

### Vouchers
| What you ask | What happens |
|---|---|
| "Show sales vouchers for April 2025" | Returns all sales entries for that period |
| "Create a sales invoice for ABC Traders, ₹50,000 + 18% GST" | Creates the voucher in Tally |
| "Record a purchase from Supplier X for ₹30,000" | Creates a purchase voucher |
| "Record a payment of ₹10,000 from HDFC Bank to Office Rent" | Creates a payment voucher |
| "Record receipt of ₹25,000 from customer DEF into SBI account" | Creates a receipt voucher |
| "Pass a journal entry: debit Repairs, credit Bank, ₹5,000" | Creates a journal voucher |

### Reports
| What you ask | What happens |
|---|---|
| "Get trial balance for Q1 2025" | Returns trial balance for the period |
| "Show balance sheet as of 31 March 2026" | Returns balance sheet |
| "Get P&L for FY 2025-26" | Returns profit and loss statement |
| "Show stock summary as of today" | Returns inventory summary |
| "Get day book for last week" | Returns all vouchers for that period |
| "What are my outstanding receivables?" | Returns bills receivable report |

---

## Project Structure

```
tallyprime-mcp/
├── src/
│   └── tallyprime_mcp/
│       ├── config.py           # Reads settings from .env file
│       ├── server.py           # Runs in Claude Desktop (stdio mode)
│       ├── server_http.py      # Runs in cloud for Claude.ai (HTTP/SSE mode)
│       ├── tally_client.py     # Talks to TallyPrime via XML over HTTP
│       ├── xml_builder.py      # Builds the XML requests TallyPrime understands
│       └── tools/
│           ├── company.py      # get_active_company
│           ├── ledgers.py      # ledger and group tools
│           ├── vouchers.py     # voucher read and create tools
│           └── reports.py      # financial report tools
├── .env.example                # Template for your configuration
├── .gitignore                  # Keeps .env and cache out of git
├── Dockerfile                  # For cloud deployment
├── pyproject.toml              # Package config and dependencies
└── README.md                   # This file
```

---

## Requirements

- **Python 3.11 or higher** (tested on Python 3.14)
- **TallyPrime 3.x or later** running on Windows
- **Claude Desktop** (for local use) or a cloud server (for Claude.ai)

---

## Installation

### Step 1 — Clone the repo

```bash
git clone https://github.com/svharivinod/tallyprime-mcp
cd tallyprime-mcp
```

### Step 2 — Install dependencies

```bash
pip install -e .
```

This installs everything: `mcp`, `httpx`, `uvicorn`, `starlette`, `python-dotenv`.

### Step 3 — Create your .env file

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Mac/Linux
```

Open `.env` and set your Tally URL:

```env
TALLY_URL=http://localhost:9000
TALLY_TIMEOUT=30
```

---

## TallyPrime Setup

TallyPrime needs its Gateway Server switched on before this project can talk to it.

1. Open TallyPrime
2. Press **F12** → click **Advanced Configuration**
3. Set **Enable ODBC Server** → **Yes**
4. Confirm **Port** is **9000**
5. Press **Enter** to save

To verify it's working, run:

```bash
python -c "import httpx; r = httpx.get('http://localhost:9000'); print(r.text)"
```

You should see: `<RESPONSE>TallyPrime Server is Running</RESPONSE>`

---

## Connecting to Claude Desktop

Claude Desktop is Anthropic's desktop app that supports MCP servers.
Download it from: **https://claude.ai/download**

### Step 1 — Find or create the config file

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

### Step 2 — Add this configuration

```json
{
  "mcpServers": {
    "tallyprime": {
      "command": "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Programs\\Python\\Python314\\Scripts\\tallyprime-mcp.exe",
      "env": {
        "TALLY_URL": "http://localhost:9000"
      }
    }
  }
}
```

To find the exact path of `tallyprime-mcp.exe` on your machine, run:

```powershell
where.exe tallyprime-mcp
```

### Step 3 — Restart Claude Desktop

Fully quit Claude Desktop (right-click system tray → Quit) and reopen it.

### Step 4 — Verify

Click the **+** button in the chat input → **Connectors** → you should see **tallyprime** listed with a blue toggle.

---

## Connecting to Claude.ai (Cloud Mode)

For Claude.ai to reach TallyPrime (which runs locally on Windows), you need to:

1. Expose TallyPrime via a tunnel
2. Run this server in HTTP/SSE mode
3. Connect Claude.ai to your server URL

### Step 1 — Create a tunnel with Cloudflare

Install cloudflared from: **https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/**

Then run on your Windows machine:

```bash
cloudflared tunnel --url http://localhost:9000
```

You'll get a URL like `https://random-name.trycloudflare.com`. Copy it.

### Step 2 — Update your .env

```env
TALLY_URL=https://random-name.trycloudflare.com
MCP_API_KEY=your-strong-random-secret
MCP_PORT=8000
```

### Step 3 — Start the HTTP server

```bash
tallyprime-mcp-http
```

### Step 4 — Connect Claude.ai

Go to Claude.ai → Settings → Integrations → Add MCP Server:

```
URL:   https://your-server-domain.com/sse
Token: your-strong-random-secret
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TALLY_URL` | `http://localhost:9000` | TallyPrime Gateway URL |
| `TALLY_TIMEOUT` | `30` | Request timeout in seconds |
| `MCP_HOST` | `0.0.0.0` | HTTP server bind host (cloud mode) |
| `MCP_PORT` | `8000` | HTTP server port (cloud mode) |
| `MCP_API_KEY` | *(empty)* | Bearer token to protect cloud endpoint. Leave blank to disable auth. |

---

## Date Format

All dates use `YYYYMMDD` format. Examples:

| Human date | YYYYMMDD format |
|---|---|
| 1 April 2025 | `20250401` |
| 31 March 2026 | `20260331` |
| 15 August 2025 | `20250815` |

---

## Known Issues and How We Solved Them

Building this wasn't completely straightforward. Here's what we ran into and how we fixed it — so you know what to do if you hit the same things.

### TallyPrime returns invalid XML characters
Tally's XML responses sometimes contain control characters that Python's XML parser rejects. We solved this by cleaning the response with a regex before parsing:
```python
clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_text)
```

### "List of Companies" report doesn't exist in TallyPrime
The `List of Companies` report name returns an error in TallyPrime. Instead, we use the `List of Accounts` request which includes `SVCURRENTCOMPANY` in its response headers — and extract the company name from there using regex.

### Python 3.14 asyncio compatibility
Python 3.14 removed `asyncio.get_event_loop()` in the main thread. We fixed this by letting FastMCP handle its own event loop instead of setting one up manually.

### Claude Desktop needs full path to the executable
Claude Desktop doesn't always inherit Windows PATH. Using just `"command": "tallyprime-mcp"` sometimes fails. The fix is to use the full path:
```
C:\\Users\\username\\AppData\\Local\\Programs\\Python\\Python314\\Scripts\\tallyprime-mcp.exe
```
Run `where.exe tallyprime-mcp` in PowerShell to find yours.

### TallyClient context manager error
The MCP tools were failing with `"Use TallyClient as an async context manager"`. We fixed `send_xml()` to create a temporary `httpx` client when called without a context manager, so tools work in both modes.

### `pip install -e .` fails when Claude Desktop is running
Windows locks the `.exe` file when it's in use. The fix: kill Claude Desktop first with `taskkill /F /IM "Claude.exe"`, then reinstall.

---

## Cloud Deployment

### Docker

```bash
docker build -t tallyprime-mcp .
docker run -d -p 8000:8000 \
  -e TALLY_URL=https://your-tunnel.trycloudflare.com \
  -e MCP_API_KEY=your-secret \
  tallyprime-mcp
```

### Railway (easiest)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables: `TALLY_URL`, `MCP_API_KEY`
4. Railway auto-detects the Dockerfile and deploys

---

## Security Notes

- Never commit your `.env` file — it's already in `.gitignore`
- Always set a strong `MCP_API_KEY` when running in cloud mode
- The `.env.example` file is safe to commit — it has no real values
- Your TallyPrime data never leaves your network in local/stdio mode

---

## Tech Stack

| Layer | Technology |
|---|---|
| MCP framework | `mcp` 1.27+ (Anthropic's official Python SDK) |
| HTTP client | `httpx` (async) |
| XML parsing | `xml.etree.ElementTree` + regex fallback |
| Cloud server | `uvicorn` + `starlette` |
| Config | `python-dotenv` |
| Packaging | `hatchling` via `pyproject.toml` |

---

## License

MIT — free to use, modify and distribute.

---
