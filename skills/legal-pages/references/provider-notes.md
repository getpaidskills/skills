# Payment-provider notes for legal pages

Providers change their review rules; check the linked pages at the time of setup. Items marked
"verify" were not confirmed against the provider's current documentation when this skill was written.

## Merchant of Record (MoR) — general

With a MoR (Creem, Paddle, Lemon Squeezy) the provider is the legal seller to the customer: it
charges, issues invoices, collects VAT/sales tax and handles chargebacks. Consequences for your pages:
- Terms must say the MoR processes orders and that its buyer terms apply (the template does this).
- The privacy policy should name the MoR as a recipient/independent controller of payment data.
- Your refund policy must not contradict the MoR's buyer terms. If the MoR's buyer terms give
  customers a refund right, your "no refunds" line does not remove it.
- Providers typically review your website (pricing, terms, privacy, refund policy, contact info)
  before enabling live payments. Have the three pages live and linked in the footer first.

## Creem
- Site: https://www.creem.io — privacy https://www.creem.io/privacy, buyer terms
  https://www.creem.io/buyer-terms, merchant terms https://www.creem.io/terms
- Docs: https://docs.creem.io — check the account review / acceptable products pages (verify).

## Paddle
- Privacy https://www.paddle.com/legal/privacy, buyer terms
  https://www.paddle.com/legal/checkout-buyer-terms
- Paddle runs a domain/website review before live checkout; it looks for terms, privacy and refund
  policy, and that terms name Paddle as the reseller/MoR (verify current wording requirements in
  Paddle's help center).

## Lemon Squeezy
- Privacy https://www.lemonsqueezy.com/privacy, buyer terms https://www.lemonsqueezy.com/buyer-terms
- Store activation includes a review of the website and products (verify).

## Stripe / direct processors (no MoR)
- You are the seller: you are responsible for tax registration and collection (VAT OSS in the EU,
  US state sales tax, etc.), invoices and consumer-law compliance. The templates' `{{^mor}}`
  branch inserts TODOs for the processor name; tax obligations need an accountant, not a template.
