#!/usr/bin/env python3
"""Rebuild feed/current.json for the live NFL week.

Source: ESPN public scoreboard. Week rolls Tuesday once the prior slate is final.

  python3 build_week.py
  python3 build_week.py --week 3
  python3 build_week.py --fresh
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import date, datetime, timezone
from math import erf, sqrt
from pathlib import Path
from zoneinfo import ZoneInfo

SIGMA = {"pass_yds": 62.0, "rush_yds": 32.0, "rec_yds": 28.0}


def p_over(proj: float, line: float, sigma: float) -> float:
    if sigma <= 0:
        return 0.5
    z = (proj - line) / (sigma * sqrt(2.0))
    return 0.5 * (1.0 + erf(z))


ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "feed" / "current.json"
PRIORS = ROOT / "feed" / "priors.json"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
UA = "nfl-desk/1.0 (+https://github.com/SpaceCooler94/nfl-desk)"
CT = ZoneInfo("America/Chicago")
WEEK1_THU = {2025: date(2025, 9, 4), 2026: date(2026, 9, 10), 2027: date(2027, 9, 9)}
ABBR = {"WAS": "WSH", "JAC": "JAX", "LA": "LAR", "WSH": "WSH", "JAX": "JAX"}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def guess_week(today: date | None = None, season: int = 2026) -> int:
    today = today or datetime.now(CT).date()
    start = WEEK1_THU.get(season, date(season, 9, 10))
    raw = 1 + max(0, (today - start).days) // 7
    return max(1, min(18, raw))


def fetch_board(season: int, week: int) -> dict:
    return _get(f"{ESPN}?seasontype=2&week={week}&dates={season}")


def _abbr(raw: str) -> str:
    raw = (raw or "").upper()
    return ABBR.get(raw, raw)


def _when(iso: str, completed: bool) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(CT)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if completed:
        return f"{days[dt.weekday()]} FINAL"
    hour = dt.strftime("%I:%M%p").lstrip("0").replace("PM", "p").replace("AM", "a")
    return f"{days[dt.weekday()]} {hour}"


def parse_games(board: dict) -> list[dict]:
    season = int((board.get("season") or {}).get("year") or 2026)
    week = int((board.get("week") or {}).get("number") or 0)
    out = []
    for ev in board.get("events") or []:
        comp = (ev.get("competitions") or [{}])[0]
        teams = {c["homeAway"]: c for c in comp.get("competitors") or []}
        home, away = teams.get("home") or {}, teams.get("away") or {}
        hab = _abbr((home.get("team") or {}).get("abbreviation"))
        aab = _abbr((away.get("team") or {}).get("abbreviation"))
        completed = bool((ev.get("status") or {}).get("type", {}).get("completed"))
        odds = (comp.get("odds") or [{}])[0]
        details = odds.get("details") or ""
        total = odds.get("overUnder")
        spread_n = odds.get("spread")
        if details:
            spread = details
        elif spread_n is not None:
            fav = hab if float(spread_n) < 0 else aab
            spread = f"{fav} {spread_n}"
        else:
            spread = "—"
        venue = comp.get("venue") or {}
        broadcasts = comp.get("broadcasts") or []
        tv = ""
        if broadcasts:
            names = broadcasts[0].get("names") or []
            tv = names[0] if names else ""
        hs, aws = home.get("score"), away.get("score")
        game = {
            "id": f"{season}_{week:02d}_{aab}_{hab}",
            "when": _when(ev.get("date") or "", completed),
            "away": aab,
            "home": hab,
            "tv": tv or None,
            "venue": venue.get("fullName") or None,
            "roof": "CLOSED" if venue.get("indoor") else "OPEN",
            "spread": spread,
            "total": float(total) if total not in (None, "") else None,
        }
        if game["total"] is not None and spread_n is not None:
            home_imp = round(game["total"] / 2 - float(spread_n) / 2, 2)
            game["home_implied"] = home_imp
            game["away_implied"] = round(game["total"] - home_imp, 2)
        if completed and hs is not None and aws is not None:
            game["score"] = f"{hab} {hs}-{aws}" if int(hs) >= int(aws) else f"{aab} {aws}-{hs}"
        if comp.get("neutralSite"):
            game["neutral"] = True
        out.append(game)
    return out


def all_final(games: list[dict]) -> bool:
    return bool(games) and all("FINAL" in str(g.get("when") or "") for g in games)


def resolve_week(season: int, week: int | None) -> tuple[int, dict]:
    if week:
        return week, fetch_board(season, week)
    guess = guess_week(season=season)
    board = fetch_board(season, guess)
    games = parse_games(board)
    if all_final(games) and guess < 18:
        nxt = guess + 1
        try:
            return nxt, fetch_board(season, nxt)
        except Exception:
            return guess, board
    return guess, board


def seed_props(games: list[dict], priors: dict) -> list[dict]:
    props = []
    for g in games:
        for side, opp in ((g["home"], g["away"]), (g["away"], g["home"])):
            prior = (priors.get("teams") or {}).get(side) or {}
            for slot, market, label, sigma_key, default_line in (
                ("qb", "pass_yds", "Pass yds", "pass_yds", 224.5),
                ("rb", "rush_yds", "Rush yds", "rush_yds", 64.5),
                ("wr", "rec_yds", "Rec yds", "rec_yds", 64.5),
            ):
                row = prior.get(slot) or {}
                name = row.get("name")
                if not name:
                    continue
                line = float(row.get("line") or default_line)
                proj = float(row.get("proj") or line)
                sigma = float(SIGMA.get(sigma_key, 28))
                props.append(
                    {
                        "id": f"w{g['id']}_{side}_{market}".lower(),
                        "game_id": g["id"],
                        "when": g["when"],
                        "player": name,
                        "team": side,
                        "opp": opp,
                        "pos": "WR" if slot == "wr" else slot.upper(),
                        "market": market,
                        "market_label": label,
                        "line": line,
                        "proj": proj,
                        "sigma": sigma,
                        "p_over": round(p_over(proj, line, sigma), 2),
                        "edge": round(proj - line, 1),
                        "play": "WATCH",
                        "units": 0,
                        "note": row.get("note") or "SEED_PRIOR auto",
                    }
                )
    return props


def merge_props(old: list[dict], fresh: list[dict]) -> list[dict]:
    keep = {p["id"]: p for p in old if p.get("id")}
    out, seen = [], set()
    gids = {x["game_id"] for x in fresh}
    for p in fresh:
        if p["id"] in keep:
            prev = keep[p["id"]]
            prev["when"] = p["when"]
            prev["game_id"] = p["game_id"]
            out.append(prev)
        else:
            out.append(p)
        seen.add(p["id"])
    for p in old:
        if p.get("id") not in seen and p.get("game_id") in gids:
            out.append(p)
    return out


def build(season: int, week: int | None, fresh: bool) -> dict:
    week, board = resolve_week(season, week)
    games = parse_games(board)
    priors = json.loads(PRIORS.read_text()) if PRIORS.exists() else {"teams": {}}
    new_props = seed_props(games, priors)
    old = json.loads(FEED.read_text()) if FEED.exists() else {}
    if not fresh and int(old.get("week") or 0) == week:
        props = merge_props(old.get("props") or [], new_props)
        old_looks = {g["id"]: g.get("looks") for g in old.get("games") or [] if g.get("looks")}
        for g in games:
            if g["id"] in old_looks:
                g["looks"] = old_looks[g["id"]]
    else:
        props = new_props
    return {
        "season": season,
        "week": week,
        "status": "SEED_PRIOR",
        "card_type": "player_props",
        "layout": "xdesk-sheet",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timezone": "America/Chicago",
        "disclaimer": (
            f"Week {week} board from ESPN scoreboard. Props are SEED_PRIOR — "
            "early-season shrink, not tickets. Re-price after inactives."
        ),
        "source": "nfl-desk",
        "feed_version": int(old.get("feed_version") or 8) + (0 if int(old.get("week") or 0) == week else 1),
        "games": games,
        "props": props,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--week", type=int)
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    card = build(args.season, args.week, args.fresh)
    ids = {g["id"] for g in card["games"]}
    missing = [x["id"] for x in card["props"] if x["game_id"] not in ids]
    if missing:
        print("props with unknown game_id", missing, file=sys.stderr)
        return 1
    text = json.dumps(card, indent=2) + "\n"
    if args.dry_run:
        print(f"week={card['week']} games={len(card['games'])} props={len(card['props'])}")
        return 0
    FEED.write_text(text)
    print(f"wrote {FEED} week={card['week']} games={len(card['games'])} props={len(card['props'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
