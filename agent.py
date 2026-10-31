"""LangChain agent for checking Indian stock market holiday status."""

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage, SystemMessage

from config import load_config
from prompts import SYSTEM_PROMPT
from schemas import MarketStatus
from tools import create_search_tool


def get_today_info() -> dict[str, str]:
    """Get today's date information in the Asia/Kolkata timezone.

    Returns:
        Dictionary with date, weekday, and timezone info.
    """
    tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(tz)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "weekday": now.strftime("%A"),
        "timezone": "Asia/Kolkata",
        "timestamp": now.isoformat(),
    }


def build_search_queries(date_info: dict[str, str]) -> list[str]:
    """Build targeted search queries for Indian stock market holiday status.

    Args:
        date_info: Dictionary containing today's date information.

    Returns:
        List of search query strings.
    """
    date_str = date_info["date"]
    year = date_str[:4]

    return [
        f"NSE BSE trading holiday {date_str} Indian stock market official calendar {year}",
        f"Indian stock market open closed today NSE BSE {date_str}",
    ]


def _extract_search_results(raw_result: object) -> list[str]:
    """Extract readable text from Tavily search results.

    Handles various response formats from TavilySearch.

    Args:
        raw_result: Raw result from TavilySearch.invoke().

    Returns:
        List of formatted result strings.
    """
    extracted: list[str] = []

    if isinstance(raw_result, dict):
        # TavilySearch returns dict with 'results' key
        answer = raw_result.get("answer")
        if answer:
            extracted.append(f"Answer: {answer}")

        results = raw_result.get("results", [])
        for r in results:
            if isinstance(r, dict):
                url = r.get("url", "")
                content = r.get("content", "")
                title = r.get("title", "")
                if content:
                    extracted.append(f"Source: {url}\nTitle: {title}\n{content}")
    elif isinstance(raw_result, list):
        for item in raw_result:
            if isinstance(item, dict):
                url = item.get("url", "")
                content = item.get("content", "")
                if content:
                    extracted.append(f"Source: {url}\n{content}")
            elif isinstance(item, str):
                extracted.append(item)
    elif isinstance(raw_result, str):
        extracted.append(raw_result)

    return extracted


def create_agent(config: dict[str, str]) -> tuple:
    """Create the LangChain agent components.

    Args:
        config: Configuration dictionary with API keys.

    Returns:
        Tuple of (llm, search_tool).
    """
    llm = ChatCohere(
        model="command-a-03-2025",
        cohere_api_key=config["COHERE_API_KEY"],
        temperature=0,
    )

    search_tool = create_search_tool(
        max_results=5,
        tavily_api_key=config.get("TAVILY_API_KEY"),
    )

    return llm, search_tool


def run_agent(config: dict[str, str] | None = None) -> MarketStatus:
    """Run the market holiday checker agent.

    Args:
        config: Optional configuration dictionary. Loaded from env if not provided.

    Returns:
        MarketStatus with the structured result.

    Raises:
        RuntimeError: If the agent fails to produce a valid result.
    """
    if config is None:
        config = load_config()

    # Step 1: Get today's date
    date_info = get_today_info()

    # Step 2: Search the internet
    llm, search_tool = create_agent(config)

    queries = build_search_queries(date_info)
    all_results: list[str] = []

    for query in queries:
        try:
            raw = search_tool.invoke({"query": query})
            extracted = _extract_search_results(raw)
            all_results.extend(extracted)
        except Exception as e:
            all_results.append(f"Search error for query '{query}': {e}")

    if not all_results:
        all_results.append(
            "No search results were retrieved. The agent should report UNKNOWN status."
        )

    # Step 3 & 4: LLM analysis with structured output
    search_context = "\n\n---\n\n".join(all_results)

    user_message = f"""Today's Date Information (deterministic, do not override):
- Date: {date_info['date']}
- Weekday: {date_info['weekday']}
- Timezone: {date_info['timezone']}
- Current Timestamp: {date_info['timestamp']}

Web Search Results:
{search_context}

Based on the above date information and search results, determine whether the Indian stock market (NSE and BSE) is OPEN or CLOSED today. Return the result as a MarketStatus object.

Important:
- Use the date and weekday exactly as provided above.
- Set timezone to "Asia/Kolkata".
- Set last_verified to the current timestamp provided above.
- Only include source_urls from the actual search results above. Do not fabricate URLs.
- If the search results are insufficient or conflicting, set status to "UNKNOWN".
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    # Try structured output with the LLM
    try:
        structured_llm = llm.with_structured_output(MarketStatus)
        result = structured_llm.invoke(messages)

        if isinstance(result, MarketStatus):
            # Enforce deterministic fields from Python — LLM cannot override these
            result.date = date_info["date"]
            result.weekday = date_info["weekday"]
            result.timezone = date_info["timezone"]
            return result
    except Exception:
        pass

    # Fallback: get raw text and try to parse
    try:
        raw_response = llm.invoke(messages)
        content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)

        # Try to extract JSON from the response
        import json
        import re

        # Look for JSON in the response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
        if json_match:
            data = json.loads(json_match.group())
            # Override deterministic fields
            data["date"] = date_info["date"]
            data["weekday"] = date_info["weekday"]
            data["timezone"] = date_info["timezone"]
            data["last_verified"] = date_info["timestamp"]
            return MarketStatus(**data)
    except Exception:
        pass

    # Final fallback: return UNKNOWN
    return MarketStatus(
        date=date_info["date"],
        weekday=date_info["weekday"],
        timezone=date_info["timezone"],
        market="BOTH",
        status="UNKNOWN",
        is_holiday=None,
        holiday_name=None,
        reason="Unable to verify market status. The agent could not retrieve or parse reliable information.",
        special_session=False,
        session_details=None,
        source_urls=[],
        last_verified=date_info["timestamp"],
    )
