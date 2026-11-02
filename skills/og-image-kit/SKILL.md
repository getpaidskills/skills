---
name: og-image-kit
description: Generates Open Graph / Twitter (X) share images for every page of a website and wires up the og:* and twitter:* meta tags, then verifies the social preview. Supports Next.js App Router (opengraph-image.tsx with next/og ImageResponse), Astro (build-time PNGs via satori + resvg) and any static site (Pillow script). Use when the user asks for OG images, social share cards, link previews, "my link looks bad on X/Slack/LinkedIn/WeChat", twitter:card, or before launching a site.
license: MIT
metadata:
  version: "0.1.0"
  author: GetPaid Skills
---

# og-image-kit

Goal: every public page has a 1200×630 share image and correct `og:*` / `twitter:*`
tags, and you have **verified** them with `scripts/check_og.py`, not just written them.

## Step 1 — Detect the stack

Look at the repo before writing anything:

| Signal | Stack | Go to |
|---|---|---|
| `next` in package.json and an `app/` (or `src/app/`) dir | Next.js App Router | Step 2A |
| `next` with only `pages/` | Next.js Pages Router | Step 2C (static) or add `/api/og` with `ImageResponse` |
| `astro` in package.json | Astro | Step 2B |
| Plain HTML, Hugo, Jekyll, Vite SPA, anything else | Static | Step 2C |

Also find: the site's canonical base URL (env var like `NEXT_PUBLIC_SITE_URL`, `site` in
`astro.config.*`), brand colors, logo, and the font in use. Ask the user only if none can be found.

## Step 2A — Next.js App Router

1. Make sure the root layout exports `metadataBase` (OG URLs must be absolute):
   ```ts
   export const metadata = { metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000") }
   ```
2. Copy `assets/nextjs/opengraph-image.tsx` to `app/opengraph-image.tsx` (site default).
   Edit `BRAND`, colors and tagline.
3. For dynamic routes (blog posts, products) copy it into the route segment, e.g.
   `app/blog/[slug]/opengraph-image.tsx`, and use `assets/nextjs/dynamic-opengraph-image.tsx`,
   which reads `params` and loads the title from your data source.
   In Next.js 15+ `params` is a Promise — `await` it.
4. Also add `twitter-image.tsx` only if the X card must differ; otherwise Next.js reuses the OG image
   when you set `twitter: { card: "summary_large_image" }` in metadata.
5. Per-page text: set `title` and `description` in each page's `metadata` / `generateMetadata`.
6. Custom fonts: load a TTF/OTF (not WOFF2) via `fetch(new URL("./Inter-Bold.ttf", import.meta.url))`
   or `readFile`. CJK text needs a CJK font file or it renders as boxes — subset it to keep size down.

Limits to respect (`next/og` / satori): flexbox only (no grid), every multi-child `div` needs
`display: "flex"`, keep the bundle small — the Next.js `ImageResponse` docs list a 500 KB limit for
JSX + CSS + fonts + images. Large fonts also slow rendering, so subset them.

## Step 2B — Astro

Use `assets/astro/og-endpoint.ts` as `src/pages/og/[...slug].png.ts`. It renders a PNG per page at
build time with `satori` + `@resvg/resvg-js` (`npm i satori @resvg/resvg-js`), and you reference it
from your layout:
```astro
<meta property="og:image" content={new URL(`/og/${slug}.png`, Astro.site)} />
```
`Astro.site` must be set in `astro.config.mjs`. Font file: put a TTF in `src/assets/fonts/`.

## Step 2C — Static sites / anything else

Generate PNGs once and commit them:
```bash
python3 scripts/generate_og.py --pages pages.json --out public/og --brand "Acme" --bg "#0f172a" --fg "#ffffff" --accent "#38bdf8"
```
`pages.json` is a list of `{"slug": "pricing", "title": "...", "subtitle": "..."}` (see
`assets/pages.example.json`). Requires Pillow (`pip install pillow`). Pass `--font path/to/font.ttf`
for brand fonts or CJK text (e.g. Noto Sans SC). Then add tags to each page (template in
`references/meta-tags.md`).

## Step 3 — Required tags (every page)

```html
<meta property="og:title" content="Page title" />
<meta property="og:description" content="One sentence, ≤ ~160 chars" />
<meta property="og:image" content="https://example.com/og/page.png" />   <!-- absolute URL -->
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:url" content="https://example.com/page" />
<meta property="og:type" content="website" />
<meta name="twitter:card" content="summary_large_image" />
```
Next.js generates these from `metadata` + `opengraph-image.tsx`; do not hand-write duplicates.

## Step 4 — Verify (do not skip)

Run against the running site (dev server, preview deploy, or production):
```bash
python3 scripts/check_og.py http://localhost:3000/ http://localhost:3000/pricing
python3 scripts/check_og.py --json https://example.com/   # machine-readable
```
It fetches each page, checks the required tags, that `og:image` is absolute, reachable,
an image content-type, ~1.91:1 and at least 600 px wide, and under 5 MB. Exit code 1 on any error.
Fix everything marked `ERROR`; `WARN` items are recommendations.

Note: social platforms cache previews. After fixing, use the platform's own debugger
(LinkedIn Post Inspector, Facebook Sharing Debugger) to re-scrape. X has no public validator any more;
post in a draft/DM to check. `localhost` URLs cannot be scraped by those tools — deploy first.

## Design rules for the image

- 1200×630, PNG, text inside a ~60 px safe margin; title ≤ ~60 chars, max 3 lines.
- High contrast; it is shown small (~500 px wide) in feeds. Test at 50% zoom.
- Include brand name/logo; avoid tiny text (< 28 px at 1200 width).
- See `references/platform-specs.md` for per-platform notes.

## Done when

- [ ] Every indexable page returns og:title, og:description, og:image (absolute), twitter:card
- [ ] `check_og.py` exits 0 for the home page and at least one page of each route type
- [ ] Images look right (open one PNG and look at it)
