#!/usr/bin/env python3
"""Generate 1200x630 Open Graph PNGs for static sites.

Usage:
  python3 generate_og.py --pages pages.json --out public/og [--brand NAME] [--bg #0f172a]
                         [--fg #ffffff] [--accent #38bdf8] [--font path.ttf] [--logo logo.png]

pages.json: [{"slug": "index", "title": "...", "subtitle": "..."}, ...]
Writes <out>/<slug>.png. Requires Pillow: pip install pillow
For Chinese/Japanese/Korean titles pass a CJK font, e.g. --font NotoSansSC-Bold.ttf
"""
import argparse
import json
import os
import re
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

W, H, MARGIN = 1200, 630, 80
FALLBACK_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def load_font(path, size):
    for p in [path] + FALLBACK_FONTS if path else FALLBACK_FONTS:
        if p and os.path.exists(p):
            return ImageFont.truetype(p, size)
    print("warning: no TTF font found, using Pillow default (pass --font)", file=sys.stderr)
    return ImageFont.load_default(size=size)


def wrap(draw, text, font, max_w):
    """Wrap by words; falls back to per-character wrapping for CJK / long words."""
    tokens = re.findall(r"\S+\s*", text) if " " in text else list(text)
    lines, cur = [], ""
    for t in tokens:
        trial = cur + t
        if draw.textlength(trial.rstrip(), font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = t
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def fit_title(draw, text, font_path, max_w, max_lines=3):
    for size in range(76, 34, -4):
        f = load_font(font_path, size)
        lines = wrap(draw, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines, size
    f = load_font(font_path, 36)
    lines = wrap(draw, text, f, max_w)[:max_lines]
    lines[-1] = lines[-1].rstrip(" .") + "…"
    return f, lines, 36


def render(page, a):
    img = Image.new("RGB", (W, H), a.bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=a.accent)
    x = MARGIN
    if a.logo and os.path.exists(a.logo):
        logo = Image.open(a.logo).convert("RGBA")
        logo.thumbnail((64, 64))
        img.paste(logo, (x, MARGIN), logo)
        bx = x + logo.width + 20
    else:
        bx = x
    brand_font = load_font(a.font, 34)
    d.text((bx, MARGIN + 12), a.brand, font=brand_font, fill=a.accent)

    tf, lines, size = fit_title(d, page["title"], a.font, W - 2 * MARGIN)
    y = 210 if len(lines) < 3 else 180
    for line in lines:
        d.text((x, y), line, font=tf, fill=a.fg)
        y += int(size * 1.2)
    sub = page.get("subtitle")
    if sub:
        sf = load_font(a.font, 32)
        sl = wrap(d, sub, sf, W - 2 * MARGIN)[:2]
        y += 16
        for line in sl:
            d.text((x, y), line, font=sf, fill=a.muted)
            y += 42
    if a.url:
        uf = load_font(a.font, 28)
        d.text((x, H - MARGIN - 10), a.url, font=uf, fill=a.muted)
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--brand", default="")
    ap.add_argument("--url", default="", help="domain shown bottom-left, e.g. example.com")
    ap.add_argument("--bg", default="#0f172a")
    ap.add_argument("--fg", default="#ffffff")
    ap.add_argument("--muted", default="#94a3b8")
    ap.add_argument("--accent", default="#38bdf8")
    ap.add_argument("--font", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args()
    with open(a.pages, encoding="utf-8") as f:
        pages = json.load(f)
    if not isinstance(pages, list) or not pages:
        sys.exit("pages.json must be a non-empty JSON list")
    os.makedirs(a.out, exist_ok=True)
    for p in pages:
        if "slug" not in p or "title" not in p:
            sys.exit(f"each page needs slug and title: {p}")
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", p["slug"]) or ".." in p["slug"]:
            sys.exit(f"unsafe slug: {p['slug']!r}")
        path = os.path.join(a.out, p["slug"] + ".png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        render(p, a).save(path, "PNG", optimize=True)
        print(f"wrote {path} ({os.path.getsize(path)//1024} KB)")


if __name__ == "__main__":
    main()
