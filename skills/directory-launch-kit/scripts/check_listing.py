#!/usr/bin/env python3
"""Check which submissions went live: for every tracker.csv row with a listing_url, fetch the listing,
confirm it links to your product and record whether the link is followed or nofollow/ugc/sponsored.
No dependencies (Python 3.9+).

  python3 scripts/check_listing.py --tracker launch-kit/tracker.csv --domain acme-invoices.example.com
  python3 scripts/check_listing.py --tracker launch-kit/tracker.csv --domain acme.com --write   # update status/link_rel

status becomes 'live' when the page links to your domain, 'no-link' when it loads but has no link to you,
'error' when it does not load. Rows without listing_url are left alone.
"""
from __future__ import annotations

import argparse
import csv
import html.parser
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0 Safari/537.36"


class Links(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            a = dict(attrs)
            if a.get("href"):
                self.links.append((a["href"], (a.get("rel") or "").lower()))


def host_matches(href: str, base: str, domain: str) -> bool:
    h = (urllib.parse.urlparse(urllib.parse.urljoin(base, href)).hostname or "").lower()
    d = domain.lower().removeprefix("www.")
    return h == d or h.endswith("." + d)


def check(url: str, domain: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(5_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return "error", f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return "error", str(e)[:80]
    p = Links()
    p.feed(body)
    mine = [(h, rel) for h, rel in p.links if host_matches(h, url, domain)]
    if not mine:
        return "no-link", ""
    rels = {("nofollow" if any(x in rel for x in ("nofollow", "ugc", "sponsored")) else "follow") for _, rel in mine}
    return "live", "follow" if "follow" in rels else "nofollow"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--domain", required=True, help="your product's domain, e.g. acme.com")
    ap.add_argument("--write", action="store_true", help="write status and link_rel back into the CSV")
    a = ap.parse_args()
    with open(a.tracker, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys()) if rows else []
    live = 0
    for r in rows:
        if not r.get("listing_url"):
            continue
        status, rel = check(r["listing_url"], a.domain)
        print(f"{status:<8} {rel:<9} {r['directory']}: {r['listing_url']}")
        live += status == "live"
        if a.write:
            r["status"], r["link_rel"] = status, rel
    if a.write and rows:
        with open(a.tracker, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    print(f"\n{live} live listing(s) linking to {a.domain}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
