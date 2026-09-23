#!/usr/bin/env python3
"""Load nflverse play-by-play into a slim local parquet lake.

Source of truth is nflverse-data GitHub releases (same files nflreadpy/nflreadr
serve). Default seasons: 2023-2025. 2026 can be appended in-season.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.parquet"
FTN_URL = "https://github.com/nflverse/nflverse-data/releases/download/ftn_charting/ftn_charting_{season}.parquet"

DEFAULT_SEASONS = (2023, 2024, 2025)

KEEP = [
    "game_id",
    "play_id",
    "old_game_id",
    "season",
    "season_type",
    "week",
    "game_date",
    "posteam",
    "defteam",
    "home_team",
    "away_team",
    "down",
    "ydstogo",
    "yardline_100",
    "qtr",
    "quarter_seconds_remaining",
    "game_seconds_remaining",
    "score_differential",
    "wp",
    "play_type",
    "pass",
    "rush",
    "qb_dropback",
    "shotgun",
    "no_huddle",
    "qb_scramble",
    "pass_length",
    "pass_location",
    "air_yards",
    "yards_after_catch",
    "yards_gained",
    "epa",
    "wpa",
    "success",
    "cpoe",
    "complete_pass",
    "incomplete_pass",
    "interception",
    "sack",
    "touchdown",
    "first_down",
    "passer_player_name",
    "receiver_player_name",
    "rusher_player_name",
    "offense_personnel",
    "defense_personnel",
    "offense_formation",
    "number_of_pass_rushers",
    "defense_man_zone_type",
    "defense_coverage_type",
    "xpass",
    "pass_oe",
    "desc",
]

FTN_KEEP = [
    "nflverse_game_id",
    "nflverse_play_id",
    "n_defense_box",
    "n_offense_backfield",
    "qb_location",
    "is_motion",
    "is_play_action",
    "is_screen_pass",
    "is_rpo",
    "is_no_huddle",
    "is_qb_out_of_pocket",
    "read_thrown",
]

TWO_HIGH_TOKENS = (
    "COVER_2",
    "COVER 2",
    "COVER2",
    "COVER_4",
    "COVER 4",
    "COVER4",
    "QUARTERS",
    "COVER_6",
    "COVER 6",
    "COVER6",
    "2-MAN",
    "2 MAN",
    "TWO MAN",
    "TAMPA 2",
    "TAMPA2",
)


def slim_path(seasons: list[int] | tuple[int, ...]) -> Path:
    tag = f"{min(seasons)}_{max(seasons)}"
    return DATA / f"pbp_slim_{tag}.parquet"


def _get(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"download {url}")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)
    return dest


def coverage_two_high(series: pd.Series) -> pd.Series:
    s = series.fillna("").astype(str).str.upper()
    out = pd.Series(False, index=series.index)
    for tok in TWO_HIGH_TOKENS:
        out = out | s.str.contains(tok, regex=False)
    out = out & s.ne("")
    return out


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    cov_col = "defense_coverage_type" if "defense_coverage_type" in df.columns else None
    df["two_high_coverage"] = coverage_two_high(df[cov_col]) if cov_col else False
    if "n_defense_box" in df.columns:
        df["light_box"] = pd.to_numeric(df["n_defense_box"], errors="coerce") <= 6
    else:
        df["light_box"] = False
    if cov_col:
        missing_cov = df[cov_col].isna() | df[cov_col].astype(str).str.strip().isin(["", "nan", "None"])
        df["two_high"] = df["two_high_coverage"] | (missing_cov & df["light_box"])
        df["two_high_source"] = ""
        df.loc[df["two_high_coverage"], "two_high_source"] = "coverage"
        df.loc[missing_cov & df["light_box"] & ~df["two_high_coverage"], "two_high_source"] = "light_box_proxy"
    else:
        df["two_high"] = df["light_box"]
        df["two_high_source"] = ""
        df.loc[df["light_box"], "two_high_source"] = "light_box_proxy"
    return df


def load_season(season: int, force: bool = False) -> pd.DataFrame:
    DATA.mkdir(parents=True, exist_ok=True)
    raw = DATA / f"play_by_play_{season}.parquet"
    if force and raw.exists():
        raw.unlink()
    _get(PBP_URL.format(season=season), raw)
    df = pd.read_parquet(raw)
    cols = [c for c in KEEP if c in df.columns]
    df = df[cols].copy()
    ftn_raw = DATA / f"ftn_charting_{season}.parquet"
    try:
        if force and ftn_raw.exists():
            ftn_raw.unlink()
        _get(FTN_URL.format(season=season), ftn_raw)
        ftn = pd.read_parquet(ftn_raw)
        fcols = [c for c in FTN_KEEP if c in ftn.columns]
        ftn = ftn[fcols].rename(
            columns={"nflverse_game_id": "game_id", "nflverse_play_id": "play_id"}
        )
        df = df.merge(ftn, on=["game_id", "play_id"], how="left")
    except Exception as exc:  # noqa: BLE001
        print(f"ftn {season} skipped: {exc}", file=sys.stderr)
    return enrich(df)


def refresh(seasons: list[int], force: bool = False) -> Path:
    frames = [load_season(s, force=force) for s in seasons]
    out = pd.concat(frames, ignore_index=True)
    if "play_type" in out.columns:
        out = out[out["play_type"].isin(["pass", "run"])]
    dest = slim_path(seasons)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest, index=False)
    meta = {
        "seasons": seasons,
        "rows": int(len(out)),
        "path": str(dest),
        "attribution": "nflverse play-by-play; FTN Data via nflverse (CC-BY-SA 4.0)",
        "two_high": "defense_coverage_type in {Cover 2/4/6, Quarters, 2-Man, Tampa 2}; else n_defense_box<=6 proxy",
    }
    (DATA / "pbp_slim_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"wrote {dest} rows={len(out)}")
    return dest


def load_slim(seasons: list[int] | None = None) -> pd.DataFrame:
    seasons = list(seasons or DEFAULT_SEASONS)
    dest = slim_path(seasons)
    if not dest.exists():
        matches = sorted(DATA.glob("pbp_slim_*.parquet"))
        if matches:
            dest = matches[-1]
        else:
            refresh(seasons)
            dest = slim_path(seasons)
    return pd.read_parquet(dest)


def main() -> int:
    p = argparse.ArgumentParser(description="Build slim nflverse PBP parquet")
    p.add_argument("--seasons", default="2023,2024,2025")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    seasons = [int(s) for s in args.seasons.split(",") if s.strip()]
    refresh(seasons, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
