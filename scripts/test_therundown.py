
import os
import json
import time
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
        raise SystemExit(
            "THERUNDOWN_API_KEY mangler i GitHub Secrets."
        )

    today = datetime.now(timezone.utc).date()
    request_count = 0

    for league, sport_id in LEAGUES.items():
        print(f"\n{'=' * 50}")
        print(f"LIGA: {league} (ID {sport_id})")
        print("=" * 50)

        for offset in (0, 1):
            date = (today + timedelta(days=offset)).isoformat()

            # Vent mellem alle API-kald for at overholde grænsen.
            if request_count > 0:
                time.sleep(1.3)

            request_count += 1
            print(f"\nDato: {date}")

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

                events = (
                    result.get("events", [])
                    if isinstance(result, dict)
                    else []
                )

                print(f"Antal kampe: {len(events)}")

                if not events:
                    print(
                        "Ingen kampe returneret for denne dato."
                    )

                for event in events[:10]:
                    teams = event.get(
                        "teams",
                        event.get("participants", [])
                    )

                    if isinstance(teams, list):
                        names = [
                            team.get("name", "?")
                            for team in teams
                            if isinstance(team, dict)
                        ]
                        match_name = " - ".join(names)
                    else:
                        match_name = str(teams)

                    print(f"\nKamp: {match_name}")

                    for market in event.get("markets", []):
                        if market.get("name") != "totals":
                            continue

                        for participant in market.get(
                            "participants", []
                        ):
                            side = participant.get("name", "?")

                            for line in participant.get("lines", []):
                                value = line.get("value", "?")

                                if value not in ("1.5", "2.5", "3.5"):
                                    continue

                                prices = line.get("prices", {})

                                for bookmaker_id, odds in prices.items():
                                    if not odds.get("is_main_line", False):
                                        continue

                                    print(
                                        f"  {side} {value} mål | "
                                        f"Bookmaker-ID {bookmaker_id} | "
                                        f"Odds: {odds.get('price', '?')}"
                                    )

            except urllib.error.HTTPError as exc:
                print(f"API-FEJL: HTTP {exc.code}")
                print(
                    exc.read().decode(
                        "utf-8", errors="replace"
                    )[:500]
                )

            except Exception as exc:
                print(
                    f"FEJL: {type(exc).__name__}: {exc}"
                )

    print("\nTesten er afsluttet.")


if __name__ == "__main__":
    main()
