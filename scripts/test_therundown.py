
import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta

KEY = os.environ.get("THERUNDOWN_API_KEY")
BASE = "https://therundown.io/api/v2"

LEAGUES = {
    "Premier League": 11,
    "Bundesliga": 13,
    "La Liga": 14,
    "Serie A": 15,
}


def get(path, params=None):
    query = urllib.parse.urlencode(params or {})
    url = BASE + path + ("?" + query if query else "")
    request = urllib.request.Request(
        url,
        headers={
            "X-TheRundown-Key": KEY or "",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    if not KEY:
        raise SystemExit("THERUNDOWN_API_KEY mangler i GitHub Secrets.")

    today = datetime.now(timezone.utc).date()

    for league, sport_id in LEAGUES.items():
        print(f"\n--- {league} (ID {sport_id}) ---")

        for offset in (0, 1):
            date = (today + timedelta(days=offset)).isoformat()

            try:
                result = get(
                    f"/sports/{sport_id}/events/{date}",
                    {
                        "market_ids": "3",
                        "affiliate_ids": "3,19,23",
                        "main_line": "true",
                        "hide_closed": "true",
                    },
                )

                events = result.get("events", []) if isinstance(result, dict) else []

                print(f"Dato {date}: {len(events)} kampe")

                for event in events[:5]:
                    print("Kamp:", event.get("event_id", event.get("id", "?")))
                    print("Hold:", event.get("teams", event.get("participants", "?")))

                    markets = event.get("markets", [])
                    for market in markets[:5]:
                        print(json.dumps(market, ensure_ascii=False)[:1200])

            except urllib.error.HTTPError as exc:
                print(f"HTTP-fejl for {date}: {exc.code}")
                print(exc.read().decode("utf-8", errors="replace")[:400])
            except Exception as exc:
                print(f"Fejl for {date}: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
