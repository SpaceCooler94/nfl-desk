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
feed/current.json        Scriptable + web read this (props sheet)
feed/scouting.json       daily 3rd-and-7+ vs 2-high lines
scriptable/NFL-Desk.js   paste into Scriptable
web/index.html           same sheet in a browser
.github/workflows/daily-pbp.yml  Mon + Tue/Wed lake refresh
python/publish_scouting.py       writes feed/scouting.json
python/pbp_store.py      nflverse PBP → slim parquet
```

## Phone

1. Copy [scriptable/NFL-Desk.js](https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/scriptable/NFL-Desk.js)
2. Scriptable → New Script → paste → name `NFL Desk`
3. Run. Pick a game. You get the sheet.

Feeds baked into the JS:

https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/feed/current.json  
https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/feed/scouting.json

Re-paste `scriptable/NFL-Desk.js` after a layout commit. The widget still shows the prop card. The full sheet adds a **3RD AND 7+ VS 2-HIGH** row from the daily job.

Browser:

https://htmlpreview.github.io/?https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/web/index.html

## Layout contract

| Surface | Renders |
|---|---|
| `scriptable/NFL-Desk.js` | WebView game sheet |
| `web/index.html` | Same sheet |
| `feed/current.json` | `games[]` + `props[]` + optional `looks[]` |
| `feed/scouting.json` | daily PBP lines by team |

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

## Daily run

[`.github/workflows/daily-pbp.yml`](.github/workflows/daily-pbp.yml) — Monday 14:30 UTC and Tue/Wed 11:30 UTC, plus **Run workflow** in Actions.

It refreshes 2024–2026 PBP on the runner and commits `feed/scouting.json`. Parquet is not committed.

## PBP desk (search + scouting)

Does not change the sheet contract. This is the research layer under the card.

Data: [nflverse-data](https://github.com/nflverse/nflverse-data) play-by-play releases plus FTN via nflverse (CC-BY-SA 4.0 — attribute **FTN Data via nflverse**).

```bash
python3 -m pip install -r requirements.txt
cd python
python3 pbp_store.py --seasons 2023,2024,2025,2026
python3 search.py --posteam KC --down 3 --ydstogo-min 7 --two-high true --pass-only --limit 15
python3 report_third_long.py --team KC --seasons 2024,2025,2026 --side offense
python3 publish_scouting.py --seasons 2024,2025,2026
```

Sister desk: [mlb-desk](https://github.com/SpaceCooler94/mlb-desk)
