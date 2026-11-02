# What audit_site.py checks and why

| Check | Level | Why it matters |
|---|---|---|
| `<title>` present, 10–60 chars | FAIL / WARN | Search result headline; truncated past ~60 chars. |
| meta description, 50–160 chars | FAIL / WARN | Search snippet and share text fallback. |
| exactly one `<h1>` | WARN | Page topic for crawlers and screen readers. |
| `<html lang>` | FAIL | Accessibility, translation prompts, hreflang sanity. |
| viewport meta | FAIL | Without it mobile renders a zoomed-out desktop page. |
| canonical, absolute, same host | WARN / FAIL (localhost) | Avoids duplicate-content splitting; localhost canonical = env var not set in prod. |
| og:title / og:description / og:image, twitter:card | WARN | Link previews on X, LinkedIn, Slack, Discord. |
| og:image absolute | FAIL | Relative og:image is ignored by every scraper. |
| robots meta / X-Robots-Tag noindex | WARN | Most common "why am I not on Google" cause after launch from a staging config. |
| img without alt | WARN | Accessibility + image search. |
| HTML > 500 KB, response > 1.5 s | WARN | Slow first load; often an inlined data blob. |
| duplicate titles / descriptions | WARN | Pages compete with each other. |
| robots.txt exists, no global Disallow, has Sitemap line | FAIL / WARN | Crawl control. |
| sitemap parses, URLs on same host and return 200 | FAIL | Wrong host = `NEXT_PUBLIC_SITE_URL`/`site` misconfigured. |
| favicon reachable, apple-touch-icon | FAIL / WARN | Browser tab, bookmarks, Google result icon. |
| random URL returns 404 | FAIL | Soft 404s (200 or redirect to home) waste crawl budget and hide broken links. |
| http → https redirect | FAIL | Mixed indexing and insecure first hit. |
| privacy / terms / refund links | FAIL / WARN | Payment providers (Creem, Paddle, Lemon Squeezy, Stripe) review these before approving a store; privacy policy is legally required in most places if you collect any personal data. |
| /llms.txt | INFO | Optional emerging convention for LLM-friendly site summaries. |

Limits: it does not run JavaScript. A client-only SPA will look empty — that is a real finding
(crawlers that don't execute JS see the same thing), but confirm with the user before
recommending SSR/prerendering. For Core Web Vitals use Lighthouse / PageSpeed Insights.
