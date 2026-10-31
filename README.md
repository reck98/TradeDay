# Indian Stock Market Holiday Checker 🇮🇳📈

An AI-powered agent that determines whether the Indian stock market (NSE and BSE) is **OPEN** or **CLOSED** today by searching the internet for current information.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────┐
│  Python      │ ──▶ │ Tavily Search │ ──▶ │ Cohere LLM │ ──▶ │ Pydantic │
│  (date/tz)   │     │ (web results) │     │ (analysis)  │     │ (output) │
└─────────────┘     └──────────────┘     └────────────┘     └──────────┘
```

1. **Python** determines today's date and weekday in the `Asia/Kolkata` timezone.
2. **Tavily Search** retrieves current information about NSE/BSE trading holidays.
3. **Cohere (Command A)** analyzes the search results and determines market status.
4. **Pydantic** validates and structures the final response.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM | Cohere Command A |
| LLM Integration | langchain-cohere |
| Agent Framework | LangChain |
| Search Provider | Tavily Search |
| Search Integration | langchain-tavily |
| Schema Validation | Pydantic |
| Environment Variables | python-dotenv |
| Package Manager | uv |
| Testing | pytest |

## Prerequisites

- **Python 3.11+** installed on your system.
- **uv** package manager. Install from [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/).
- **Cohere API Key** — Sign up at [https://dashboard.cohere.com/](https://dashboard.cohere.com/).
- **Tavily API Key** — Sign up at [https://app.tavily.com/](https://app.tavily.com/).

## Setup

### 1. Clone and enter the project

```bash
cd market-holiday-agent
```

### 2. Install dependencies

```bash
uv sync
```

This will create the `.venv` and install all dependencies from `pyproject.toml` and `uv.lock`.

### 3. Configure environment variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
COHERE_API_KEY=your_actual_cohere_api_key
TAVILY_API_KEY=your_actual_tavily_api_key
```

### How to obtain API keys

**Cohere API Key:**
1. Visit [https://dashboard.cohere.com/](https://dashboard.cohere.com/).
2. Sign up or log in.
3. Navigate to API Keys.
4. Create a new key or copy an existing one.

**Tavily API Key:**
1. Visit [https://app.tavily.com/](https://app.tavily.com/).
2. Sign up or log in.
3. Copy your API key from the dashboard.

## Usage

### Check market status (human-readable)

```bash
uv run python main.py
```

Example output:

```text
==================================================
          INDIAN STOCK MARKET STATUS
==================================================

Date       : 2026-10-31 (Saturday)
Timezone   : Asia/Kolkata
Market     : NSE + BSE

Status     : CLOSED

Reason:
  Saturday is a regular non-trading day. No
  exceptional trading session was identified.

Special Session: No

Verified Sources:
  1. https://www.nseindia.com

Last Verified: 2026-10-31T10:00:00+05:30

==================================================
```

### Check market status (JSON)

```bash
uv run python main.py --json
```

Returns a structured JSON response:

```json
{
  "date": "2026-10-31",
  "weekday": "Saturday",
  "timezone": "Asia/Kolkata",
  "market": "BOTH",
  "status": "CLOSED",
  "is_holiday": false,
  "holiday_name": null,
  "reason": "Saturday is a regular non-trading day.",
  "special_session": false,
  "session_details": null,
  "source_urls": ["https://www.nseindia.com"],
  "last_verified": "2026-10-31T10:00:00+05:30"
}
```

## Structured Output

The agent returns a `MarketStatus` Pydantic model with validated fields:

| Field | Type | Description |
|---|---|---|
| `date` | str | Date in YYYY-MM-DD format |
| `weekday` | str | Weekday name |
| `timezone` | str | Always "Asia/Kolkata" |
| `market` | str | NSE, BSE, or BOTH |
| `status` | Literal | OPEN, CLOSED, or UNKNOWN |
| `is_holiday` | bool/None | Whether today is a trading holiday |
| `holiday_name` | str/None | Holiday name, if applicable |
| `reason` | str | Explanation of the result |
| `special_session` | bool | Whether a special session exists |
| `session_details` | str/None | Special session details |
| `source_urls` | list[str] | Sources used for verification |
| `last_verified` | str | ISO 8601 verification timestamp |

The agent uses LangChain's `with_structured_output()` to request the LLM to return a response matching the Pydantic schema. Deterministic fields (date, weekday, timezone) are enforced by Python, not the LLM.

## Testing

Run all tests:

```bash
uv run pytest
```

Run tests with verbose output:

```bash
uv run pytest -v
```

Tests mock external API calls (Cohere and Tavily) and cover:
- Regular weekday, Saturday, and Sunday handling
- Trading holidays and settlement holidays
- Muhurat Trading and special sessions
- Different NSE/BSE statuses
- API failures and error handling
- Schema validation and date formatting

## Project Structure

```
market-holiday-agent/
├── main.py          # Entry point and terminal output
├── config.py        # Environment variables and configuration
├── agent.py         # LangChain agent initialization and execution
├── tools.py         # Tavily search tool setup
├── schemas.py       # Pydantic MarketStatus model
├── prompts.py       # Agent system instructions
├── tests/
│   ├── __init__.py
│   ├── test_date.py          # Date utility tests
│   ├── test_market_status.py # Schema validation tests
│   └── test_agent.py         # Agent integration tests
├── .env.example     # Example environment configuration
├── .gitignore
├── pyproject.toml   # Project metadata and dependencies
├── uv.lock          # Locked dependency versions
└── README.md
```

## License

MIT
