# Manual launch checklist (things a crawler cannot see)

Mark each: ✅ done · ➖ not applicable · 🙋 user must do.

## Money
- [ ] Payment flow tested end-to-end in **live** mode with a real small payment, then refunded
- [ ] Webhook endpoint registered in live mode, signature verified, idempotent
- [ ] Receipt / license / download email arrives (check spam folder)
- [ ] Prices, currency and tax display match the provider's checkout
- [ ] Refund policy matches what the payment provider allows

## Accounts & data
- [ ] Sign-up, login, password reset / magic link work on a fresh browser
- [ ] Database backups scheduled and one restore tested
- [ ] Secrets only in env vars; `.env` not committed; production keys ≠ test keys
- [ ] Account deletion / data export path exists (GDPR requests)

## Email deliverability
- [ ] SPF, DKIM, DMARC records set for the sending domain
- [ ] From-address is a real monitored inbox or has a reply-to

## Monitoring
- [ ] Error tracking (e.g. Sentry) receives a test error from production
- [ ] Uptime monitor on home page and a health endpoint
- [ ] Analytics installed, respects the cookie/consent requirements of your audience

## Search & discovery
- [ ] Google Search Console and Bing Webmaster Tools verified; sitemap submitted
- [ ] Social preview checked in LinkedIn Post Inspector / Facebook Sharing Debugger
- [ ] `llms.txt` (optional) describes the product for AI assistants

## Domain & infra
- [ ] Domain auto-renew on, registrar account has 2FA
- [ ] TLS certificate auto-renews (Let's Encrypt / host-managed)
- [ ] `www` ↔ apex redirect chosen and consistent with canonical URLs
- [ ] Rate limiting on auth and webhook endpoints

## Support
- [ ] Contact email / support link visible in footer
- [ ] Status of "who maintains this" and response-time expectations written down
