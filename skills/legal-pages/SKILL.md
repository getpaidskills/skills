---
name: legal-pages
description: Drafts a Privacy Policy, Terms of Service and Refund Policy for a SaaS, digital product or website from a short questionnaire, adapted to the payment provider (Creem, Paddle, Lemon Squeezy as Merchant of Record, or Stripe/direct) and to where users are (EU/UK GDPR, California CCPA/CPRA, China PIPL notes), then renders them as Markdown, HTML or Next.js pages and links them in the footer. Output is a starting template, NOT legal advice - the user must review it and have it checked by a qualified lawyer. Use when the user needs privacy policy, terms, refund policy, legal pages, or a payment provider (Paddle/Creem/Lemon Squeezy/Stripe) review asks for them.
license: MIT
metadata:
  version: "0.1.0"
  author: GetPaid Skills
---

# legal-pages

> **Not legal advice.** This skill produces templates filled with the user's answers. It does not
> know the user's jurisdiction-specific obligations and is not a substitute for a lawyer. You must
> tell the user this in your final message, and the generated pages carry a review notice that the
> user deletes only after they have reviewed the text. Never claim the pages are "compliant".

## Step 1 — Collect facts (ask, don't guess)

Inspect the codebase first to pre-fill what you can (auth provider, analytics script, payment SDK,
email provider, database host, cookies set). Then confirm with the user. Copy
`assets/legal-config.example.json` to `legal-config.json` in the project root and fill it:

| Field | Example | Where to look |
|---|---|---|
| `company_name`, `product_name`, `website_url`, `contact_email` | "Acme Studio" | ask; footer; env |
| `legal_entity_type`, `address`, `governing_law` | "individual", "Hebei, China", "People's Republic of China" | **ask — never invent** |
| `merchant_of_record` | `creem` / `paddle` / `lemonsqueezy` / `none` | package.json deps (`creem`, `@paddle/paddle-js`, `@lemonsqueezy/...`, `stripe`) |
| `data_collected` | email, name, payment handled by MoR, IP/usage logs | auth + DB schema |
| `processors` | Resend (email), Plausible (analytics), AWS (hosting) | env vars, SDK imports |
| `uses_cookies`, `analytics_cookies` | true / false | cookies set by auth/analytics |
| `sells_subscriptions`, `sells_one_time` | | pricing page |
| `refund_mode` | `window` (N days) / `case_by_case` / `none` | **ask** — must match the provider's rules |
| `serves_eu`, `serves_california`, `serves_china` | | ask; affects added sections |
| `min_age` | 13 or 16 | 16 is the safer default if serving the EU |

Anything the user does not know stays as a `[[TODO: …]]` marker in the output — do not fill legal
facts (address, entity, governing law) with plausible-looking values.

## Step 2 — Render

```bash
python3 scripts/render_legal.py --config legal-config.json --out legal --format md
python3 scripts/render_legal.py --config legal-config.json --out app/(legal) --format nextjs   # Next.js App Router
python3 scripts/render_legal.py --config legal-config.json --out public/legal --format html
```
Produces `privacy`, `terms`, `refund` documents. The script fails if a required field is missing,
prints every remaining `[[TODO]]`, and stamps "Last updated" with `effective_date` (or today).
`--format nextjs` writes `privacy/page.tsx`, `terms/page.tsx`, `refund/page.tsx` with static HTML
and `metadata` — no extra dependencies. Wrap with your site layout/typography as needed.

## Step 3 — Wire up

- Footer links to all three pages on every page (payment providers look for them).
- Checkout: link terms + refund policy near the buy button ("By purchasing you agree to…").
- If `analytics_cookies` is true and `serves_eu` is true: tell the user a cookie consent banner is
  likely needed before loading analytics (or switch to a cookieless analytics tool). Do not add a
  banner silently.
- Sign-up form: link privacy policy.

## Step 4 — Provider-specific checks

Read `references/provider-notes.md` for the chosen Merchant of Record. Key points: with a MoR,
the MoR is the seller of record to the customer, so terms must say so and the refund policy must
not promise something the MoR's own buyer terms contradict.

## Step 5 — Hand-off message (required)

Tell the user, in their language:
1. Which files were created and where they are linked.
2. The list of `[[TODO]]` items still open.
3. That the text is a template, not legal advice, and should be reviewed by a qualified lawyer,
   especially for: governing law, liability limits, consumer withdrawal rights (EU 14-day rule
   for digital content), and data transfers out of the user's country.
4. That they must keep the pages accurate when they add a new tool that processes user data.

## Files

- `assets/templates/*.md` — the three templates (mustache-style `{{field}}`, `{{#flag}}…{{/flag}}`).
- `assets/legal-config.example.json` — questionnaire with every field.
- `scripts/render_legal.py` — renderer (stdlib only).
- `references/provider-notes.md` — Creem / Paddle / Lemon Squeezy / Stripe notes with links.
- `references/regional-notes.md` — GDPR, UK GDPR, CCPA/CPRA, PIPL pointers (informational).
