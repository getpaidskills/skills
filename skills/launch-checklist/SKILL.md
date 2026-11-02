---
name: launch-checklist
description: Pre-launch audit for a website or SaaS - checks SEO tags (title, description, canonical, lang, Open Graph), robots.txt, sitemap.xml, favicon and apple-touch-icon, real 404 status, HTTPS redirect, legal pages (privacy, terms, refund), image alt text, page weight and response time, plus a payment self-check (webhook signature, raw body, idempotency, refunds, secrets, success-page grants), then lists the problems and fixes them in the codebase. Ships a no-dependency crawler script (audit_site.py) that produces a pass/warn/fail report. Use when the user says they are about to launch, ship, go live, submit to Product Hunt or AI directories, or asks "is my site ready", "SEO check", "why is my site not indexed", or wants a launch checklist, or asks whether their payment or webhook setup is safe.
license: MIT
metadata:
  version: "0.2.0"
  author: GetPaid Skills
---

# launch-checklist

Run the automated audit, fix what fails in the code, re-run until clean, then walk through the
manual items the script cannot see. Report to the user what you changed and what still needs them.

## Step 1 — Run the audit

Against the production URL if it exists, otherwise a local production build
(`npm run build && npm start`, not the dev server — dev servers add scripts and skip caching):

```bash
python3 scripts/audit_site.py https://example.com            # text report
python3 scripts/audit_site.py http://localhost:3000 --max-pages 30 --json > audit.json
```

What it checks (details in `references/checks.md`):
- Per page: `<title>` (10–60 chars), meta description (50–160), exactly one `<h1>`, `<html lang>`,
  viewport, canonical (absolute, same host), og:title/description/image, twitter:card,
  `<img>` without `alt`, HTML size, response time, `noindex` on pages you probably want indexed,
  duplicate titles/descriptions across pages.
- Site: `/robots.txt` exists and does not `Disallow: /` everything, references a sitemap;
  `/sitemap.xml` (or the one named in robots) parses and its URLs return 200 on the same host;
  favicon reachable; apple-touch-icon; a random URL returns **404** (not 200 or a redirect to home);
  http→https redirect (for https sites); links to privacy policy / terms (and refund policy if
  the site sells something); `/llms.txt` presence (informational only).

Exit code 1 when any FAIL. Pages crawled: start URL + same-host links, up to `--max-pages` (default 20).

## Step 2 — Fix in the codebase

Detect the framework and use the matching recipe. For Next.js App Router,
`references/fixes-nextjs.md` has drop-in `robots.ts`, `sitemap.ts`, `not-found.tsx`, `metadata`,
icon conventions. Generic HTML/other frameworks: `references/fixes-generic.md`.

Rules:
- Fix the root cause (shared layout / metadata helper), not page by page, when the issue repeats.
- Never add `noindex` or block crawlers without asking.
- Missing legal pages: generate them with the `legal-pages` skill if installed; otherwise tell the
  user — do not invent legal text inline.
- Missing OG images: use the `og-image-kit` skill if installed.

## Step 3 — Re-run until no FAIL

Re-run the same command. WARN items: fix the cheap ones, list the rest for the user.

## Step 4 — Manual items (script cannot verify)

Go through `references/manual-checklist.md` with the user — analytics installed, error tracking,
transactional email deliverability (SPF/DKIM/DMARC), payment flow tested end-to-end with a real
small payment, backups, uptime monitor, Search Console / Bing Webmaster verification and sitemap
submission, status of the domain's renewal. Mark each as done / not applicable / user to do.

## Step 4b — Payment self-check (if the site takes money)

```bash
python3 scripts/payment_check.py --src . --provider creem          # code scan
python3 scripts/payment_check.py --url http://localhost:3000        # probes a running build
python3 scripts/payment_check.py --url http://localhost:3000 --secret "$CREEM_WEBHOOK_SECRET"  # test-mode secret only
```
FAILs: webhook accepts unsigned or forged requests, parses JSON before verifying, no dedupe on
event id, success page grants access, payment secrets in `NEXT_PUBLIC_*` or committed, webhook
redirects or sits behind a bot challenge. Fix them, re-run, then do the manual card tests in
`references/payment-checks.md` (success card, decline card, refund, dashboard resend, cancel).
Never pass a live webhook secret. `scripts/test_payment_check.py` is the script's own test.

## Report format

```
Launch audit for <url> — <date>
FAIL fixed: …   (file:line changed)
WARN fixed: …
Still open (needs you): …
Manual checklist: x/y done
```
