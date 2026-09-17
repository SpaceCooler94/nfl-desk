# NFL Desk

Personal NFL prediction desk for **Scriptable on iOS**.

The phone never runs Python. It pulls a frozen JSON card from this repo.

```
feed/current.json          ← Scriptable reads this
scriptable/NFL-Desk.js     ← paste into Scriptable
python/                    ← rebuild the card on a laptop
```

## Raw feed URL (public)

```
https://raw.githubusercontent.com/SpaceCooler94/nfl-desk/main/feed/current.json
```

GitHub raw caches. The Scriptable file appends `?t=<timestamp>`.

## Scriptable install

1. Open [Scriptable](https://scriptable.app) on iPhone.
2. Tap **+** → paste `scriptable/NFL-Desk.js`.
3. Name it `NFL Desk`.
4. Run it. You should get Week 2 as a table.
5. Optional: long-press home screen → Scriptable widget → small or medium → script `NFL Desk`.

If you later make the repo private, add a classic PAT with `repo` scope into Scriptable Keychain:

```js
Keychain.set("nflDeskGithubToken", "ghp_...");
```

The script already sends `Authorization: Bearer` when that key exists.

## Card contract

See `feed/schema.json`. Minimum fields Scriptable needs per game:

- `away`, `home`, `kickoff`
- `market_spread` (home perspective, e.g. BUF -5.5 → `-5.5`)
- `model_spread` (home expected margin, same sign convention)
- `play` = `HOME` | `AWAY` | `OVER` | `UNDER` | `PASS`
- `edge_spread` = `model_spread - market_spread` (positive = model likes home vs the number)

`status` on the card:

- `SEED_PRIOR` — placeholder priors, do not bet this
- `LIVE` — generated from the Python rating pipeline

## Rebuild the card (laptop)

```bash
pip install nflreadpy pandas numpy
python python/export_feed.py
```

Commit the updated `feed/current.json`. Scriptable picks it up on the next run.

## Week 2 note

The checked-in card is a **seed** so the iOS script works tonight (DET @ BUF). It is prior-weighted, not a matured 2026 model. Treat every `PASS` as the correct default until you replace the file with `export_feed.py` output.
