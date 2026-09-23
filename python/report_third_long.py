#!/usr/bin/env python3
"""Team X on 3rd-and-7+ vs 2-high, default 2024-2025.

2-high = NGS defense_coverage_type in Cover 2/4/6, Quarters, 2-Man, Tampa 2.
If coverage is blank, FTN n_defense_box <= 6 is the proxy (labeled).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pbp_store import load_slim
from search import Query, apply_query

ROOT = Path(__file__).resolve().parents[1]


def _rate(s: pd.Series) -> float | None:
    x = pd.to_numeric(s, errors="coerce")
    return None if x.notna().sum() == 0 else float(x.mean())


def _mean(s: pd.Series) -> float | None:
    x = pd.to_numeric(s, errors="coerce")
    return None if x.notna().sum() == 0 else float(x.mean())


def bucket_air(yards: pd.Series) -> pd.Series:
    y = pd.to_numeric(yards, errors="coerce")
    return pd.cut(
        y,
        bins=[-20, 0, 5, 10, 20, 80],
        labels=["screen/behind", "0-5", "6-10", "11-20", "20+"],
    )


def summarize(plays: pd.DataFrame, label: str) -> dict:
    if plays.empty:
        return {"label": label, "n": 0}
    is_pass = plays["play_type"].eq("pass") if "play_type" in plays.columns else plays.get("pass", 0) == 1
    passing = plays[is_pass] if isinstance(is_pass, pd.Series) else plays
    out = {
        "label": label,
        "n": int(len(plays)),
        "pass_rate": _rate(is_pass.astype(int)) if isinstance(is_pass, pd.Series) else None,
        "epa_per_play": _mean(plays["epa"]) if "epa" in plays.columns else None,
        "success_rate": _rate(plays["success"]) if "success" in plays.columns else None,
        "cpoe": _mean(passing["cpoe"]) if "cpoe" in passing.columns else None,
        "sack_rate": _rate(passing["sack"]) if "sack" in passing.columns else None,
        "int_rate": _rate(passing["interception"]) if "interception" in passing.columns else None,
        "explosive_pass_rate": None,
    }
    if "air_yards" in passing.columns and "yards_gained" in passing.columns:
        yg = pd.to_numeric(passing["yards_gained"], errors="coerce")
        out["explosive_pass_rate"] = float((yg >= 16).mean()) if len(passing) else None
        buckets = (
            passing.assign(air_bucket=bucket_air(passing["air_yards"]))
            .groupby("air_bucket", observed=False)
            .agg(n=("epa", "size"), epa=("epa", "mean"), cpoe=("cpoe", "mean"))
            .reset_index()
        )
        out["by_air_yards"] = [
            {
                "bucket": str(r.air_bucket),
                "n": int(r.n),
                "epa": None if pd.isna(r.epa) else float(r.epa),
                "cpoe": None if pd.isna(r.cpoe) else float(r.cpoe),
            }
            for r in buckets.itertuples(index=False)
        ]
    if "pass_location" in passing.columns:
        loc = (
            passing.groupby(passing["pass_location"].fillna("unknown"))
            .agg(n=("epa", "size"), epa=("epa", "mean"))
            .reset_index()
            .rename(columns={"pass_location": "location"})
        )
        out["by_location"] = [
            {
                "location": str(r.location),
                "n": int(r.n),
                "epa": None if pd.isna(r.epa) else float(r.epa),
            }
            for r in loc.itertuples(index=False)
        ]
    if "passer_player_name" in passing.columns and len(passing):
        qb = (
            passing.groupby(passing["passer_player_name"].fillna("NA"))
            .agg(n=("epa", "size"), epa=("epa", "mean"), cpoe=("cpoe", "mean"))
            .sort_values("n", ascending=False)
            .head(6)
            .reset_index()
        )
        out["by_qb"] = [
            {
                "passer": str(r.passer_player_name),
                "n": int(r.n),
                "epa": None if pd.isna(r.epa) else float(r.epa),
                "cpoe": None if pd.isna(r.cpoe) else float(r.cpoe),
            }
            for r in qb.itertuples(index=False)
        ]
    src = plays["two_high_source"].fillna("") if "two_high_source" in plays.columns else pd.Series("", index=plays.index)
    out["n_labeled_coverage"] = int((src == "coverage").sum())
    out["n_light_box_proxy"] = int((src == "light_box_proxy").sum())
    return out


def report(team: str, seasons: list[int], side: str = "offense") -> dict:
    team = team.upper()
    df = load_slim(seasons)
    base = Query(
        seasons=seasons,
        season_type="REG",
        down=3,
        ydstogo_min=7,
        posteam=team if side == "offense" else None,
        defteam=team if side == "defense" else None,
        limit=10_000,
    )
    third_long = apply_query(df, base)
    vs_two = third_long[third_long["two_high"] == True] if "two_high" in third_long.columns else third_long.iloc[0:0]  # noqa: E712
    vs_else = third_long[third_long["two_high"] != True] if "two_high" in third_long.columns else third_long  # noqa: E712
    body = {
        "title": f"{team} 3rd-and-7+ vs 2-high ({min(seasons)}-{max(seasons)} REG)",
        "team": team,
        "side": side,
        "seasons": seasons,
        "definition": {
            "situation": "down=3 and ydstogo>=7, regular season, pass or run",
            "two_high": "NGS coverage in Cover 2/4/6, Quarters, 2-Man, Tampa 2",
            "proxy": "if coverage blank: FTN n_defense_box <= 6",
            "attribution": "nflverse PBP; FTN Data via nflverse (CC-BY-SA 4.0)",
        },
        "vs_two_high": summarize(vs_two, "3rd-and-7+ vs 2-high / light box"),
        "vs_other": summarize(vs_else, "3rd-and-7+ vs all other looks"),
        "all_third_long": summarize(third_long, "all 3rd-and-7+"),
        "sample_plays": [],
    }
    cols = [c for c in ["season", "week", "posteam", "defteam", "ydstogo", "epa", "passer_player_name", "receiver_player_name", "air_yards", "yards_gained", "defense_coverage_type", "n_defense_box", "two_high_source", "desc"] if c in vs_two.columns]
    if not vs_two.empty:
        top = vs_two.sort_values("epa", ascending=False).head(8)
        recs = top[cols].to_dict(orient="records")
        for r in recs:
            for k, v in list(r.items()):
                if pd.isna(v):
                    r[k] = None
                elif hasattr(v, "item"):
                    r[k] = v.item()
        body["sample_plays"] = recs
    a = body["vs_two_high"].get("epa_per_play")
    b = body["vs_other"].get("epa_per_play")
    if a is not None and b is not None:
        body["epa_delta_vs_other"] = a - b
    return body


def render_text(rep: dict) -> str:
    lines = [
        rep["title"],
        f"side={rep['side']}  n_two_high={rep['vs_two_high'].get('n', 0)}  n_other={rep['vs_other'].get('n', 0)}",
        f"2-high EPA/play={_fmt(rep['vs_two_high'].get('epa_per_play'))}  other={_fmt(rep['vs_other'].get('epa_per_play'))}  delta={_fmt(rep.get('epa_delta_vs_other'))}",
        f"2-high success={_fmt(rep['vs_two_high'].get('success_rate'), pct=True)}  CPOE={_fmt(rep['vs_two_high'].get('cpoe'))}  sack={_fmt(rep['vs_two_high'].get('sack_rate'), pct=True)}",
        f"labeled coverage plays={rep['vs_two_high'].get('n_labeled_coverage')}  light-box proxy={rep['vs_two_high'].get('n_light_box_proxy')}",
        "",
    ]
    for row in rep.get("vs_two_high", {}).get("by_air_yards") or []:
        lines.append(f"  air {row['bucket']}: n={row['n']} EPA={_fmt(row['epa'])} CPOE={_fmt(row['cpoe'])}")
    return "\n".join(lines)


def _fmt(v, pct: bool = False) -> str:
    if v is None:
        return "—"
    return f"{100 * v:.1f}%" if pct else f"{v:.3f}"


def main() -> int:
    p = argparse.ArgumentParser(description="3rd-and-7+ vs 2-high report")
    p.add_argument("--team", required=True)
    p.add_argument("--seasons", default="2024,2025")
    p.add_argument("--side", choices=["offense", "defense"], default="offense")
    p.add_argument("--json", action="store_true")
    p.add_argument("--out")
    args = p.parse_args()
    seasons = [int(s) for s in args.seasons.split(",") if s.strip()]
    rep = report(args.team, seasons, side=args.side)
    text = render_text(rep)
    print(text if not args.json else json.dumps(rep, indent=2))
    dest = Path(args.out) if args.out else ROOT / "data" / "reports" / f"{args.team}_{min(seasons)}_{max(seasons)}_3rd7_two_high.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rep, indent=2))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
