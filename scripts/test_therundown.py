
import os
import json
import urllib.request
import urllib.parse
import urllib.error

KEY = os.environ.get("THERUNDOWN_API_KEY")
BASE = "https://therundown.io/api/v2"


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

    try:
        result = get("/sports")
        print("Forbindelse OK: /sports svarede.")
        print("Svarformat:", type(result).__name__)
    except urllib.error.HTTPError as exc:
        print("API-fejl: HTTP", exc.code)
        print(exc.read().decode("utf-8", errors="replace")[:500])
        raise SystemExit(1)
    except Exception as exc:
        print("Forbindelsesfejl:", type(exc).__name__)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
