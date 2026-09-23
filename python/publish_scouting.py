#!/usr/bin/env python3
"""Write feed/scouting.json for Scriptable / the web sheet.

Reads this week's teams from feed/current.json, runs 3rd-and-7+ vs 2-high
for each side, keeps a small card. Parquet stays local / on the runner.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_third_long import report

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "feed" / "current.json"
OUT = ROOT / "feed" / "scouting.json"


def _line(rep: dict) -> str:
    v = rep.get("vs_two_high") or {}
    if not v.get("n"):
        return f"{rep['team']} 3rd-7+ vs 2H · n=0"
    epa = v.get("epa_per_play")
    delta = rep.get("epa_delta_vs_other")
    suc = v.get("success_rate")
    bits = [f"{rep['team']} 3rd-7+ vs 2H n={v['n']}"]
    if epa is not None:
        bits.append(f"EPA {epa:+.2f}")
    if delta is not None:
        bits.append(f"Δ {delta:+.2f}")
    if suc is not None:
        bits.append(f"succ {100 * suc:.0f}%")
    return " · ".join(bits)


def _pack(rep: dict) -> dict:
    v = rep.get("vs_two_high") or {}
    return {
        "team": rep["team"],
        "side": rep["side"],
        "n": v.get("n", 0),
        "epa": v.get("epa_per_play"),
        "delta": rep.get("epa_delta_vs_other"),
        "success": v.get("success_rate"),
        "cpoe": v.get("cpoe"),
        "n_coverage": v.get("n_labeled_coverage", 0),
        "n_proxy": v.get("n_light_box_proxy", 0),
        "line": _line(rep),
    }


def teams_from_feed() -> list[str]:
    if not FEED.exists():
        return []
    card = json.loads(FEED.read_text())
    out: list[str] = []
    for g in card.get("games") or []:
        for k in ("away", "home"):
            t = g.get(k)
            if t and t not in out:
                out.append(t)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seasons", default="2024,2025,2026")
    args = p.parse_args()
    seasons = [int(s) for s in args.seasons.split(",") if s.strip()]
    teams = teams_from_feed()
    rows = []
    for team in teams:
        try:
            rows.append(_pack(report(team, seasons, side="offense")))
        except Exception as exc:  # noqa: BLE001
            rows.append({"team": team, "side": "offense", "n": 0, "line": f"{team} failed: {exc}"})
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seasons": seasons,
        "attribution": "nflverse PBP; FTN Data via nflverse",
        "teams": {r["team"]: r for r in rows},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT} teams={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
