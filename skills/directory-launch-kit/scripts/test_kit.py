#!/usr/bin/env python3
"""Self-test for make_kit.py and check_listing.py (offline: a local HTTP server stands in for directories).
   python3 scripts/test_kit.py      (Pillow needed for the image checks; they are skipped without it)"""
from __future__ import annotations

import csv
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
failed = 0


def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    failed += 0 if cond else 1


def run(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


with open(os.path.join(HERE, "..", "references", "directories.json"), encoding="utf-8") as f:
    data = json.load(f)
ids = [d["id"] for d in data["directories"]]
check(len(ids) == len(set(ids)), "directory ids are unique")
check(all(d["submit_url"].startswith("https://") for d in data["directories"]), "every submit_url is https")
check(all(d.get("cost") and d.get("cost_source") for d in data["directories"]), "every directory records cost and where it was read")

try:
    from PIL import Image
    have_pil = True
except ImportError:
    have_pil = False

with tempfile.TemporaryDirectory() as tmp:
    product = json.load(open(os.path.join(HERE, "..", "assets", "product.example.json"), encoding="utf-8"))
    if have_pil:
        Image.new("RGB", (800, 800), "#059669").save(os.path.join(tmp, "logo.png"))
        Image.new("RGB", (1440, 900), "#0f172a").save(os.path.join(tmp, "shot-1.png"))
        Image.new("RGB", (1440, 900), "#1e293b").save(os.path.join(tmp, "shot-2.png"))
    pj = os.path.join(tmp, "product.json")
    json.dump(product, open(pj, "w"))
    out = os.path.join(tmp, "kit")
    r = run(os.path.join(HERE, "make_kit.py"), "--product", pj, "--out", out, *([] if have_pil else ["--no-images"]))
    check(r.returncode == 0, f"example product builds a kit (exit {r.returncode}) {r.stderr[-300:]}")
    copy = open(os.path.join(out, "copy.md"), encoding="utf-8").read()
    check("## Product Hunt" in copy and "## Hacker News (Show HN)" in copy, "copy.md has Product Hunt and Show HN")
    check("## Dang.ai" not in copy and "AI tools only" in copy, "AI-only directories skipped for a non-AI product")
    check("## Claude Marketplaces" not in copy, "agent-skill directories skipped unless agent_skills is true")
    check(product["maker_comment"] in copy, "maker comment copied verbatim, not rewritten")
    rows = list(csv.DictReader(open(os.path.join(out, "tracker.csv"), encoding="utf-8")))
    check(rows and all(r["status"] == "todo" for r in rows), f"tracker has {len(rows)} todo rows")
    if have_pil:
        sizes = {fn: Image.open(os.path.join(out, "images", fn)).size for fn in os.listdir(os.path.join(out, "images"))}
        check(sizes.get("ph-thumbnail-240.png") == (240, 240), "Product Hunt thumbnail is 240x240")
        check(sizes.get("gallery-1-1270x760.png") == (1270, 760) and sizes.get("gallery-2-1270x760.png") == (1270, 760), "two 1270x760 gallery images")
        check(sizes.get("og-1200x630.png") == (1200, 630), "OG image is 1200x630")
        check(all(os.path.getsize(os.path.join(out, "images", f)) < 3 * 1024 * 1024 for f in sizes), "every image under 3 MB")

    # progress survives a re-run
    rows[0]["status"], rows[0]["listing_url"] = "submitted", "http://127.0.0.1:0/x"
    with open(os.path.join(out, "tracker.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    run(os.path.join(HERE, "make_kit.py"), "--product", pj, "--out", out, "--no-images")
    rows2 = list(csv.DictReader(open(os.path.join(out, "tracker.csv"), encoding="utf-8")))
    check(rows2[0]["status"] == "submitted", "re-running keeps statuses already recorded")

    # over-limit tagline is reported, not truncated
    long = dict(product, tagline="x" * 75)
    json.dump(long, open(pj, "w"))
    r = run(os.path.join(HERE, "make_kit.py"), "--product", pj, "--out", os.path.join(tmp, "kit2"), "--no-images", "--only", "product-hunt")
    c2 = open(os.path.join(tmp, "kit2", "copy.md"), encoding="utf-8").read()
    check(r.returncode == 1 and "OVER LIMIT by 15" in c2 and "x" * 75 in c2, "75-char tagline flagged OVER LIMIT by 15 and kept whole")

    # check_listing against a local server: one followed link, one nofollow, one without a link
    pages = {
        "/follow": '<a href="https://acme-invoices.example.com/?ref=dir">Acme</a>',
        "/nofollow": '<a rel="nofollow ugc" href="https://www.acme-invoices.example.com">Acme</a>',
        "/none": '<a href="https://other.example.org">Other</a>',
    }

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            b = pages.get(self.path)
            self.send_response(200 if b else 404); self.end_headers(); self.wfile.write((b or "").encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    t = os.path.join(tmp, "t.csv")
    with open(t, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "directory", "status", "listing_url", "link_rel"]); w.writeheader()
        for name in ("follow", "nofollow", "none", "missing"):
            w.writerow({"id": name, "directory": name, "status": "submitted", "listing_url": base + "/" + name, "link_rel": ""})
        w.writerow({"id": "todo", "directory": "todo", "status": "todo", "listing_url": "", "link_rel": ""})
    r = run(os.path.join(HERE, "check_listing.py"), "--tracker", t, "--domain", "acme-invoices.example.com", "--write")
    got = {row["id"]: (row["status"], row["link_rel"]) for row in csv.DictReader(open(t))}
    srv.shutdown()
    check(got["follow"] == ("live", "follow"), f"followed link detected {got['follow']}")
    check(got["nofollow"] == ("live", "nofollow"), f"nofollow/ugc link detected {got['nofollow']}")
    check(got["none"] == ("no-link", ""), f"page without a link is no-link {got['none']}")
    check(got["missing"][0] == "error", f"404 listing is error {got['missing']}")
    check(got["todo"] == ("todo", ""), "rows without listing_url untouched")

print(f"\n{'all passed' if not failed else f'{failed} failed'}")
sys.exit(1 if failed else 0)
