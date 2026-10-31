"""Tests for the agent module."""

import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import MarketStatus
from agent import run_agent, get_today_info, build_search_queries


def _mock_search_results(results_data: list[dict]) -> list[dict]:
    """Create mock Tavily search results."""
    return results_data


class TestAgentRunWithMocks:
    """Tests for the run_agent function with mocked external calls."""

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_regular_weekday_open(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should report OPEN for a regular weekday with no holiday."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {
                "content": "NSE and BSE are open today. No trading holiday.",
                "url": "https://www.nseindia.com",
            }
        ]
        mock_search_tool_fn.return_value = mock_search

        expected_result = MarketStatus(
            date="2026-10-30",
            weekday="Friday",
            timezone="Asia/Kolkata",
            market="BOTH",
            status="OPEN",
            is_holiday=False,
            holiday_name=None,
            reason="Regular trading day. No trading holiday for this date.",
            special_session=False,
            session_details=None,
            source_urls=["https://www.nseindia.com"],
            last_verified="2026-10-30T10:00:00+05:30",
        )

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-10-30",
                "weekday": "Friday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-10-30T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "OPEN"
        assert result.weekday == "Friday"

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_saturday_closed(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should report CLOSED on Saturday."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {
                "content": "Stock market closed on weekends.",
                "url": "https://www.nseindia.com",
            }
        ]
        mock_search_tool_fn.return_value = mock_search

        expected_result = MarketStatus(
            date="2026-10-31",
            weekday="Saturday",
            timezone="Asia/Kolkata",
            market="BOTH",
            status="CLOSED",
            is_holiday=False,
            reason="Saturday is a regular non-trading day.",
            special_session=False,
            source_urls=["https://www.nseindia.com"],
            last_verified="2026-10-31T10:00:00+05:30",
        )

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-10-31",
                "weekday": "Saturday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-10-31T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "CLOSED"
        assert result.weekday == "Saturday"

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_trading_holiday_closed(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should report CLOSED on a declared trading holiday."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {
                "content": "NSE and BSE closed for Republic Day holiday.",
                "url": "https://www.nseindia.com/resources/exchange-communication-holidays",
            }
        ]
        mock_search_tool_fn.return_value = mock_search

        expected_result = MarketStatus(
            date="2026-01-26",
            weekday="Monday",
            timezone="Asia/Kolkata",
            market="BOTH",
            status="CLOSED",
            is_holiday=True,
            holiday_name="Republic Day",
            reason="Republic Day is an officially declared trading holiday for NSE and BSE.",
            special_session=False,
            source_urls=["https://www.nseindia.com/resources/exchange-communication-holidays"],
            last_verified="2026-01-26T10:00:00+05:30",
        )

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-01-26",
                "weekday": "Monday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-01-26T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "CLOSED"
        assert result.is_holiday is True
        assert result.holiday_name == "Republic Day"

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_muhurat_trading_special_session(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should report special Muhurat Trading session."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {
                "content": "Muhurat Trading session on Diwali from 18:15 to 19:15.",
                "url": "https://www.nseindia.com",
            }
        ]
        mock_search_tool_fn.return_value = mock_search

        expected_result = MarketStatus(
            date="2026-11-08",
            weekday="Sunday",
            timezone="Asia/Kolkata",
            market="BOTH",
            status="OPEN",
            is_holiday=False,
            reason="Special Muhurat Trading session on Diwali.",
            special_session=True,
            session_details="Muhurat Trading from 18:15 to 19:15 IST",
            source_urls=["https://www.nseindia.com"],
            last_verified="2026-11-08T10:00:00+05:30",
        )

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-11-08",
                "weekday": "Sunday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-11-08T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "OPEN"
        assert result.special_session is True

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_different_nse_bse_status(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should handle different NSE and BSE statuses."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {
                "content": "NSE open, BSE closed for maintenance.",
                "url": "https://example.com",
            }
        ]
        mock_search_tool_fn.return_value = mock_search

        expected_result = MarketStatus(
            date="2026-10-30",
            weekday="Friday",
            timezone="Asia/Kolkata",
            market="NSE",
            status="OPEN",
            is_holiday=False,
            reason="NSE is open. BSE is closed for maintenance.",
            special_session=False,
            source_urls=["https://example.com"],
            last_verified="2026-10-30T10:00:00+05:30",
        )

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-10-30",
                "weekday": "Friday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-10-30T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.market == "NSE"

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_search_failure_returns_unknown(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should return UNKNOWN if search fails."""
        mock_search = MagicMock()
        mock_search.invoke.side_effect = Exception("Tavily API error")
        mock_search_tool_fn.return_value = mock_search

        expected_result = MarketStatus(
            date="2026-10-30",
            weekday="Friday",
            timezone="Asia/Kolkata",
            market="BOTH",
            status="UNKNOWN",
            is_holiday=None,
            reason="Search failed. Unable to verify market status.",
            special_session=False,
            source_urls=[],
            last_verified="2026-10-30T10:00:00+05:30",
        )

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-10-30",
                "weekday": "Friday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-10-30T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "UNKNOWN"

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_cohere_failure_returns_unknown(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should return UNKNOWN if Cohere API fails."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {"content": "Markets open", "url": "https://example.com"}
        ]
        mock_search_tool_fn.return_value = mock_search

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = Exception("Cohere API error")
        mock_llm.with_structured_output.return_value = mock_structured_llm
        # Also make the fallback raw invoke fail
        mock_llm.invoke.side_effect = Exception("Cohere API error")
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-10-30",
                "weekday": "Friday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-10-30T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "UNKNOWN"
        assert "Unable to verify" in result.reason

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_invalid_structured_response_fallback(self, mock_cohere_cls, mock_search_tool_fn):
        """Agent should handle invalid structured response gracefully."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {"content": "Markets open", "url": "https://example.com"}
        ]
        mock_search_tool_fn.return_value = mock_search

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        # Return something that's not a MarketStatus
        mock_structured_llm.invoke.return_value = "invalid response"
        mock_llm.with_structured_output.return_value = mock_structured_llm
        # Fallback also fails
        mock_llm.invoke.side_effect = Exception("Fallback failed")
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-10-30",
                "weekday": "Friday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-10-30T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "UNKNOWN"

    @patch("agent.create_search_tool")
    @patch("agent.ChatCohere")
    def test_settlement_holiday_not_trading_holiday(self, mock_cohere_cls, mock_search_tool_fn):
        """Settlement holiday should not be confused with trading holiday."""
        mock_search = MagicMock()
        mock_search.invoke.return_value = [
            {
                "content": "Settlement holiday today. Markets open for trading.",
                "url": "https://www.nseindia.com",
            }
        ]
        mock_search_tool_fn.return_value = mock_search

        expected_result = MarketStatus(
            date="2026-10-30",
            weekday="Friday",
            timezone="Asia/Kolkata",
            market="BOTH",
            status="OPEN",
            is_holiday=False,
            reason="Settlement holiday but trading is operational.",
            special_session=False,
            source_urls=["https://www.nseindia.com"],
            last_verified="2026-10-30T10:00:00+05:30",
        )

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = expected_result
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_cohere_cls.return_value = mock_llm

        config = {"COHERE_API_KEY": "test-key", "TAVILY_API_KEY": "test-key"}

        with patch("agent.get_today_info") as mock_date:
            mock_date.return_value = {
                "date": "2026-10-30",
                "weekday": "Friday",
                "timezone": "Asia/Kolkata",
                "timestamp": "2026-10-30T10:00:00+05:30",
            }
            result = run_agent(config)

        assert result.status == "OPEN"
        assert result.is_holiday is False
