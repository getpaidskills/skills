# Privacy Policy

_Last updated: {{effective_date}}_

This Privacy Policy explains how {{company_name}} ("we", "us") collects, uses and shares personal
data when you use {{product_name}} at {{website_url}} (the "Service").

## Who we are

{{company_name}} ({{legal_entity_type}}), {{address}}. Contact: {{contact_email}}.
{{#serves_eu}}For the purposes of the EU and UK GDPR, we are the controller of the personal data described here, except where a payment provider acts as an independent controller (see "Payments").{{/serves_eu}}

## Data we collect

{{#data_collected}}
- {{.}}
{{/data_collected}}

We do not sell personal data.

## How we use it

- To create and secure your account and provide the Service.
- To deliver what you purchased and give you access to updates.
- To send transactional messages (receipts, download links, security notices). Marketing emails
  only if you opt in; every marketing email has an unsubscribe link.
- To prevent fraud and abuse, and to comply with legal obligations.
- To understand aggregate usage and improve the Service.

{{#serves_eu}}
## Legal bases (EU/UK)

- **Contract** — account, delivery of purchases, support.
- **Legitimate interests** — security, fraud prevention, aggregate analytics, product improvement.
- **Consent** — marketing emails{{#analytics_cookies}} and analytics cookies{{/analytics_cookies}}; you can withdraw consent at any time.
- **Legal obligation** — tax and accounting records.
{{/serves_eu}}

## Payments

{{#mor}}
Purchases are processed by {{mor_name}} ({{mor_url}}), which acts as the Merchant of Record and
reseller of the Service. {{mor_name}} collects your payment details, billing address and tax
information and processes them under its own privacy policy ({{mor_privacy_url}}). We receive
limited order information (such as your email, country, product and order ID) but never your full
card details.
{{/mor}}
{{^mor}}
Payments are processed by our payment processor. Card details are entered directly with the
processor and are not stored on our servers. [[TODO: name the processor and link its privacy policy]]
{{/mor}}

## Service providers

We share personal data only with providers that help us run the Service, under contracts that
limit their use of the data:

{{#processors}}
- **{{name}}** — {{purpose}} ({{location}})
{{/processors}}

{{#serves_eu}}
Some of these providers are located outside the EU/UK. Where that is the case we rely on adequacy
decisions or Standard Contractual Clauses. [[TODO: confirm the transfer mechanism for each provider]]
{{/serves_eu}}

## Cookies

{{#uses_cookies}}
We use strictly necessary cookies to keep you signed in and to secure forms.
{{#analytics_cookies}}With your consent we also use analytics cookies from {{analytics_provider}}. You can change your choice at any time via the cookie settings link in the footer.{{/analytics_cookies}}
{{^analytics_cookies}}We do not use advertising or cross-site tracking cookies.{{/analytics_cookies}}
{{/uses_cookies}}
{{^uses_cookies}}
We do not use cookies other than those strictly necessary for the Service to function.
{{/uses_cookies}}

## Retention

- Account data: while your account is open, and deleted within a reasonable period after you ask
  us to close it.
- Order and invoice records: as long as tax and accounting laws require.
- Server logs: up to {{retention_days_logs}} days.

## Your rights

You can ask us to access, correct, export or delete your personal data by emailing
{{contact_email}}. We will answer within the time limits required by applicable law.
{{#serves_eu}}
If you are in the EU or UK you also have the right to object to or restrict processing and to
lodge a complaint with your local data protection authority.
{{/serves_eu}}
{{#serves_california}}
**California residents.** Under the CCPA/CPRA you have the right to know, delete and correct
personal information and to opt out of its "sale" or "sharing". We do not sell or share personal
information as those terms are defined by the CCPA, and we will not discriminate against you for
exercising your rights.
{{/serves_california}}
{{#serves_china}}
**Users in mainland China.** We process personal information in accordance with the Personal
Information Protection Law (PIPL). Your data may be transferred to and stored outside mainland
China by the providers listed above. [[TODO: confirm the cross-border transfer basis and consent flow with a lawyer]]
{{/serves_china}}

## Children

The Service is not directed to children under {{min_age}}, and we do not knowingly collect their
personal data.

## Security

We use reasonable technical and organisational measures (encryption in transit, access controls,
least-privilege access to production systems). No method of transmission or storage is 100% secure.

## Changes

We will post any changes on this page and update the date above. If changes are material we will
notify you by email or in the Service.

## Contact

{{contact_email}}
