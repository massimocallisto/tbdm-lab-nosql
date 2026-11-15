"""Read the local .env without embedding credentials in source files."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_settings() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError('Install requirements.txt in your virtual environment first') from exc
    load_dotenv(ROOT / '.env', override=False)


def setting(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise RuntimeError(f'{name} is missing. Copy .env.example to .env and edit it.')
    return value


def port(name: str, default: int) -> int:
    value = int(setting(name, str(default)))
    if not 1 <= value <= 65535:
        raise ValueError(f'{name} must be a TCP port between 1 and 65535')
    return value
