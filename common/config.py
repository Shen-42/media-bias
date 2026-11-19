"""Load config/config.toml once. Paths are resolved against the repo root."""

import tomllib
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@cache
def load() -> dict:
    with open(ROOT / "config" / "config.toml", "rb") as f:
        return tomllib.load(f)


def path(rel: str) -> Path:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
