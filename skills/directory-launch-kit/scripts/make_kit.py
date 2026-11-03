#!/usr/bin/env python3
"""Build a directory launch kit from one product.json: per-directory copy within each field limit,
a submission tracker (CSV) and correctly sized images. Python 3.9+; images need Pillow.

  python3 scripts/make_kit.py --product product.json --out launch-kit
  python3 scripts/make_kit.py --product product.json --out launch-kit --only product-hunt,show-hn
  python3 scripts/make_kit.py --product product.json --out launch-kit --no-images

It never invents copy: every sentence comes from product.json. Fields that are too long are reported
as OVER LIMIT (exit code 1) so you shorten them yourself instead of the script cutting mid-word.
Nothing is submitted anywhere.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIRECTORIES = os.path.join(HERE, "..", "references", "directories.json")

REQUIRED = ["name", "url", "tagline", "description"]
# Which product.json field fills which directory form field.
FIELD_SOURCE = {
    "name": "name", "title": "show_hn_title", "tagline": "tagline", "pitch": "tagline",
    "description": "description", "website_url": "url",
}
IMAGE_SPECS = {
    # file name: (width, height, source, note)
    "ph-thumbnail-240.png": (240, 240, "logo", "Product Hunt thumbnail, square, under 3 MB"),
    "logo-512.png": (512, 512, "logo", "square logo for directories that ask for an icon"),
    "og-1200x630.png": (1200, 630, "screenshot", "link preview / og:image"),
    "gallery-{n}-1270x760.png": (1270, 760, "screenshot", "Product Hunt gallery (upload at least 2)"),
    "screenshot-{n}-1920x1080.png": (1920, 1080, "screenshot", "16:9 screenshot for most directories"),
}
MAX_BYTES = 3 * 1024 * 1024


def load_product(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        p = json.load(f)
    missing = [k for k in REQUIRED if not str(p.get(k, "")).strip()]
    if missing:
        sys.exit(f"product.json is missing: {', '.join(missing)}")
    if not p["url"].startswith("https://"):
        sys.exit("url must be the live https:// address of the product")
    p.setdefault("show_hn_title", f"Show HN: {p['name']} – {p['tagline']}")
    return p


def applies(d: dict, p: dict) -> tuple[bool, str]:
    """Skip directories the product does not belong in (an honest submission list beats a long one)."""
    if d["kind"] == "ai-directory" and not p.get("ai"):
        return False, "AI tools only; product.json says ai: false"
    if d["id"] == "openalternative" and not p.get("open_source"):
        return False, "open-source products only"
    if d["kind"] == "agent-skills" and not p.get("agent_skills"):
        return False, "only for Agent Skills / Claude plugins / MCP servers"
    if d["id"] == "devhunt" and not p.get("developer_tool"):
        return False, "developer tools only"
    if d["id"] == "sideprojectors" and not p.get("open_to_offers"):
        return False, "marketplace for selling side projects; product.json open_to_offers is false"
    if d["id"] == "show-hn" and p.get("requires_signup_to_try"):
        return True, "WARNING: Show HN wants something people can try without signup; add a demo or no-signup path first"
    return True, ""


def copy_section(d: dict, p: dict) -> tuple[str, int]:
    over = 0
    lines = [f"## {d['name']}", "", f"- Submit: {d['submit_url']}", f"- Cost ({DATA['checked']}): {d['cost']}"]
    if d.get("verify"):
        lines.append(f"- Verify first: {d['verify']}")
    for r in d.get("rules", []):
        lines.append(f"- Rule: {r}")
    if d.get("backlink_required"):
        lines.append(f"- Backlink required: {d['backlink_required']}")
    lines.append("")
    for field, limit in d.get("fields", {}).items():
        src = FIELD_SOURCE.get(field, field)
        val = str(p.get(src, "")).strip()
        n = len(val)
        flag = f"OVER LIMIT by {n - limit}" if n > limit else "ok"
        over += n > limit
        lines += [f"**{field}** ({n}/{limit}, {flag})", "", "```text", val, "```", ""]
    if not d.get("fields"):
        lines += ["**name**", "", "```text", p["name"], "```", "", "**tagline**", "", "```text", p["tagline"], "```", "",
                  "**description**", "", "```text", p["description"], "```", ""]
    if d["id"] == "saashub" and p.get("competitors"):
        lines += ["**competitors to list**", "", "```text", ", ".join(p["competitors"]), "```", ""]
    if d["kind"] in ("launch", "community") and p.get("maker_comment"):
        lines += ["**first comment (yours, post it right after submitting)**", "", "```text", p["maker_comment"], "```", ""]
    return "\n".join(lines), over


def fit(img, w: int, h: int, bg):
    """Scale to fit inside w x h without cropping, centred on a solid background."""
    from PIL import Image
    img = img.convert("RGBA")
    scale = min(w / img.width, h / img.height)
    resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), bg)
    canvas.paste(resized, ((w - resized.width) // 2, (h - resized.height) // 2), resized)
    return canvas.convert("RGB")


def make_images(p: dict, out: str, base: str) -> list[str]:
    try:
        from PIL import Image, ImageColor
    except ImportError:
        return ["Pillow not installed: pip install pillow (or pass --no-images)"]
    img_cfg = p.get("images", {})
    bg = ImageColor.getrgb(img_cfg.get("background", "#ffffff")) + (255,)
    logo = img_cfg.get("logo")
    shots = img_cfg.get("screenshots", [])
    notes, d = [], os.path.join(out, "images")
    os.makedirs(d, exist_ok=True)
    resolve = lambda f: f if os.path.isabs(f) else os.path.join(base, f)  # noqa: E731
    for name, (w, h, src, note) in IMAGE_SPECS.items():
        sources = [logo] if src == "logo" else shots[:1] if "{n}" not in name else shots[:5]
        sources = [s for s in sources if s]
        if not sources:
            notes.append(f"skipped {name}: no {src} in product.json images")
            continue
        for i, s in enumerate(sources, 1):
            fn = name.format(n=i)
            im = fit(Image.open(resolve(s)), w, h, bg)
            path = os.path.join(d, fn)
            im.save(path, optimize=True)
            size = os.path.getsize(path)
            if size > MAX_BYTES:
                im.save(path[:-4] + ".jpg", quality=88, optimize=True)
                os.remove(path)
                path, size = path[:-4] + ".jpg", os.path.getsize(path[:-4] + ".jpg")
            notes.append(f"{os.path.relpath(path, out)}  {w}x{h}  {size // 1024} KB  ({note})")
        if src == "screenshot" and "gallery" in name and len(sources) < 2:
            notes.append("WARNING: Product Hunt shows the gallery only with at least 2 images; add another screenshot")
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--product", required=True)
    ap.add_argument("--out", default="launch-kit")
    ap.add_argument("--only", help="comma-separated directory ids")
    ap.add_argument("--no-images", action="store_true")
    a = ap.parse_args()
    p = load_product(a.product)
    os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None

    sections, rows, skipped, over_total = [], [], [], 0
    for d in DATA["directories"]:
        if only and d["id"] not in only:
            continue
        ok, why = applies(d, p)
        if not ok:
            skipped.append(f"- {d['name']}: {why}")
            continue
        text, over = copy_section(d, p)
        if why:
            text = text.replace("\n\n", f"\n\n> {why}\n\n", 1)
        sections.append(text)
        over_total += over
        rows.append({"id": d["id"], "directory": d["name"], "submit_url": d["submit_url"], "kind": d["kind"],
                     "cost_observed": d["cost"], "checked": DATA["checked"],
                     "backlink_required": d.get("backlink_required") or "no",
                     "status": "todo", "submitted_on": "", "listing_url": "", "link_rel": "", "notes": ""})

    header = [f"# Directory launch kit: {p['name']}", "",
              f"Product: {p['url']}  ", f"Directory data checked: {DATA['checked']} (re-run scripts/check_directories.py before paying for anything)", "",
              f"{len(rows)} directories selected, {len(skipped)} skipped, {over_total} fields over their limit.", ""]
    if skipped:
        header += ["Skipped:", *skipped, ""]
    with open(os.path.join(a.out, "copy.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n" + "\n\n".join(sections) + "\n")
    tracker = os.path.join(a.out, "tracker.csv")
    if os.path.exists(tracker):
        # keep progress the user already recorded
        with open(tracker, newline="", encoding="utf-8") as f:
            old = {r["id"]: r for r in csv.DictReader(f)}
        for r in rows:
            for k in ("status", "submitted_on", "listing_url", "link_rel", "notes"):
                if old.get(r["id"], {}).get(k):
                    r[k] = old[r["id"]][k]
    with open(tracker, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id"])
        w.writeheader()
        w.writerows(rows)

    notes = [] if a.no_images else make_images(p, a.out, os.path.dirname(os.path.abspath(a.product)))
    print(f"wrote {a.out}/copy.md ({len(rows)} directories), {a.out}/tracker.csv")
    for n in notes:
        print("  " + n)
    if over_total:
        print(f"{over_total} field(s) OVER LIMIT: shorten them in product.json and re-run (see copy.md)")
    return 1 if over_total else 0


with open(DIRECTORIES, encoding="utf-8") as _f:
    DATA = json.load(_f)

if __name__ == "__main__":
    sys.exit(main())
