#!/usr/bin/env python3
"""Situation search over the slim PBP lake. Sort default: EPA desc."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pbp_store import DEFAULT_SEASONS, load_slim

RESULT_COLS = [
    "season",
    "week",
    "game_id",
    "play_id",
    "posteam",
    "defteam",
    "down",
    "ydstogo",
    "yardline_100",
    "qtr",
    "play_type",
    "pass_location",
    "air_yards",
    "yards_gained",
    "epa",
    "success",
    "cpoe",
    "passer_player_name",
    "receiver_player_name",
    "rusher_player_name",
    "offense_personnel",
    "defense_coverage_type",
    "n_defense_box",
    "number_of_pass_rushers",
    "two_high",
    "two_high_source",
    "is_play_action",
    "is_motion",
    "desc",
]


@dataclass
class Query:
    seasons: list[int] | None = None
    season_type: str = "REG"
    posteam: str | None = None
    defteam: str | None = None
    down: int | None = None
    ydstogo_min: float | None = None
    ydstogo_max: float | None = None
    qtr: int | None = None
    play_type: str | None = None
    two_high: bool | None = None
    shotgun: bool | None = None
    pass_only: bool | None = None
    score_diff_max: float | None = None
    score_diff_min: float | None = None
    yardline_max: float | None = None
    sort: str = "epa"
    ascending: bool = False
    limit: int = 50


def apply_query(df: pd.DataFrame, q: Query) -> pd.DataFrame:
    out = df
    if q.seasons:
        out = out[out["season"].isin(q.seasons)]
    if q.season_type and "season_type" in out.columns:
        out = out[out["season_type"] == q.season_type]
    if q.posteam:
        out = out[out["posteam"] == q.posteam.upper()]
    if q.defteam:
        out = out[out["defteam"] == q.defteam.upper()]
    if q.down is not None:
        out = out[out["down"] == q.down]
    if q.ydstogo_min is not None:
        out = out[out["ydstogo"] >= q.ydstogo_min]
    if q.ydstogo_max is not None:
        out = out[out["ydstogo"] <= q.ydstogo_max]
    if q.qtr is not None:
        out = out[out["qtr"] == q.qtr]
    if q.play_type:
        out = out[out["play_type"] == q.play_type]
    if q.two_high is True and "two_high" in out.columns:
        out = out[out["two_high"] == True]  # noqa: E712
    if q.two_high is False and "two_high" in out.columns:
        out = out[out["two_high"] == False]  # noqa: E712
    if q.shotgun is not None and "shotgun" in out.columns:
        out = out[out["shotgun"] == int(q.shotgun)]
    if q.pass_only:
        if "pass" in out.columns:
            out = out[out["pass"] == 1]
        else:
            out = out[out["play_type"] == "pass"]
    if q.score_diff_min is not None and "score_differential" in out.columns:
        out = out[out["score_differential"] >= q.score_diff_min]
    if q.score_diff_max is not None and "score_differential" in out.columns:
        out = out[out["score_differential"] <= q.score_diff_max]
    if q.yardline_max is not None and "yardline_100" in out.columns:
        out = out[out["yardline_100"] <= q.yardline_max]
    sort_col = q.sort if q.sort in out.columns else "epa"
    out = out.sort_values(sort_col, ascending=q.ascending, na_position="last")
    return out


def to_records(df: pd.DataFrame, limit: int) -> list[dict]:
    cols = [c for c in RESULT_COLS if c in df.columns]
    slim = df[cols].head(int(limit))
    recs = slim.to_dict(orient="records")
    for r in recs:
        for k, v in list(r.items()):
            if pd.isna(v):
                r[k] = None
            elif hasattr(v, "item"):
                r[k] = v.item()
    return recs


def search(q: Query, df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_slim(q.seasons or list(DEFAULT_SEASONS))
    hits = apply_query(df, q)
    epa = pd.to_numeric(hits.get("epa"), errors="coerce") if len(hits) else pd.Series(dtype=float)
    return {
        "n": int(len(hits)),
        "epa_mean": None if epa.empty else float(epa.mean()) if epa.notna().any() else None,
        "success_rate": None
        if "success" not in hits.columns or hits.empty
        else float(pd.to_numeric(hits["success"], errors="coerce").mean()),
        "query": asdict(q),
        "plays": to_records(hits, q.limit),
    }


def _bool_arg(v: str | None) -> bool | None:
    if v is None:
        return None
    return v.lower() in {"1", "true", "yes", "y"}


def main() -> int:
    p = argparse.ArgumentParser(description="Search slim PBP by situation")
    p.add_argument("--seasons", default="2023,2024,2025")
    p.add_argument("--posteam")
    p.add_argument("--defteam")
    p.add_argument("--down", type=int)
    p.add_argument("--ydstogo-min", type=float)
    p.add_argument("--ydstogo-max", type=float)
    p.add_argument("--qtr", type=int)
    p.add_argument("--play-type")
    p.add_argument("--two-high", choices=["true", "false"])
    p.add_argument("--pass-only", action="store_true")
    p.add_argument("--sort", default="epa")
    p.add_argument("--asc", action="store_true")
    p.add_argument("--limit", type=int, default=25)
    args = p.parse_args()
    q = Query(
        seasons=[int(s) for s in args.seasons.split(",") if s.strip()],
        posteam=args.posteam,
        defteam=args.defteam,
        down=args.down,
        ydstogo_min=args.ydstogo_min,
        ydstogo_max=args.ydstogo_max,
        qtr=args.qtr,
        play_type=args.play_type,
        two_high=_bool_arg(args.two_high),
        pass_only=args.pass_only or None,
        sort=args.sort,
        ascending=args.asc,
        limit=args.limit,
    )
    print(json.dumps(search(q), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
