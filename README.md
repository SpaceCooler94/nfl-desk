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

Sister desk: [mlb-desk](https://github.com/SpaceCooler94/mlb-desk)
