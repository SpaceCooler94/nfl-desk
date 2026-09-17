"""Rebuild feed/current.json from nflverse + ratings.py.

Run on a laptop after games land. Commit the JSON. Scriptable pulls it.

  pip install nflreadpy pandas numpy
  python python/export_feed.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ratings import (
    HFA_POINTS,
    current_ratings,
    expected_margin,
    margin_to_win_prob,
    pbp_to_team_games,
    season_priors,
)


SEASON = 2026
THROUGH_WEEK = 1
CARD_WEEK = 2
OUT = Path(__file__).resolve().parents[1] / "feed" / "current.json"


def load_pbp(years):
    try:
        import nflreadpy as nfl

        frame = nfl.load_pbp(list(years))
        return frame.to_pandas()
    except Exception as exc:
        raise SystemExit(
            "nflreadpy unavailable or download failed. "
            "Keep the seed feed and retry later.\n" + str(exc)
        )


def main() -> None:
    pbp = load_pbp([SEASON - 2, SEASON - 1, SEASON])
    games = pbp_to_team_games(pbp)
    priors = season_priors(games, SEASON - 1)
    ratings = current_ratings(games, SEASON, THROUGH_WEEK, priors)

    raw = json.loads(OUT.read_text())
    raw["status"] = "LIVE"
    raw["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    raw["disclaimer"] = (
        f"Live ratings through {SEASON} week {THROUGH_WEEK}. "
        "Still prior-heavy. Edge is vs the number stored in this file."
    )

    rteams = set(ratings["team"])
    updated = []
    for g in raw["games"]:
        if g["home"] in rteams and g["away"] in rteams:
            margin = expected_margin(ratings, g["home"], g["away"])
            g["model_spread"] = round(margin, 1)
            g["home_wp"] = round(margin_to_win_prob(margin), 3)
            if g.get("market_spread") is not None:
                g["edge_spread"] = round(margin - float(g["market_spread"]), 1)
            if g.get("market_total") is not None and g.get("model_total") is not None:
                g["edge_total"] = round(float(g["model_total"]) - float(g["market_total"]), 1)
        updated.append(g)

    raw["week"] = CARD_WEEK
    raw["season"] = SEASON
    raw["games"] = updated
    OUT.write_text(json.dumps(raw, indent=2) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
