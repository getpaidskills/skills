# Image sizes

| Asset | Size | Rules | Source |
|---|---|---|---|
| Product Hunt gallery | 1270×760 | at least 2 images before the gallery shows; keep each under 3 MB | Product Hunt help center, "How to post a product" |
| Product Hunt thumbnail | 240×240, square | separate upload, GIF allowed (animates on hover, first frame must work), under 3 MB | Product Hunt help center |
| BetaList icon + screenshots | icon + 1–5 screenshots | each ≤ 3 MB, 10–5000 px per side, png/jpeg/gif/webp/avif; paying needs an icon and a screenshot | betalist.com/agent (2026-11-03) |
| Open Graph / link preview | 1200×630 | absolute URL in `og:image`, ~1.91:1 | Meta and LinkedIn sharing docs |
| Generic directory screenshot | 1920×1080 (16:9) | most directories show screenshots in a 16:9 frame | common practice; check each form |
| Square logo | 512×512 | PNG, no text smaller than the logo itself | common practice |

`make_kit.py` produces all of these from one logo and up to five screenshots, letterboxed on
`images.background` so nothing important is cropped. Open every output and look at it.

## Capturing real screenshots

```bash
npx playwright screenshot --viewport-size=1440,900 https://example.com shot-1.png
npx playwright screenshot --viewport-size=1440,900 --full-page https://example.com/pricing shot-2.png
```
Use a clean account with realistic (not fake-metric) data. Hide personal data, API keys and emails.
For a GIF thumbnail, keep it short and readable; the first frame is what most people see.
