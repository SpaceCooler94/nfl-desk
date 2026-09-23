from datetime import date

from build_week import guess_week, parse_games, _abbr


def test_guess_week_2026():
    assert guess_week(date(2026, 9, 10), 2026) == 1
    assert guess_week(date(2026, 9, 16), 2026) == 1
    assert guess_week(date(2026, 9, 17), 2026) == 2
    assert guess_week(date(2026, 9, 22), 2026) == 2
    assert guess_week(date(2026, 9, 24), 2026) == 3


def test_abbr():
    assert _abbr("WAS") == "WSH"
    assert _abbr("JAC") == "JAX"
    assert _abbr("GB") == "GB"


def test_parse_games_fixture():
    board = {
        "season": {"year": 2026},
        "week": {"number": 3},
        "events": [
            {
                "date": "2026-09-25T00:15Z",
                "status": {"type": {"completed": False, "name": "STATUS_SCHEDULED"}},
                "competitions": [
                    {
                        "neutralSite": False,
                        "venue": {"fullName": "Lambeau Field", "indoor": False},
                        "broadcasts": [{"names": ["Prime Video"]}],
                        "odds": [{"details": "GB -5.5", "overUnder": 43.5, "spread": -5.5}],
                        "competitors": [
                            {"homeAway": "home", "team": {"abbreviation": "GB"}, "score": None},
                            {"homeAway": "away", "team": {"abbreviation": "ATL"}, "score": None},
                        ],
                    }
                ],
            }
        ],
    }
    games = parse_games(board)
    assert games[0]["id"] == "2026_03_ATL_GB"
    assert games[0]["spread"] == "GB -5.5"
    assert games[0]["total"] == 43.5
    assert games[0]["roof"] == "OPEN"
    assert games[0]["tv"] == "Prime Video"
    assert games[0]["home_implied"] == 24.5
    assert games[0]["away_implied"] == 19.0
