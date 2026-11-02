# Payment self-check

What `scripts/payment_check.py` checks, why, and what it can't see. Written 2026-11-01 for
Creem, Paddle, Stripe, Lemon Squeezy and Polar webhooks.

## Static scan (`--src`)

| Check | FAIL when | Why it matters |
|---|---|---|
| No secrets in the repo | a tracked `.env*` (other than examples) or a live-looking key (`creem_…` without `test_`, `sk_live_…`, `whsec_…`, `pdl_live_…`) | anyone with repo access can charge, refund or forge webhooks; rotate after removing |
| Payment secrets stay on the server | `NEXT_PUBLIC_*SECRET/API_KEY/WEBHOOK` | `NEXT_PUBLIC_` values are inlined into the browser bundle |
| Webhook verifies the signature | no HMAC / verify call in the handler or an imported verifier | without it anyone can POST "payment succeeded" |
| Webhook uses the raw body | `await req.json()` and no `text()`/raw read | the signature is over the exact bytes; re-serialised JSON won't match |
| Webhook is idempotent | no event-id / unique-key / `INSERT OR IGNORE` handling | providers retry on timeouts and you can resend from the dashboard |
| Refunds remove access | WARN when no refund/dispute handling | refunded buyers otherwise keep access |
| Success page does not grant access | a write in a success / thank-you page | that URL can be opened without paying; only the verified webhook grants |

It is a heuristic grep, not a proof: a PASS means the pattern exists, not that it's correct.

## Probes (`--url`)

| Probe | Expect |
|---|---|
| POST to the webhook with no signature | 400/401/403. 2xx = FAIL. 3xx = FAIL (providers don't follow redirects). 404/405 = wrong path. 503 = secret not set |
| POST with a forged signature | 400/401/403 |
| Bot-challenge or WAF page on the webhook | FAIL: exclude the path from WAF, bot protection, rate limits |
| `--secret` (test mode only): signed event for an unknown product, sent twice | 2xx both times, nothing granted, answered in < 5 s |
| POST to the checkout endpoint without a session | not a checkout URL (WARN if guest checkout is intended) |
| Random URL | 404 |

`--secret` signs like Creem (`creem-signature`: hex HMAC-SHA256 of the raw body) or Paddle
(`Paddle-Signature: ts=…;h1=…`, HMAC over `ts:body`). Use a test-mode secret against a local or
staging server. Never run it with a live secret.

## Manual (the script can't do these)

1. Test-mode purchase with the provider's success test card (Creem and Stripe:
   `4111 1111 1111 1111` / `4242 4242 4242 4242`) → access appears within seconds.
2. Decline card (Creem `4507 9900 0000 0028`) → no access, no grant row.
3. Refund that order from the dashboard → access gone.
4. Resend the same webhook from the dashboard → no second grant, no second email.
5. Cancel a subscription → access stays until the period end, then ends.
6. Live mode: webhook registered at the production URL, live keys only in server env, one real
   low-price purchase refunded.

The paid skills `creem-checkout`, `paddle-billing` and `creem-starter` ship code and tests that
pass every item above.
