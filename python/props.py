"""Player-prop projection layer.

v1 is a shrunk volume model, not a full opponent-adjusted EPA engine.

  pass_yds  = attempts * YPA
  rush_yds  = carries * YPC
  rec_yds   = targets * catch_rate * YPR
  receptions = targets * catch_rate

Week 1-4: blend last season mean with current-season games.
P(over) uses a Normal(proj, sigma) vs the posted line.
Anytime TD is a separate Poisson/opportunity model later.
"""

from __future__ import annotations

from math import erf, sqrt


SIGMA = {
    "pass_yds": 62.0,
    "pass_tds": 0.95,
    "rush_yds": 32.0,
    "rush_att": 4.5,
    "rec_yds": 28.0,
    "receptions": 2.2,
    "pass_rush_yds": 68.0,
}

K_EARLY = 6


def shrink(obs: float, n: int, prior: float, k: int = K_EARLY) -> float:
    w = n / (n + k)
    return w * obs + (1 - w) * prior


def p_over(proj: float, line: float, sigma: float) -> float:
    if sigma <= 0:
        return 0.5
    z = (proj - line) / (sigma * sqrt(2.0))
    return 0.5 * (1.0 + erf(z))


def american_implied(odds: int) -> float:
    if odds < 0:
        return (-odds) / ((-odds) + 100.0)
    return 100.0 / (odds + 100.0)


def ev_over(p: float, odds: int) -> float:
    if odds < 0:
        profit = 100.0 / (-odds)
    else:
        profit = odds / 100.0
    return p * profit - (1 - p)


def project_volume(prior_per_game: float, week1_value: float | None, games: int = 1) -> float:
    if week1_value is None:
        return prior_per_game
    return shrink(week1_value, games, prior_per_game)


def decide(p: float, odds: int | None, edge_units: float, sigma: float, min_edge_sigma: float = 0.35) -> str:
    if abs(edge_units) < min_edge_sigma * max(sigma, 1e-6):
        return "PASS"
    if odds is not None and odds < -125:
        return "PASS"
    if p >= 0.58 or p <= 0.42:
        return "WATCH"
    return "PASS"
