"""Pydantic schemas for structured market status response."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class MarketStatus(BaseModel):
    """Structured response for Indian stock market trading status."""

    date: str = Field(
        ...,
        description="Date in YYYY-MM-DD format (e.g. 2026-10-31)",
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v
    weekday: str = Field(
        ...,
        description="Weekday name (e.g., Monday, Tuesday)",
    )
    timezone: str = Field(
        default="Asia/Kolkata",
        description="Timezone used for date determination",
    )
    market: str = Field(
        ...,
        description="Which market(s) this status applies to: NSE, BSE, or BOTH",
    )
    status: Literal["OPEN", "CLOSED", "UNKNOWN"] = Field(
        ...,
        description="Current trading status of the market",
    )
    is_holiday: Optional[bool] = Field(
        default=None,
        description="Whether today is an officially declared trading holiday",
    )
    holiday_name: Optional[str] = Field(
        default=None,
        description="Name of the trading holiday, if applicable",
    )
    reason: str = Field(
        ...,
        description="Concise explanation of why the market is OPEN, CLOSED, or UNKNOWN",
    )
    special_session: bool = Field(
        default=False,
        description="Whether a special trading session (e.g., Muhurat Trading) exists today",
    )
    session_details: Optional[str] = Field(
        default=None,
        description="Details about the special session, if applicable",
    )
    source_urls: list[str] = Field(
        default_factory=list,
        description="URLs of sources used for verification",
    )
    last_verified: str = Field(
        ...,
        description="Verification timestamp in ISO 8601 format",
    )
