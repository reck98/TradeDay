"""Tavily web search tool for the market holiday checker agent."""

from langchain_tavily import TavilySearch


def create_search_tool(max_results: int = 5, tavily_api_key: str | None = None) -> TavilySearch:
    """Create a Tavily search tool for web searches.

    Args:
        max_results: Maximum number of search results to return.
        tavily_api_key: Optional Tavily API key.

    Returns:
        Configured TavilySearch tool instance.
    """
    kwargs = {
        "max_results": max_results,
        "search_depth": "advanced",
        "topic": "general",
        "include_answer": True,
        "include_raw_content": False,
    }
    if tavily_api_key:
        kwargs["tavily_api_key"] = tavily_api_key
    return TavilySearch(**kwargs)
