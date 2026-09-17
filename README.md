# NFL Desk — player props

Scriptable iOS client + JSON feed. **Props only.** Sides/totals are out of the card.

```
feed/current.json          ← Scriptable reads this
scriptable/NFL-Desk.js     ← paste into Scriptable
python/props.py            ← projection helpers
```

## Feed

https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/feed/current.json

## Install

1. Scriptable → + → paste `scriptable/NFL-Desk.js` → name it `NFL Desk`.
2. Run. You get tonight's DET @ BUF prop board.
3. Optional medium widget on the same script (top WATCH row).

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

## How the prop model is supposed to work

Do not project yards from Week 1 box scores raw.

1. Last-season per-game mean as prior (8-game trailing, not full season if role changed).
2. Shrink current-season games toward that prior. Week 2 prior weight is heavy (`k ≈ 6`).
3. Volume first, efficiency second. Receptions and carries stabilize before yards.
4. Opponent adjust with defense vs position (pass EPA allowed to WR/TE/RB, rush EPA allowed).
5. Convert mean to P(over) with a position-market sigma. Passing yards sigma is ~60, not 15.
6. Bet the over only if `p_over` beats vig-removed implied and `|proj-line|` is a real fraction of sigma.
7. Refuse −125 or worse unless the edge is large. Gibbs 18.5 carries at −128 is a pass even if volume is real.

Anytime TD is a different model (opportunity × red-zone share × vulture risk). Do not treat it like a yard total.

## TNF note

The checked-in card is a **seed** so the phone works before kickoff. Lines were pulled from public Week 2 writeups (DK / MGM / FanDuel / Underdog / Betr). They will move. Re-price before you even think about a unit.
