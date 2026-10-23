
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.footballsoccerapi.com/v1"
KEY = os.environ.get("FSAPI_KEY")

TARGETS = {
    "England": ["Premier League", "Championship", "League One"],
    "Germany": ["Bundesliga"],
    "Italy": ["Serie A"],
    "Spain": ["La Liga"],
    "Denmark": ["Superligaen", "1. Division"],
}

def get(path, params=None):
    query = urllib.parse.urlencode(params or {})
    url = BASE + path + ("?" + query if query else "")
    request = urllib.request.Request(
        url,
        headers={"X-API-Key": KEY, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def rows(payload):
    data = payload.get("data", [])
    if isinstance(data, dict):
        return [data]
    return data if isinstance(data, list) else []

def main():
    if not KEY:
        raise SystemExit("FSAPI_KEY mangler. Kontrollér GitHub Secrets.")

    found = []
    for country, wanted in TARGETS.items():
        payload = get("/leagues", {"country": country, "limit": 1000})
        leagues = rows(payload)

        for name in wanted:
            matches = [
                league for league in leagues
                if league.get("league_name", "").casefold() == name.casefold()
            ]
            if not matches:
                print(f"Mangler i kataloget: {country} — {name}")
                continue

            for league in matches:
                found.append((country, name, league))
                print(
                    f"Fundet: {country} — {name} | "
                    f"ID={league.get('league_id')} | "
                    f"Sæsoner={league.get('season_first')}–"
                    f"{league.get('season_last')}"
                )

    print("\n--- Sæsondækning ---")
    for country, name, league in found:
        league_id = league.get("league_id")
        latest = league.get("season_last")
        if not league_id or latest is None:
            print(f"Kan ikke kontrollere sæson: {country} — {name}")
            continue

        # Tjek seneste sæson samt forrige sæson, hvis tilgængelig.
        seasons = [int(latest)]
        if league.get("season_first") is not None:
            if int(latest) > int(league["season_first"]):
                seasons.append(int(latest) - 1)

        for season in seasons:
            try:
                payload = get("/coverage", {
                    "league_id": league_id,
                    "season": season,
                    "limit": 1000,
                })
                data = rows(payload)
                if not data:
                    print(
                        f"{country} — {name} — {season}: "
                        "Ingen kampdata returneret"
                    )
                    continue

                for row in data:
                    print(
                        f"{country} — {name} — "
                        f"{row.get('season_start_year', season)} | "
                        f"kampe={row.get('matches', row.get('match_count', '?'))} | "
                        f"afsluttede={row.get('settled_matches', '?')} | "
                        f"status={row.get('match_status', '?')}"
                    )
            except urllib.error.HTTPError as exc:
                # Udskriv ikke headers eller anmodningen, så nøglen forbliver privat.
                print(
                    f"{country} — {name} — {season}: "
                    f"API svarede HTTP {exc.code}"
                )
            except Exception as exc:
                print(
                    f"{country} — {name} — {season}: "
                    f"Fejl ({type(exc).__name__})"
                )

if __name__ == "__main__":
    main()
