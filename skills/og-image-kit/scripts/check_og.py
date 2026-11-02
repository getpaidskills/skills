#!/usr/bin/env python3
"""Check Open Graph / Twitter card tags and the og:image for one or more URLs.

Usage:
  python3 check_og.py URL [URL ...] [--json] [--timeout 15]

Standard library only. Exit code: 0 = no errors, 1 = at least one ERROR, 2 = usage problem.
"""
import argparse
import json
import struct
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; og-image-kit-check/0.1; +https://agentskills.io)"
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").strip().lower()
            if key and "content" in a and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data


def fetch(url, timeout, limit=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read(limit) if limit else r.read()
        return r.status, r.headers, body, r.geturl()


def image_size(data):
    """Return (w, h, kind) for PNG/JPEG/GIF/WEBP headers, or (None, None, kind)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return w, h, "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        w, h = struct.unpack("<HH", data[6:10])
        return w, h, "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 " and len(data) >= 30:
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF, "webp"
        if chunk == b"VP8L" and len(data) >= 25:
            b = data[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return w, h, "webp"
        if chunk == b"VP8X" and len(data) >= 30:
            w = 1 + int.from_bytes(data[24:27], "little")
            h = 1 + int.from_bytes(data[27:30], "little")
            return w, h, "webp"
        return None, None, "webp"
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h, "jpeg"
            seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
            i += 2 + seg_len
        return None, None, "jpeg"
    return None, None, "unknown"


def check(url, timeout):
    issues = []  # (level, message)

    def err(m):
        issues.append(("ERROR", m))

    def warn(m):
        issues.append(("WARN", m))

    result = {"url": url, "tags": {}, "image": None, "issues": issues}
    try:
        status, headers, body, final = fetch(url, timeout)
    except urllib.error.HTTPError as e:
        err(f"page returned HTTP {e.code}")
        return result
    except Exception as e:  # noqa: BLE001
        err(f"could not fetch page: {e}")
        return result
    if final != url:
        result["final_url"] = final
    p = MetaParser()
    p.feed(body.decode("utf-8", "replace"))
    m = p.meta
    keys = ["og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name",
            "og:image:width", "og:image:height", "og:image:alt", "twitter:card", "twitter:title",
            "twitter:description", "twitter:image", "twitter:site"]
    result["tags"] = {k: m[k] for k in keys if k in m}
    result["title"] = (p.title or "").strip()

    for k in ("og:title", "og:description", "og:image"):
        if not m.get(k):
            err(f"missing {k}")
    if not m.get("twitter:card"):
        err("missing twitter:card (use summary_large_image for big previews)")
    elif m["twitter:card"] not in ("summary_large_image", "summary", "player", "app"):
        warn(f"unusual twitter:card value {m['twitter:card']!r}")
    for k in ("og:url", "og:type"):
        if not m.get(k):
            warn(f"missing {k}")
    if m.get("og:title") and len(m["og:title"]) > 90:
        warn(f"og:title is {len(m['og:title'])} chars; it will be truncated (aim for <= 60-70)")
    if m.get("og:description") and len(m["og:description"]) > 200:
        warn(f"og:description is {len(m['og:description'])} chars; aim for <= 160")
    if m.get("og:url") and urlparse(m["og:url"]).hostname in ("localhost", "127.0.0.1") and \
            urlparse(url).hostname not in ("localhost", "127.0.0.1"):
        err("og:url points at localhost on a non-local page (metadataBase / site URL not set?)")

    img = m.get("og:image") or m.get("twitter:image")
    if img:
        parsed = urlparse(img)
        if not parsed.scheme:
            err(f"og:image is not an absolute URL: {img!r} (scrapers need https://...)")
            img = urljoin(final, img)
        elif urlparse(url).scheme == "https" and parsed.scheme != "https":
            warn("og:image uses http on an https page")
        if parsed.hostname in ("localhost", "127.0.0.1") and urlparse(url).hostname not in ("localhost", "127.0.0.1"):
            err("og:image points at localhost on a non-local page")
        info = {"url": img}
        result["image"] = info
        try:
            status, h, data, _ = fetch(img, timeout, limit=MAX_IMAGE_BYTES + 1)
            ctype = h.get("Content-Type", "")
            info["content_type"] = ctype
            info["bytes"] = len(data)
            if not ctype.startswith("image/"):
                err(f"og:image content-type is {ctype!r}, expected image/*")
            if len(data) > MAX_IMAGE_BYTES:
                err("og:image is larger than 5 MB (X and others reject it)")
            elif len(data) > 1024 * 1024:
                warn(f"og:image is {len(data)//1024} KB; under ~1 MB loads faster in feeds")
            w, hgt, kind = image_size(data)
            info.update({"width": w, "height": hgt, "format": kind})
            if kind == "unknown":
                warn("could not detect image format (use PNG or JPEG)")
            if w and hgt:
                ratio = w / hgt
                if w < 600:
                    err(f"og:image is {w}x{hgt}; use at least 1200x630 (min 600 wide for large cards)")
                elif abs(ratio - 1.91) > 0.15:
                    warn(f"og:image is {w}x{hgt} (ratio {ratio:.2f}); 1200x630 (1.91:1) avoids cropping")
                declared_w, declared_h = m.get("og:image:width"), m.get("og:image:height")
                if declared_w and declared_h and (declared_w != str(w) or declared_h != str(hgt)):
                    warn(f"og:image:width/height say {declared_w}x{declared_h} but image is {w}x{hgt}")
            if kind == "webp":
                warn("WebP og:image is not supported by every scraper; PNG/JPEG is safest")
        except urllib.error.HTTPError as e:
            err(f"og:image returned HTTP {e.code}")
        except Exception as e:  # noqa: BLE001
            err(f"could not fetch og:image: {e}")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a text report")
    ap.add_argument("--timeout", type=float, default=15)
    a = ap.parse_args()
    for u in a.urls:
        if not urlparse(u).scheme.startswith("http"):
            print(f"not an http(s) URL: {u}", file=sys.stderr)
            return 2
    results = [check(u, a.timeout) for u in a.urls]
    errors = sum(1 for r in results for lvl, _ in r["issues"] if lvl == "ERROR")
    if a.json:
        out = [dict(r, issues=[{"level": l, "message": m} for l, m in r["issues"]]) for r in results]
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"\n== {r['url']}")
            for k, v in r["tags"].items():
                print(f"   {k}: {v}")
            if r["image"]:
                i = r["image"]
                print(f"   image: {i.get('width')}x{i.get('height')} {i.get('format')} {i.get('bytes')} bytes")
            if not r["issues"]:
                print("   OK - no issues")
            for lvl, msg in r["issues"]:
                print(f"   {lvl}: {msg}")
        print(f"\n{len(results)} page(s), {errors} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
