"""Tests for the MarketStatus schema."""

import sys
import os

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas import MarketStatus


def _make_status(**overrides) -> dict:
    """Create a valid MarketStatus dict with optional overrides."""
    base = {
        "date": "2026-10-30",
        "weekday": "Friday",
        "timezone": "Asia/Kolkata",
        "market": "BOTH",
        "status": "OPEN",
        "is_holiday": False,
        "holiday_name": None,
        "reason": "Regular trading day.",
        "special_session": False,
        "session_details": None,
        "source_urls": ["https://www.nseindia.com"],
        "last_verified": "2026-10-30T10:00:00+05:30",
    }
    base.update(overrides)
    return base


class TestMarketStatusSchema:
    """Tests for Pydantic MarketStatus model validation."""

    def test_valid_open_status(self):
        """Should accept a valid OPEN status."""
        data = _make_status(status="OPEN")
        result = MarketStatus(**data)
        assert result.status == "OPEN"
        assert result.market == "BOTH"

    def test_valid_closed_status(self):
        """Should accept a valid CLOSED status."""
        data = _make_status(status="CLOSED", is_holiday=True, holiday_name="Diwali")
        result = MarketStatus(**data)
        assert result.status == "CLOSED"
        assert result.holiday_name == "Diwali"

    def test_valid_unknown_status(self):
        """Should accept UNKNOWN status."""
        data = _make_status(status="UNKNOWN", is_holiday=None)
        result = MarketStatus(**data)
        assert result.status == "UNKNOWN"

    def test_invalid_status_value(self):
        """Should reject invalid status values."""
        data = _make_status(status="MAYBE")
        with pytest.raises(ValidationError):
            MarketStatus(**data)

    def test_saturday_closed(self):
        """Should handle Saturday as a closed day."""
        data = _make_status(
            date="2026-10-31",
            weekday="Saturday",
            status="CLOSED",
            reason="Saturday is a regular non-trading day.",
        )
        result = MarketStatus(**data)
        assert result.weekday == "Saturday"
        assert result.status == "CLOSED"

    def test_sunday_closed(self):
        """Should handle Sunday as a closed day."""
        data = _make_status(
            date="2026-11-01",
            weekday="Sunday",
            status="CLOSED",
            reason="Sunday is a regular non-trading day.",
        )
        result = MarketStatus(**data)
        assert result.status == "CLOSED"

    def test_trading_holiday(self):
        """Should handle an officially declared trading holiday."""
        data = _make_status(
            status="CLOSED",
            is_holiday=True,
            holiday_name="Republic Day",
            reason="Republic Day is an officially declared trading holiday.",
        )
        result = MarketStatus(**data)
        assert result.is_holiday is True
        assert result.holiday_name == "Republic Day"

    def test_muhurat_trading_special_session(self):
        """Should handle Muhurat Trading special session."""
        data = _make_status(
            status="OPEN",
            is_holiday=False,
            special_session=True,
            session_details="Muhurat Trading session from 18:15 to 19:15",
            reason="Special Muhurat Trading session on Diwali.",
        )
        result = MarketStatus(**data)
        assert result.special_session is True
        assert result.session_details is not None

    def test_different_nse_bse_status(self):
        """Should allow specifying individual exchange."""
        data_nse = _make_status(market="NSE", status="OPEN")
        data_bse = _make_status(market="BSE", status="CLOSED")
        nse = MarketStatus(**data_nse)
        bse = MarketStatus(**data_bse)
        assert nse.market == "NSE"
        assert bse.market == "BSE"

    def test_settlement_vs_trading_holiday(self):
        """Settlement holiday status should be distinct from trading holiday."""
        # A settlement holiday is NOT a trading holiday
        data = _make_status(
            status="OPEN",
            is_holiday=False,
            reason="Today is a settlement holiday but not a trading holiday. Markets are open.",
        )
        result = MarketStatus(**data)
        assert result.status == "OPEN"
        assert result.is_holiday is False

    def test_conflicting_search_results_unknown(self):
        """When search results conflict, status should be UNKNOWN."""
        data = _make_status(
            status="UNKNOWN",
            is_holiday=None,
            reason="Conflicting information from sources. Unable to verify.",
        )
        result = MarketStatus(**data)
        assert result.status == "UNKNOWN"

    def test_missing_required_field(self):
        """Should reject data missing required fields."""
        with pytest.raises(ValidationError):
            MarketStatus(
                date="2026-10-30",
                weekday="Friday",
                # Missing status, market, reason, last_verified
            )

    def test_invalid_date_format(self):
        """Should reject invalid date format."""
        data = _make_status(date="30-10-2026")
        with pytest.raises(ValidationError):
            MarketStatus(**data)

    def test_source_urls_list(self):
        """Should accept a list of source URLs."""
        data = _make_status(source_urls=[
            "https://www.nseindia.com/resources/exchange-communication-holidays",
            "https://www.bseindia.com/",
        ])
        result = MarketStatus(**data)
        assert len(result.source_urls) == 2

    def test_empty_source_urls(self):
        """Should accept empty source URLs list."""
        data = _make_status(source_urls=[])
        result = MarketStatus(**data)
        assert result.source_urls == []

    def test_json_serialization(self):
        """Should serialize to JSON correctly."""
        data = _make_status()
        result = MarketStatus(**data)
        json_str = result.model_dump_json()
        assert "OPEN" in json_str

    def test_model_dump(self):
        """Should dump to dict correctly."""
        data = _make_status()
        result = MarketStatus(**data)
        dumped = result.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["status"] == "OPEN"
