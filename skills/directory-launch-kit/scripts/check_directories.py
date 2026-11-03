#!/usr/bin/env python3
"""Re-check the directory list before you rely on it: is each submit page still up, and do the prices
recorded in references/directories.json still appear on the page? No dependencies (Python 3.9+).

  python3 scripts/check_directories.py                 # all directories
  python3 scripts/check_directories.py --only fazier,dang-ai --json

Results per directory:
  OK       page loads and every recorded $ amount is still on it (or none was recorded)
  CHANGED  page loads but a recorded $ amount is gone: read the page and update directories.json
  BLOCKED  403/429/challenge page: the site blocks scripts, open it in a browser by hand
  DOWN     404, 5xx or network error: the URL moved or the directory closed
Many sites render prices with JavaScript; CHANGED can mean "not in the server HTML". Always read the
page yourself before telling the user a price, and give the date you read it.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0 Safari/537.36"
PRICE_RE = re.compile(r"\$\d+(?:\.\d+)?")


def fetch(url: str, timeout: int = 20) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*", "Accept-Language": "en-US,en"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(3_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(200_000).decode("utf-8", "replace") if e.fp else ""
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def classify(d: dict, status: int, body: str) -> tuple[str, str]:
    if status in (401, 403, 429) or re.search(r"cf-chl-|<title>Just a moment|<title>Attention Required", body[:20000], re.I):
        return "BLOCKED", f"HTTP {status}: open {d['submit_url']} in a browser"
    if status == 0 or status >= 400:
        return "DOWN", f"HTTP {status or 'error'}: {body[:120] if status == 0 else ''}".strip()
    recorded = PRICE_RE.findall(d.get("cost", ""))
    page = set(PRICE_RE.findall(body))
    missing = [p for p in recorded if p not in page]
    if missing:
        return "CHANGED", f"recorded {', '.join(missing)} not found in the page HTML (JS-rendered or changed)"
    return "OK", f"HTTP {status}" + (f", prices {', '.join(recorded)} still present" if recorded else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(HERE, "..", "references", "directories.json"))
    ap.add_argument("--only")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    with open(a.data, encoding="utf-8") as f:
        data = json.load(f)
    only = set(a.only.split(",")) if a.only else None
    results = []
    for d in data["directories"]:
        if only and d["id"] not in only:
            continue
        url = d.get("pricing_url") or d["submit_url"]
        status, body = fetch(url)
        level, detail = classify(d, status, body)
        results.append({"id": d["id"], "name": d["name"], "url": url, "level": level, "detail": detail})
        if not a.json:
            print(f"{level:<8} {d['name']}: {detail}", flush=True)
    if a.json:
        print(json.dumps({"checked_against": data["checked"], "results": results}, indent=2))
    else:
        counts = {k: sum(r["level"] == k for r in results) for k in ("OK", "CHANGED", "BLOCKED", "DOWN")}
        print(f"\n{len(results)} directories: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
        print(f"Data recorded on {data['checked']}. Update references/directories.json for CHANGED/DOWN rows.")
    return 1 if any(r["level"] == "DOWN" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
