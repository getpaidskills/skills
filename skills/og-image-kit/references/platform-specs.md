# Share-image specs by platform

Numbers below are the commonly documented values; platforms change them without notice.
When in doubt, 1200×630 PNG under 1 MB works everywhere listed.

| Platform | Tags it reads | Recommended size | Notes |
|---|---|---|---|
| Facebook / Meta | `og:*` | 1200×630 (1.91:1) | Smaller than 600×315 shows as a small thumbnail. Re-scrape with the Sharing Debugger. |
| X (Twitter) | `twitter:*`, falls back to `og:*` | 2:1 for `summary_large_image` (1200×630 is fine, slight crop) | Image must be < 5 MB. Needs `twitter:card` or you get a small card. |
| LinkedIn | `og:*` | 1200×627 | Caches ~7 days; use Post Inspector to refresh. |
| Slack / Discord / Telegram | `og:*` (Discord also `theme-color`) | 1200×630 | Fetch happens at paste time; old previews stay cached. |
| WeChat (微信) | Not reliably `og:*`; uses page `<title>`, first large image, or JS-SDK `updateAppMessageShareData` | 300×300+ square icon | For WeChat cards inside the WeChat browser you need the JS-SDK with an ICP-registered domain. Outside of that, there is no reliable control. |
| iMessage | `og:*` | 1200×630 | Uses `og:title` and the image; `og:description` often ignored. |

## Checklist for the image itself

- Safe area: keep text ≥ 60 px from edges (some clients crop to 2:1 or round corners).
- Title ≤ 60 characters, ≥ 48 px font at 1200 width.
- Brand mark on every image.
- PNG for text/graphics, JPEG for photos. Avoid SVG and WebP for og:image.
- Absolute HTTPS URL. No query string tricks needed, but changing the URL (e.g. `?v=2`) is the
  fastest way to bust a platform cache.
