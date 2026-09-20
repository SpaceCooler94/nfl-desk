#!/usr/bin/env python3
"""Validate feed/current.json against the sheet contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "feed" / "current.json"


def main() -> int:
    card = json.loads(FEED.read_text())
    games = card.get("games") or []
    props = card.get("props") or []
    ids = {g.get("id") for g in games}
    missing = [p for p in props if p.get("game_id") not in ids]
    empty = [g["id"] for g in games if not any(p.get("game_id") == g["id"] for p in props)]
    print(f"season={card.get('season')} week={card.get('week')} status={card.get('status')}")
    print(f"games={len(games)} props={len(props)} layout={card.get('layout')}")
    if missing:
        print("props with unknown game_id:", [p.get("id") for p in missing])
        return 1
    if empty:
        print("games with no props:", empty)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
