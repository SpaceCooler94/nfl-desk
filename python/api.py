#!/usr/bin/env python3
"""Local search + report API for NFL Desk.

  uvicorn api:app --reload --port 8787
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pbp_store import DEFAULT_SEASONS, load_slim
from report_third_long import report as third_long_report
from search import Query as SitQuery
from search import search as run_search

app = FastAPI(title="NFL Desk PBP", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=4)
def _df(seasons: tuple[int, ...]):
    return load_slim(list(seasons))


def _seasons(raw: str | None) -> list[int]:
    if not raw:
        return list(DEFAULT_SEASONS)
    return [int(s) for s in raw.split(",") if s.strip()]


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/search")
def search_plays(
    seasons: str | None = None,
    posteam: str | None = None,
    defteam: str | None = None,
    down: int | None = None,
    ydstogo_min: float | None = None,
    ydstogo_max: float | None = None,
    qtr: int | None = None,
    play_type: str | None = None,
    two_high: bool | None = None,
    pass_only: bool | None = None,
    shotgun: bool | None = None,
    score_diff_min: float | None = None,
    score_diff_max: float | None = None,
    sort: str = "epa",
    asc: bool = False,
    limit: int = Query(50, ge=1, le=500),
):
    seas = _seasons(seasons)
    q = SitQuery(
        seasons=seas,
        posteam=posteam,
        defteam=defteam,
        down=down,
        ydstogo_min=ydstogo_min,
        ydstogo_max=ydstogo_max,
        qtr=qtr,
        play_type=play_type,
        two_high=two_high,
        pass_only=pass_only,
        shotgun=shotgun,
        score_diff_min=score_diff_min,
        score_diff_max=score_diff_max,
        sort=sort,
        ascending=asc,
        limit=limit,
    )
    return run_search(q, df=_df(tuple(seas)))


@app.get("/reports/third-long-two-high")
def third_long_two_high(
    team: str,
    seasons: str = "2024,2025",
    side: str = Query("offense", pattern="^(offense|defense)$"),
):
    seas = _seasons(seasons)
    return third_long_report(team, seas, side=side)
