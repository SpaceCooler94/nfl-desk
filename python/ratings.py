"""
Bayesian EPA power ratings for NFL team-weeks.

This is the core of a personal model a sharp desk would start with:
  1. Aggregate play-level EPA into team-game offensive / defensive ratings.
  2. Opponent-adjust with a simple additive model.
  3. Shrink current-season observations toward last year's ratings
     (heavy shrinkage in Weeks 1-4).
  4. Project expected margin = off_home - def_away - (off_away - def_home) + HFA.

Not a finished betting engine. It is the rating layer you hang features on.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


OFF_YEAR_CORR = 0.47
DEF_YEAR_CORR = 0.31
HFA_POINTS = 2.2
PLAYS_PER_GAME = 65.0


@dataclass
class TeamRatings:
    team: str
    off_epa: float
    def_epa: float
    n_games: int
    prior_off: float
    prior_def: float


def pbp_to_team_games(pbp: pd.DataFrame) -> pd.DataFrame:
    df = pbp.copy()
    if "play_type" in df.columns:
        df = df[df["play_type"].isin(["pass", "run", "qb_kneel", "qb_spike"])]
    if "epa" not in df.columns:
        raise ValueError("pbp must contain an 'epa' column (nflverse / nflfastR)")

    needed = ["game_id", "season", "week", "posteam", "defteam", "epa"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")

    df = df.dropna(subset=["posteam", "defteam", "epa"])
    off = (
        df.groupby(["game_id", "season", "week", "posteam"], as_index=False)
        .agg(off_epa=("epa", "mean"), off_plays=("epa", "size"))
        .rename(columns={"posteam": "team"})
    )
    deff = (
        df.groupby(["game_id", "season", "week", "defteam"], as_index=False)
        .agg(def_epa=("epa", "mean"), def_plays=("epa", "size"))
        .rename(columns={"defteam": "team"})
    )
    return off.merge(deff, on=["game_id", "season", "week", "team"], how="inner")


def season_priors(team_games: pd.DataFrame, prior_season: int) -> pd.DataFrame:
    prev = team_games[team_games["season"] == prior_season]
    if prev.empty:
        return pd.DataFrame(columns=["team", "prior_off", "prior_def"])
    priors = (
        prev.groupby("team", as_index=False)
        .agg(prior_off=("off_epa", "mean"), prior_def=("def_epa", "mean"))
    )
    priors["prior_off"] = OFF_YEAR_CORR * priors["prior_off"] + (1 - OFF_YEAR_CORR) * priors["prior_off"].mean()
    priors["prior_def"] = DEF_YEAR_CORR * priors["prior_def"] + (1 - DEF_YEAR_CORR) * priors["prior_def"].mean()
    return priors


def shrink_team(observed: float, n: int, prior: float, games_to_full: int = 8) -> float:
    w = n / (n + games_to_full)
    return w * observed + (1 - w) * prior


def current_ratings(
    team_games: pd.DataFrame,
    season: int,
    through_week: int,
    priors: pd.DataFrame,
) -> pd.DataFrame:
    cur = team_games[(team_games["season"] == season) & (team_games["week"] <= through_week)]
    agg = (
        cur.groupby("team", as_index=False)
        .agg(obs_off=("off_epa", "mean"), obs_def=("def_epa", "mean"), n_games=("game_id", "nunique"))
    )
    out = agg.merge(priors, on="team", how="outer")
    league_off = team_games["off_epa"].mean()
    league_def = team_games["def_epa"].mean()
    out["prior_off"] = out["prior_off"].fillna(league_off)
    out["prior_def"] = out["prior_def"].fillna(league_def)
    out["obs_off"] = out["obs_off"].fillna(out["prior_off"])
    out["obs_def"] = out["obs_def"].fillna(out["prior_def"])
    out["n_games"] = out["n_games"].fillna(0).astype(int)
    k = 10 if through_week <= 4 else 6 if through_week <= 8 else 4
    out["off_epa"] = [
        shrink_team(o, n, p, games_to_full=k)
        for o, n, p in zip(out["obs_off"], out["n_games"], out["prior_off"])
    ]
    out["def_epa"] = [
        shrink_team(d, n, p, games_to_full=k)
        for d, n, p in zip(out["obs_def"], out["n_games"], out["prior_def"])
    ]
    return out[["team", "off_epa", "def_epa", "n_games", "prior_off", "prior_def", "obs_off", "obs_def"]]


def expected_margin(ratings: pd.DataFrame, home: str, away: str, hfa: float = HFA_POINTS) -> float:
    r = ratings.set_index("team")
    home_net = (r.loc[home, "off_epa"] - r.loc[away, "def_epa"]) * PLAYS_PER_GAME * 0.5
    away_net = (r.loc[away, "off_epa"] - r.loc[home, "def_epa"]) * PLAYS_PER_GAME * 0.5
    return float((home_net - away_net) + hfa)


def margin_to_win_prob(margin: float, sigma: float = 13.5) -> float:
    from math import erf, sqrt

    z = margin / (sigma * sqrt(2.0))
    return 0.5 * (1.0 + erf(z))


def american_to_implied(odds: int) -> float:
    if odds < 0:
        return (-odds) / ((-odds) + 100.0)
    return 100.0 / (odds + 100.0)


def edge_vs_market(model_p: float, market_american: int) -> float:
    return model_p - american_to_implied(market_american)
