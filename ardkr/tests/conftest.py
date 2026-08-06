"""Test-session setup: load the repository root ``.env`` before imports."""

from __future__ import annotations

import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _load_root_env() -> None:
    env_file = REPOSITORY_ROOT / ".env"
    if not env_file.is_file():
        return

    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()

        name, separator, value = line.partition("=")
        if not separator:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name.strip(), value)


_load_root_env()
