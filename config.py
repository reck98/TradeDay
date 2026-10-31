"""Configuration and environment variable management."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def load_config() -> dict[str, str]:
    """Load and validate required environment variables.

    Returns:
        Dictionary containing validated configuration values.

    Raises:
        SystemExit: If required environment variables are missing.
    """
    # Load .env file from project root
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)

    config: dict[str, str] = {}
    missing: list[str] = []

    required_keys = ["COHERE_API_KEY", "TAVILY_API_KEY"]

    for key in required_keys:
        value = os.getenv(key)
        if not value or value.strip() == "" or value.startswith("your_"):
            missing.append(key)
        else:
            config[key] = value.strip()

    if missing:
        print("ERROR: Missing required environment variables:", file=sys.stderr)
        for key in missing:
            print(f"  - {key}", file=sys.stderr)
        print(
            "\nPlease set them in the .env file. See .env.example for reference.",
            file=sys.stderr,
        )
        sys.exit(1)

    return config
