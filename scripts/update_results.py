import json, os, re, sys
from datetime import date, timedelta
from urllib.request import Request, urlopen

API_KEY = os.environ.get("API_FOOTBALL_KEY")
LEAGUES = {
    "Premier League": 39, "Championship": 40, "League One": 41,
    "Bundesliga": 78, "Serie A": 135, "La Liga": 140,
    "Superligaen": 119, "1. Division": 121,
}

def fetch(league_id, season, start, end):
    url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}&from={start}&to={end}"
    req = Request(url, headers={"x-apisports-key": API_KEY})
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("errors"):
        raise RuntimeError(f"API-fejl for liga {league_id}: {result['errors']}")
    return result.get("response", [])

def norm(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())

def main():
    if not API_KEY:
        raise RuntimeError("GitHub Secret API_FOOTBALL_KEY mangler.")
    with open("index.html", encoding="utf-8") as f:
        html = f.read()
    match = re.search(r"const initialData=(\{.*?\});\nlet data=load\(\)", html, re.S)
    if not match:
        raise RuntimeError("Kunne ikke finde initialData i index.html.")
    data = json.loads(match.group(1))
    matches = data.get("matches", [])
    today = date.today()
    start, end = (today - timedelta(days=7)).isoformat(), today.isoformat()
    season = today.year if today.month >= 7 else today.year - 1
    updated = checked = 0
    for league, league_id in LEAGUES.items():
        finished = {}
        fixtures = fetch(league_id, season, start, end)
        checked += len(fixtures)
        for item in fixtures:
            status = item.get("fixture", {}).get("status", {}).get("short", "")
            goals = item.get("goals") or {}
            home = item.get("teams", {}).get("home", {}).get("name", "")
            away = item.get("teams", {}).get("away", {}).get("name", "")
            day = (item.get("fixture", {}).get("date") or "")[:10]
            if status in {"FT", "AET", "PEN"} and goals.get("home") is not None and goals.get("away") is not None:
                finished[(day, norm(home), norm(away))] = (goals["home"], goals["away"])
        for game in matches:
            if game.get("league") != league:
                continue
            key = (str(game.get("date", ""))[:10], norm(game.get("home")), norm(game.get("away")))
            score = finished.get(key)
            if score is not None and (game.get("hg") != score[0] or game.get("ag") != score[1]):
                game["hg"], game["ag"] = score
                updated += 1
    if updated:
        html = html[:match.start(1)] + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + html[match.end(1):]
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
    print(f"API-kampe kontrolleret: {checked}; resultater opdateret: {updated}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Automatisk opdatering fejlede: {exc}", file=sys.stderr)
        sys.exit(1)
