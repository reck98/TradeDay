"""Entry point for the Indian Stock Market Holiday Checker."""

import argparse
import json
import sys

from schemas import MarketStatus


def format_output(result: MarketStatus) -> str:
    """Format the MarketStatus result for terminal display.

    Args:
        result: The structured market status result.

    Returns:
        Formatted string for terminal output.
    """
    market_display = result.market
    if result.market == "BOTH":
        market_display = "NSE + BSE"

    lines = [
        "",
        "=" * 50,
        "          INDIAN STOCK MARKET STATUS",
        "=" * 50,
        "",
        f"Date       : {result.date} ({result.weekday})",
        f"Timezone   : {result.timezone}",
        f"Market     : {market_display}",
        "",
        f"Status     : {result.status}",
    ]

    if result.is_holiday and result.holiday_name:
        lines.append(f"Holiday    : {result.holiday_name}")

    lines.append("")
    lines.append("Reason:")

    # Word-wrap the reason at ~50 chars per line
    words = result.reason.split()
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 > 50:
            lines.append(f"  {current_line.strip()}")
            current_line = word + " "
        else:
            current_line += word + " "
    if current_line.strip():
        lines.append(f"  {current_line.strip()}")

    lines.append("")
    lines.append(f"Special Session: {'Yes' if result.special_session else 'No'}")

    if result.special_session and result.session_details:
        lines.append(f"  {result.session_details}")

    if result.source_urls:
        lines.append("")
        lines.append("Verified Sources:")
        for i, url in enumerate(result.source_urls, 1):
            lines.append(f"  {i}. {url}")

    lines.append("")
    lines.append(f"Last Verified: {result.last_verified}")

    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Indian Stock Market Holiday Checker",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the result as JSON",
    )
    args = parser.parse_args()

    try:
        from agent import run_agent

        result = run_agent()
    except SystemExit:
        # Config validation already printed the error
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print(format_output(result))


if __name__ == "__main__":
    main()
