"""Unit tests that do not need nflverse downloads."""

from __future__ import annotations

import pandas as pd

from pbp_store import coverage_two_high, enrich
from search import Query, apply_query


def test_coverage_tokens():
    s = pd.Series(["COVER_4", "COVER 1", "Quarters", None, "2-MAN"])
    flags = coverage_two_high(s)
    assert list(flags) == [True, False, True, False, True]


def test_enrich_proxy():
    df = pd.DataFrame(
        {
            "defense_coverage_type": ["COVER_2", None, "COVER_3"],
            "n_defense_box": [8, 5, 5],
            "play_type": ["pass", "pass", "pass"],
        }
    )
    out = enrich(df)
    assert list(out["two_high"]) == [True, True, False]
    assert list(out["two_high_source"]) == ["coverage", "light_box_proxy", ""]


def test_apply_query():
    df = pd.DataFrame(
        {
            "season": [2024, 2024, 2025],
            "season_type": ["REG", "REG", "REG"],
            "posteam": ["KC", "KC", "BUF"],
            "defteam": ["BUF", "SF", "KC"],
            "down": [3, 3, 1],
            "ydstogo": [8, 3, 10],
            "epa": [0.4, -0.2, 1.1],
            "two_high": [True, False, True],
            "play_type": ["pass", "run", "pass"],
        }
    )
    hits = apply_query(df, Query(posteam="KC", down=3, ydstogo_min=7, two_high=True))
    assert len(hits) == 1
    assert hits.iloc[0]["epa"] == 0.4
