"""Tests for date utility functions."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import get_today_info, build_search_queries


class TestGetTodayInfo:
    """Tests for the get_today_info function."""

    def test_returns_required_keys(self):
        """Should return dict with date, weekday, timezone, timestamp."""
        info = get_today_info()
        assert "date" in info
        assert "weekday" in info
        assert "timezone" in info
        assert "timestamp" in info

    def test_timezone_is_kolkata(self):
        """Should always use Asia/Kolkata timezone."""
        info = get_today_info()
        assert info["timezone"] == "Asia/Kolkata"

    def test_date_format(self):
        """Date should be in YYYY-MM-DD format."""
        info = get_today_info()
        # Validate format by parsing
        datetime.strptime(info["date"], "%Y-%m-%d")

    def test_weekday_is_valid(self):
        """Weekday should be a valid day name."""
        info = get_today_info()
        valid_days = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]
        assert info["weekday"] in valid_days

    @patch("agent.datetime")
    def test_saturday_detection(self, mock_datetime):
        """Should correctly identify Saturday."""
        mock_now = datetime(2026, 10, 31, 10, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        info = get_today_info()
        assert info["weekday"] == "Saturday"
        assert info["date"] == "2026-10-31"

    @patch("agent.datetime")
    def test_sunday_detection(self, mock_datetime):
        """Should correctly identify Sunday."""
        mock_now = datetime(2026, 11, 1, 10, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        info = get_today_info()
        assert info["weekday"] == "Sunday"
        assert info["date"] == "2026-11-01"

    @patch("agent.datetime")
    def test_weekday_detection(self, mock_datetime):
        """Should correctly identify a weekday (Monday)."""
        mock_now = datetime(2026, 10, 26, 10, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        info = get_today_info()
        assert info["weekday"] == "Monday"

    def test_timestamp_is_iso_format(self):
        """Timestamp should be in ISO 8601 format with timezone."""
        info = get_today_info()
        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(info["timestamp"])
        assert parsed.tzinfo is not None

    def test_timezone_boundary_handling(self):
        """Date should reflect Asia/Kolkata timezone, not UTC."""
        info = get_today_info()
        now_kolkata = datetime.now(ZoneInfo("Asia/Kolkata"))
        assert info["date"] == now_kolkata.strftime("%Y-%m-%d")


class TestBuildSearchQueries:
    """Tests for the build_search_queries function."""

    def test_returns_list_of_strings(self):
        """Should return a list of search query strings."""
        date_info = {
            "date": "2026-10-30",
            "weekday": "Friday",
            "timezone": "Asia/Kolkata",
            "timestamp": "2026-10-30T10:00:00+05:30",
        }
        queries = build_search_queries(date_info)
        assert isinstance(queries, list)
        assert all(isinstance(q, str) for q in queries)

    def test_queries_include_date(self):
        """Queries should include the specific date."""
        date_info = {
            "date": "2026-10-30",
            "weekday": "Friday",
            "timezone": "Asia/Kolkata",
            "timestamp": "2026-10-30T10:00:00+05:30",
        }
        queries = build_search_queries(date_info)
        assert any("2026-10-30" in q for q in queries)

    def test_queries_include_year(self):
        """Queries should include the year."""
        date_info = {
            "date": "2026-10-30",
            "weekday": "Friday",
            "timezone": "Asia/Kolkata",
            "timestamp": "2026-10-30T10:00:00+05:30",
        }
        queries = build_search_queries(date_info)
        assert any("2026" in q for q in queries)

    def test_queries_mention_nse_or_bse(self):
        """At least one query should mention NSE or BSE."""
        date_info = {
            "date": "2026-10-30",
            "weekday": "Friday",
            "timezone": "Asia/Kolkata",
            "timestamp": "2026-10-30T10:00:00+05:30",
        }
        queries = build_search_queries(date_info)
        assert any("NSE" in q or "BSE" in q for q in queries)

    def test_queries_not_empty(self):
        """Should return at least one query."""
        date_info = {
            "date": "2026-10-30",
            "weekday": "Friday",
            "timezone": "Asia/Kolkata",
            "timestamp": "2026-10-30T10:00:00+05:30",
        }
        queries = build_search_queries(date_info)
        assert len(queries) > 0
