#!/usr/bin/env python3
"""Pre-launch website audit. Standard library only.

Usage:
  python3 audit_site.py BASE_URL [--max-pages 20] [--json] [--timeout 15] [--sells]

--sells   the site sells something: refund policy link becomes a FAIL instead of WARN.
Exit code 0 = no FAIL, 1 = at least one FAIL, 2 = start URL unreachable.
"""
import argparse
import json
import re
import sys
import time
import uuid
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urljoin, urldefrag, urlparse

UA = "Mozilla/5.0 (compatible; launch-checklist-audit/0.1)"
SKIP_EXT = re.compile(r"\.(png|jpe?g|gif|webp|svg|ico|pdf|zip|mp4|webm|mp3|css|js|json|xml|txt|woff2?|ttf)$", re.I)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def request(url, timeout, follow=True, method="GET"):
    """Return dict(status, headers, body, url, ms). Never raises for HTTP errors."""
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
    t0 = time.time()
    try:
        r = opener.open(req, timeout=timeout)
        body = r.read(5_000_000) if method == "GET" else b""
        return {"status": r.status, "headers": r.headers, "body": body, "url": r.geturl(), "ms": int((time.time() - t0) * 1000)}
    except urllib.error.HTTPError as e:
        body = e.read(200_000) if method == "GET" else b""
        return {"status": e.code, "headers": e.headers, "body": body, "url": url, "ms": int((time.time() - t0) * 1000)}
    except Exception as e:  # noqa: BLE001
        return {"status": None, "error": str(e), "headers": {}, "body": b"", "url": url, "ms": int((time.time() - t0) * 1000)}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._t = False
        self.meta = {}
        self.links = []
        self.anchors = []  # (href, text)
        self._a = None
        self.h1 = 0
        self.imgs_no_alt = []
        self.lang = None
        self.icons = []
        self.canonical = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._t = True
            self.title = self.title or ""
        elif tag == "meta":
            k = (a.get("name") or a.get("property") or "").lower()
            if k and k not in self.meta:
                self.meta[k] = a.get("content", "").strip()
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonical = a.get("href")
            if "icon" in rel or "apple-touch-icon" in rel:
                self.icons.append((" ".join(rel), a.get("href")))
        elif tag == "a" and a.get("href"):
            self._a = [a["href"], ""]
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img":
            if "alt" not in a:
                self.imgs_no_alt.append(a.get("src", "?"))

    def handle_endtag(self, tag):
        if tag == "title":
            self._t = False
        elif tag == "a" and self._a:
            self.anchors.append((self._a[0], self._a[1].strip()))
            self.links.append(self._a[0])
            self._a = None

    def handle_data(self, d):
        if self._t:
            self.title += d
        if self._a is not None:
            self._a[1] += d


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, where, msg):
        self.items.append({"level": level, "where": where, "message": msg})

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)


