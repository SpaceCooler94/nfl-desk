# NFL Desk

Personal player-prop desk. GitHub JSON in, xDESK game sheet out.

The repo **always** ships this card. That is the product.

```
WEEK 2                 NFL · GAME SHEET                 xDESK
JAGUARS AT BRONCOS
[teal AWAY | AT | orange HOME]
SPREAD · TOTAL · KICKOFF · ROOF
PROPS AT A GLANCE     PLAYER · PROJ · LINE · GAP · GRADE
KEY MATCHUPS          0–100 badges
```

```
feed/current.json        Scriptable + web read this
scriptable/NFL-Desk.js   paste into Scriptable
web/index.html           same sheet in a browser
python/props.py          projection helpers
python/export_feed.py    validate the card
python/pbp_store.py      nflverse PBP → slim parquet
python/search.py         situation search (EPA sort)
python/report_third_long.py  3rd-and-7+ vs 2-high
python/api.py            local search + report API
```

## Phone

1. Copy [scriptable/NFL-Desk.js](https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/scriptable/NFL-Desk.js)
2. Scriptable → New Script → paste → name `NFL Desk`
3. Run. Pick a game. You get the sheet.

Feed (already baked into the JS):

https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/feed/current.json

Browser:

https://htmlpreview.github.io/?https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/web/index.html

Re-paste the script after a layout commit. The feed refreshes on its own (`?t=Date.now()`).

## Layout contract

| Surface | Renders |
|---|---|
| `scriptable/NFL-Desk.js` | WebView game sheet |
| `web/index.html` | Same sheet |
| `feed/current.json` | `games[]` + `props[]` + optional `looks[]` |

Do not ship a native table or a neon board as the primary view.

## Card

| field | meaning |
|---|---|
| `proj` | model mean |
| `line` | posted number |
| `edge` | `proj - line` (positive likes the over) |
| `p_over` | Normal(proj, sigma) vs the line |
| `play` | `OVER` `UNDER` `WATCH` `PASS` |

`WATCH` is interesting. It is not a ticket until `status` is `LIVE`.

This Week 2 card is `SEED_PRIOR`. One 2026 game is not a model.

## PBP desk (search + scouting)

Does not change the sheet contract. This is the research layer under the card.

Data: [nflverse-data](https://github.com/nflverse/nflverse-data) play-by-play releases (same files `nflreadpy` / `nflreadr` serve) plus [FTN charting](https://nflreadr.nflverse.com/reference/load_ftn_charting.html) via nflverse (CC-BY-SA 4.0 — attribute **FTN Data via nflverse**).

Public FTN does **not** include coverage family. 2-high is:

1. NGS `defense_coverage_type` in Cover 2 / Cover 4 / Cover 6 / Quarters / 2-Man / Tampa 2 when the column is populated
2. Otherwise FTN `n_defense_box <= 6` as a **labeled proxy**

```bash
python3 -m pip install -r requirements.txt
cd python

# 1. slim lake (2023-2026). 2026 refreshes when older than 12h.
python3 pbp_store.py --seasons 2023,2024,2025,2026

# 2. situation search, EPA desc
python3 search.py --posteam KC --down 3 --ydstogo-min 7 --two-high true --pass-only --limit 15

# 3. scouting report
python3 report_third_long.py --team KC --seasons 2024,2025,2026 --side offense

# API
uvicorn api:app --port 8787
# GET /search?posteam=KC&down=3&ydstogo_min=7&two_high=true&sort=epa
# GET /reports/third-long-two-high?team=KC&seasons=2024,2025,2026&side=offense
```

Parquet stays in `data/` and is gitignored. Unit tests: `cd python && python3 -m pytest test_search.py -q`

Sister desk: [mlb-desk](https://github.com/SpaceCooler94/mlb-desk)
