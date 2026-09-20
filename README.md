# NFL Desk — player props

Scriptable iOS client + JSON feed. **Props only.**

The repo **always** ships the xDESK game-sheet layout. That is the product.

```
WEEK 2          NFL · GAME SHEET                              xDESK
JAGUARS AT BRONCOS
[teal AWAY | AT | orange HOME]
SPREAD · TOTAL · KICKOFF · ROOF
PROPS AT A GLANCE     PLAYER · PROJ · LINE · GAP · GRADE
KEY MATCHUPS          0–100 badges
```

Do not replace this with a native UITable, a neon prop board, or a list-only view. If the sheet and the feed disagree, fix the feed.

```
feed/current.json          ← Scriptable + web read this
scriptable/NFL-Desk.js     ← paste into Scriptable (WebView sheet)
web/index.html             ← same sheet in the browser
python/props.py            ← projection helpers
```

## Feed

https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/feed/current.json

Sheet preview:

https://htmlpreview.github.io/?https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/web/index.html

## Install

1. Scriptable → + → paste `scriptable/NFL-Desk.js` → name it `NFL Desk`.
2. Run. Pick a game. You get the game sheet.
3. Optional medium widget on the same script.

Re-paste the script after a layout commit. The feed updates on its own (`?t=Date.now()`).

## Layout contract (do not drift)

| Surface | Must render |
|---|---|
| `scriptable/NFL-Desk.js` | WebView game sheet (banner, 4 pills, props table, key matchups) |
| `web/index.html` | Same sheet, fed by `feed/current.json` |
| `feed/current.json` | `games[]` + `props[]`. Optional `looks[]` on a game. |

Pills are always **SPREAD / TOTAL / KICKOFF / ROOF**.
Table columns are always **PLAYER / PROJ / LINE / GAP / GRADE**.
Gap is green if `proj >= line`, red otherwise. Grade is pink.

## Card fields that matter

| field | meaning |
|---|---|
| `market` | `pass_yds` `rush_yds` `rec_yds` `receptions` `rush_att` `pass_rush_yds` `anytime_td` |
| `line` | posted number |
| `proj` | model mean |
| `edge` | `proj - line` (positive likes the over) |
| `p_over` | Normal(proj, sigma) vs the line |
| `price` | American on the over / yes |
| `play` | `OVER` `UNDER` `WATCH` `PASS` |

`WATCH` = the number is interesting. It is not a ticket until `status` is `LIVE` and juice is tolerable.

## Daily loop

Morning: injuries + inactives
Noon: push `feed/current.json` (sheet stays the same file)
Kickoff: lock
Night: grade vs close

The checked-in card is a **seed** so the phone works before kickoff. Lines move. Re-price before a unit.