def audit_page(url, res, rep, base_host):
    p = PageParser()
    try:
        p.feed(res["body"].decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        rep.add("WARN", url, f"HTML parse problem: {e}")
    path = urlparse(url).path or "/"
    title = (p.title or "").strip()
    if not title:
        rep.add("FAIL", path, "missing <title>")
    elif not 10 <= len(title) <= 60:
        rep.add("WARN", path, f"title length {len(title)} (aim 10-60): {title!r}")
    desc = p.meta.get("description", "")
    if not desc:
        rep.add("FAIL", path, "missing meta description")
    elif not 50 <= len(desc) <= 160:
        rep.add("WARN", path, f"meta description length {len(desc)} (aim 50-160)")
    if p.h1 == 0:
        rep.add("WARN", path, "no <h1>")
    elif p.h1 > 1:
        rep.add("WARN", path, f"{p.h1} <h1> elements (use one)")
    if not p.lang:
        rep.add("FAIL", path, "<html> has no lang attribute")
    if "viewport" not in p.meta:
        rep.add("FAIL", path, "missing <meta name=viewport> (mobile rendering)")
    if not p.canonical:
        rep.add("WARN", path, "no <link rel=canonical>")
    else:
        cu = urlparse(p.canonical)
        if not cu.scheme:
            rep.add("WARN", path, f"canonical is relative: {p.canonical}")
        elif cu.hostname != base_host:
            rep.add("WARN", path, f"canonical points to another host: {p.canonical}")
        if cu.hostname in ("localhost", "127.0.0.1") and base_host not in ("localhost", "127.0.0.1"):
            rep.add("FAIL", path, "canonical points at localhost")
    for k in ("og:title", "og:description", "og:image"):
        if k not in p.meta:
            rep.add("WARN", path, f"missing {k} (share previews)")
    if "og:image" in p.meta and not urlparse(p.meta["og:image"]).scheme:
        rep.add("FAIL", path, "og:image must be an absolute URL")
    if "twitter:card" not in p.meta:
        rep.add("WARN", path, "missing twitter:card")
    robots = p.meta.get("robots", "").lower()
    if "noindex" in robots:
        rep.add("WARN", path, f"page has robots meta {robots!r} - intended?")
    xrt = (res["headers"].get("X-Robots-Tag") or "").lower() if res["headers"] else ""
    if "noindex" in xrt:
        rep.add("WARN", path, f"X-Robots-Tag: {xrt} - intended?")
    if p.imgs_no_alt:
        rep.add("WARN", path, f"{len(p.imgs_no_alt)} <img> without alt, e.g. {p.imgs_no_alt[0]}")
    kb = len(res["body"]) // 1024
    if kb > 500:
        rep.add("WARN", path, f"HTML is {kb} KB (large)")
    if res["ms"] > 1500:
        rep.add("WARN", path, f"response took {res['ms']} ms")
    return p, title, desc


def find_link(anchors, patterns):
    for href, text in anchors:
        s = (href + " " + text).lower()
        if any(re.search(pt, s) for pt in patterns):
            return href
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sells", action="store_true", help="site sells something: refund policy required")
    a = ap.parse_args()

    start = a.url if "://" in a.url else "https://" + a.url
    bu = urlparse(start)
    origin = f"{bu.scheme}://{bu.netloc}"
    host = bu.hostname
    rep = Report()

    first = request(start, a.timeout)
    if first["status"] is None:
        print(f"cannot reach {start}: {first.get('error')}", file=sys.stderr)
        return 2

    # ---- crawl ----
    queue, seen, pages = [start], set(), {}
    all_anchors = []
    titles, descs = defaultdict(list), defaultdict(list)
    while queue and len(pages) < a.max_pages:
        u = queue.pop(0)
        if u in seen:
            continue
        seen.add(u)
        res = first if u == start else request(u, a.timeout)
        ctype = (res["headers"].get("Content-Type") or "") if res["headers"] else ""
        if res["status"] != 200:
            rep.add("FAIL", urlparse(u).path or "/", f"linked page returns HTTP {res['status']}")
            continue
        if "html" not in ctype:
            continue
        p, t, d = audit_page(u, res, rep, host)
        pages[u] = {"status": res["status"], "ms": res["ms"], "title": t}
        if t:
            titles[t].append(u)
        if d:
            descs[d].append(u)
        all_anchors.extend(p.anchors)
        for href in p.links:
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            nu = urldefrag(urljoin(u, href))[0]
            pu = urlparse(nu)
            if pu.hostname == host and not SKIP_EXT.search(pu.path) and nu not in seen:
                queue.append(nu)
    for t, us in titles.items():
        if len(us) > 1:
            rep.add("WARN", "site", f"duplicate title on {len(us)} pages: {t!r}")
    for d, us in descs.items():
        if len(us) > 1:
            rep.add("WARN", "site", f"duplicate meta description on {len(us)} pages")

    # ---- robots.txt ----
    sitemap_urls = []
    r = request(origin + "/robots.txt", a.timeout)
    if r["status"] != 200:
        rep.add("FAIL", "/robots.txt", f"missing (HTTP {r['status']})")
    else:
        txt = r["body"].decode("utf-8", "replace")
        ua_all, blocks_all = False, False
        for line in txt.splitlines():
            line = line.split("#")[0].strip()
            if not line or ":" not in line:
                continue
            k, v = [x.strip() for x in line.split(":", 1)]
            kl = k.lower()
            if kl == "user-agent":
                ua_all = v == "*"
            elif kl == "disallow" and ua_all and v == "/":
                blocks_all = True
            elif kl == "sitemap":
                sitemap_urls.append(v)
        if blocks_all:
            rep.add("FAIL", "/robots.txt", "Disallow: / for User-agent: * blocks all crawlers")
        if not sitemap_urls:
            rep.add("WARN", "/robots.txt", "no Sitemap: line")

    # ---- sitemap ----
    sm = sitemap_urls[0] if sitemap_urls else origin + "/sitemap.xml"
    r = request(sm, a.timeout)
    sm_path = urlparse(sm).path
    if r["status"] != 200:
        rep.add("FAIL", sm_path, f"sitemap not reachable (HTTP {r['status']})")
    else:
        try:
            root = ET.fromstring(r["body"])
            locs = [el.text.strip() for el in root.iter() if el.tag.endswith("loc") and el.text]
            if not locs:
                rep.add("FAIL", sm_path, "sitemap has no <loc> entries")
            if urlparse(sm).hostname != host:
                rep.add("WARN", sm_path, "sitemap is on a different host")
            bad_host = [l for l in locs if urlparse(l).hostname != host]
            if bad_host:
                rep.add("FAIL", sm_path, f"{len(bad_host)} sitemap URLs on another host, e.g. {bad_host[0]} (wrong base URL env?)")
            is_index = root.tag.endswith("sitemapindex")
            sample = [l for l in locs if urlparse(l).hostname == host][:10]
            for l in sample:
                rr = request(l, a.timeout, method="GET")
                if rr["status"] != 200:
                    rep.add("FAIL", sm_path, f"sitemap URL returns HTTP {rr['status']}: {l}")
            rep.add("INFO", sm_path, f"{len(locs)} entries{' (sitemap index)' if is_index else ''}, checked {len(sample)}")
        except ET.ParseError as e:
            rep.add("FAIL", sm_path, f"sitemap is not valid XML: {e}")

    # ---- favicon / icons ----
    home = PageParser()
    home.feed(first["body"].decode("utf-8", "replace"))
    icon_href = next((h for rel, h in home.icons if "icon" in rel.split() or rel == "shortcut icon"), None) or "/favicon.ico"
    r = request(urljoin(start, icon_href), a.timeout)
    if r["status"] != 200:
        rep.add("FAIL", "favicon", f"{icon_href} returns HTTP {r['status']}")
    if not any("apple-touch-icon" in rel for rel, _ in home.icons):
        r = request(origin + "/apple-touch-icon.png", a.timeout)
        if r["status"] != 200:
            rep.add("WARN", "favicon", "no apple-touch-icon (iOS home screen / some link previews)")

    # ---- 404 ----
    missing = origin + f"/this-page-should-not-exist-{uuid.uuid4().hex[:8]}"
    r = request(missing, a.timeout, follow=False)
    if r["status"] in (301, 302, 307, 308):
        rep.add("FAIL", "404", f"unknown URL redirects ({r['status']}) instead of returning 404 (soft 404)")
    elif r["status"] == 200:
        rep.add("FAIL", "404", "unknown URL returns 200 (soft 404) - return a real 404 status")
    elif r["status"] != 404:
        rep.add("WARN", "404", f"unknown URL returns HTTP {r['status']} (expected 404)")

    # ---- https ----
    if bu.scheme == "https" and host not in ("localhost", "127.0.0.1"):
        r = request(f"http://{bu.netloc}/", a.timeout, follow=False)
        loc = (r["headers"].get("Location") or "") if r["headers"] else ""
        if r["status"] is None:
            rep.add("WARN", "https", "http:// not reachable (fine if port 80 is closed on purpose)")
        elif r["status"] not in (301, 308, 302, 307) or not loc.startswith("https://"):
            rep.add("FAIL", "https", f"http:// does not redirect to https (HTTP {r['status']})")
    elif bu.scheme == "http" and host not in ("localhost", "127.0.0.1"):
        rep.add("FAIL", "https", "site audited over plain http")

    # ---- legal pages ----
    if not find_link(all_anchors, [r"privacy", r"隐私"]):
        rep.add("FAIL", "legal", "no link to a privacy policy found")
    if not find_link(all_anchors, [r"terms", r"条款", r"/tos\b"]):
        rep.add("WARN", "legal", "no link to terms of service found")
    if not find_link(all_anchors, [r"refund", r"退款"]):
        rep.add("FAIL" if a.sells else "WARN", "legal", "no link to a refund policy found (required by most payment providers)")

    # ---- llms.txt (informational) ----
    r = request(origin + "/llms.txt", a.timeout)
    rep.add("INFO", "/llms.txt", "present" if r["status"] == 200 else "not present (optional)")

    fails, warns = rep.count("FAIL"), rep.count("WARN")
    if a.json:
        print(json.dumps({"url": start, "pages": pages, "fail": fails, "warn": warns, "items": rep.items}, indent=2, ensure_ascii=False))
    else:
        print(f"Launch audit: {start}  ({len(pages)} pages crawled)")
        for level in ("FAIL", "WARN", "INFO"):
            for i in rep.items:
                if i["level"] == level:
                    print(f"  [{level}] {i['where']}: {i['message']}")
        print(f"\nSummary: {fails} FAIL, {warns} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
