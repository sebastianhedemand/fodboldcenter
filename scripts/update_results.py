"""Safely reconcile provider results with the legacy embedded match list.

Existing/manual scores are never overwritten. A mismatch is reported for review.
Run with API_FOOTBALL_KEY set in the environment.
"""
import json
import os
import re
import sys
from datetime import date, timedelta
from urllib.request import Request, urlopen

API_KEY = os.environ.get("API_FOOTBALL_KEY")
LEAGUES = {
    "Premier League": 39,
    "Championship": 40,
    "League One": 41,
    "Bundesliga": 78,
    "Serie A": 135,
    "La Liga": 140,
    "Superligaen": 119,
    "1. Division": 121,
}
FINISHED_STATUSES = {"FT", "AET", "PEN"}


def fetch(league_id, season, start, end):
    url = (
        "https://v3.football.api-sports.io/fixtures"
        f"?league={league_id}&season={season}&from={start}&to={end}"
    )
    request = Request(url, headers={"x-apisports-key": API_KEY})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("errors"):
        raise RuntimeError(f"API-fejl for liga {league_id}: {payload['errors']}")
    return payload.get("response", [])


def norm(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def main():
    if not API_KEY:
        raise RuntimeError("GitHub Secret API_FOOTBALL_KEY mangler.")

    with open("index.html", encoding="utf-8") as handle:
        html = handle.read()
    match = re.search(r"const initialData=(\{.*?\});\nlet data=load\(\)", html, re.S)
    if not match:
        raise RuntimeError("Kunne ikke finde initialData i index.html.")

    data = json.loads(match.group(1))
    matches = data.get("matches", [])
    today = date.today()
    start = (today - timedelta(days=7)).isoformat()
    end = today.isoformat()
    season = today.year if today.month >= 7 else today.year - 1

    checked = filled = already = conflicts = 0
    for league, league_id in LEAGUES.items():
        finished = {}
        for item in fetch(league_id, season, start, end):
            fixture = item.get("fixture") or {}
            status = (fixture.get("status") or {}).get("short", "")
            goals = item.get("goals") or {}
            home = (item.get("teams") or {}).get("home") or {}
            away = (item.get("teams") or {}).get("away") or {}
            day = (fixture.get("date") or "")[:10]
            if (
                status in FINISHED_STATUSES
                and goals.get("home") is not None
                and goals.get("away") is not None
            ):
                key = (day, norm(home.get("name")), norm(away.get("name")))
                finished[key] = (int(goals["home"]), int(goals["away"]))
        checked += len(finished)

        for game in matches:
            if game.get("league") != league:
                continue
            key = (
                str(game.get("date", ""))[:10],
                norm(game.get("home")),
                norm(game.get("away")),
            )
            score = finished.get(key)
            if score is None:
                continue
            old_home, old_away = game.get("hg"), game.get("ag")
            has_existing_score = old_home not in (None, "") and old_away not in (None, "")
            if has_existing_score:
                if (str(old_home), str(old_away)) == (str(score[0]), str(score[1])):
                    already += 1
                else:
                    conflicts += 1
                    print(
                        "KONFLIKT – eksisterende score bevares: "
                        f"{league} {key[0]} {game.get('home')}–{game.get('away')} "
                        f"lokal={old_home}-{old_away}, provider={score[0]}-{score[1]}"
                    )
                continue

            game["hg"], game["ag"] = score
            game["result_source"] = "api-football"
            game["result_verified_at"] = today.isoformat()
            filled += 1

    if filled:
        updated_html = (
            html[:match.start(1)]
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            + html[match.end(1):]
        )
        with open("index.html", "w", encoding="utf-8") as handle:
            handle.write(updated_html)

    print(
        f"Afsluttede provider-kampe kontrolleret: {checked}; "
        f"tomme resultater udfyldt: {filled}; allerede ens: {already}; "
        f"konflikter til manuel kontrol: {conflicts}."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Automatisk opdatering fejlede: {exc}", file=sys.stderr)
        sys.exit(1)
