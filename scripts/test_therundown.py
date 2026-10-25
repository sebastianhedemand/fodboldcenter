
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

KEY = os.environ.get("THERUNDOWN_API_KEY")
BASE = "https://therundown.io/api/v2"

def get(path, params=None):
    query = urllib.parse.urlencode(params or {})
    url = BASE + path + ("?" + query if query else "")
    req = urllib.request.Request(
        url,
        headers={"X-TheRundown-Key": KEY, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    if not KEY:
        raise SystemExit("THERUNDOWN_API_KEY mangler i GitHub Secrets.")

    # Kontroller at nøglen virker, og find næste kampdato
    sports = get("/sports")
    print("Forbindelse OK: API'et svarede.")

    targets = {
        "Premier League": 11,
        "Bundesliga": 13,
        "La Liga": 14,
        "Serie A": 15,
    }

    dates = get("/sports/dates", {
        "sport_ids": ",".join(map(str, targets.values())),
        "format": "epoch",
        "exclude_canceled": "true",
    })

    now = datetime.now(timezone.utc).timestamp()

    for league, sport_id in targets.items():
        body = dates.get(str(sport_id), {})
        future = [
            stamp for stamp in (body.get("dates") or [])
            if stamp > now
        ]

        if not future:
            print(f"{league}: ingen kommende kampdato fundet i opslaget.")
            continue

        stamp = min(future)
        date = datetime.fromtimestamp(
            stamp, timezone.utc
        ).date().isoformat()

        try:
            data = get(f"/sports/{sport_id}/events/{date}", {
                "market_ids": "1,2,3",
                "main_line": "true",
                "hide_closed": "true",
            })

            events = data.get("events", [])
            print(f"\n{league} — {date}: {len(events)} kampe returneret")

            for event in events[:10]:
                teams = event.get("teams", [])
                names = [t.get("name", "?") for t in teams]
                markets = event.get("markets", [])
                total_found = any(
                    "total" in str(m.get("name", "")).lower()
                    for m in markets
                )
                print(
                    f"  {' – '.join(names)} | "
                    f"totalmarked fundet: {total_found}"
                )
       except Exception as exc:
    if hasattr(exc, "code"):
        print(f"{league}: HTTP {exc.code}")
        if hasattr(exc, "read"):
            print(exc.read().decode("utf-8", errors="replace")[:500])
    else:
        print(f"{league}: {type(exc).__name__}: {exc}")

if __name__ == "__main__":
    main()
