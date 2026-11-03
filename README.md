# GetPaid Skills — free launch skills for coding agents

Five free, MIT-licensed [Agent Skills](https://agentskills.io) (`SKILL.md` format) that help your
coding agent get a site ready to launch. They work in **Claude Code**, **Codex** and **Cursor**
(and other agents that read `SKILL.md` folders). No signup, no API key.

![Installing launch-checklist into Claude Code, then checking a live site's share-card tags with og-image-kit](assets/demo.gif)

| Skill | What it does |
| --- | --- |
| [`launch-checklist`](skills/launch-checklist) | Pre-launch audit. A no-dependency Python crawler reports pass/warn/fail for titles and descriptions, canonical, Open Graph/Twitter tags, robots.txt, sitemap.xml, real 404 status, HTTPS redirect, favicon, legal-page links, image alt text, page weight and response time. A second script checks payment webhooks (signature on the raw body, idempotency, refunds, secrets in client code). The agent then fixes the failures and re-runs until clean. |
| [`legal-pages`](skills/legal-pages) | Drafts a Privacy Policy, Terms of Service and Refund Policy from a short questionnaire, adapted to your payment provider (Creem, Paddle, Lemon Squeezy, Stripe) and your users' regions, and renders them as Markdown, HTML or Next.js pages. A starting template, **not legal advice**. |
| [`og-image-kit`](skills/og-image-kit) | Generates 1200×630 share images for every page (Next.js `opengraph-image.tsx`, Astro, or a Pillow script for static sites), wires up `og:*` / `twitter:*` tags, and verifies them with `check_og.py`. |
| [`agents-md-starter`](skills/agents-md-starter) | Scans a repo for its languages, package manager and real build/test/lint commands, then writes an `AGENTS.md` plus a `CLAUDE.md` that imports it, so Claude Code, Codex and Cursor follow one set of project rules. |
| [`directory-launch-kit`](skills/directory-launch-kit) | Launch copy, images and a tracker for 26 directories (Product Hunt, Show HN, BetaList, There's An AI For That, Uneed, SaaSHub, Peerlist, V2EX and more). `make_kit.py` writes per-directory copy with character counts against each site's limits (it stops instead of truncating) and resizes your real screenshots to each required size; `check_directories.py` re-checks submit pages and observed prices before you pay; `check_listing.py` confirms live listings link back and whether the link is nofollow. Never submits, pays or upvotes for you. |

Scripts need Python 3.9+ and only the standard library, except `og-image-kit/scripts/generate_og.py`,
which needs Pillow (`pip install pillow`).

## Install

### Any agent: `npx skills add`

```bash
npx skills add getpaidskills/skills                            # pick skills and agents interactively
npx skills add getpaidskills/skills --skill launch-checklist   # just one skill
```

Uses the open [`skills` CLI](https://github.com/vercel-labs/skills), which installs into the right
folder for Claude Code, Codex, Cursor and many other agents.

### Claude Code plugin

```text
/plugin marketplace add getpaidskills/skills
/plugin install launch-kit@getpaidskills
```

Plugin skills are namespaced, e.g. `/launch-kit:launch-checklist`. Claude also picks them up
automatically when your request matches (for example "is my site ready to launch?").

### Manual copy

```bash
git clone https://github.com/getpaidskills/skills.git getpaidskills-skills
cp -r getpaidskills-skills/skills/* ~/.claude/skills/    # Claude Code
cp -r getpaidskills-skills/skills/* ~/.agents/skills/    # Codex (older versions: ~/.codex/skills/)
cp -r getpaidskills-skills/skills/* ~/.cursor/skills/    # Cursor
```

Create the target folder first if it doesn't exist. For a single project, copy into
`.claude/skills/`, `.agents/skills/` or `.cursor/skills/` inside the repo instead.

## Use

Ask your agent in plain words:

- "Is my site ready to launch? Audit https://example.com and fix what fails."
- "Write a privacy policy, terms and refund policy for this app."
- "Add OG share images to every page and check the link previews."
- "Set up AGENTS.md for this repo."
- "Prepare launch directory submissions for my product and tell me where to submit first."

Or run the scripts yourself:

```bash
python3 skills/launch-checklist/scripts/audit_site.py https://example.com
python3 skills/launch-checklist/scripts/payment_check.py --src . --provider creem
python3 skills/og-image-kit/scripts/check_og.py https://example.com/
python3 skills/agents-md-starter/scripts/scan_repo.py .
```

Known limits: the crawler reads server-rendered HTML only, so tags injected by client-side
JavaScript are not seen. `legal-pages` output must be reviewed by you and a qualified lawyer.

## Feedback

False positive, broken script, or a check you wish existed?
[Open an issue](https://github.com/getpaidskills/skills/issues) — reports with the command you ran
and its output are the most useful. Email: support@getpaidskills.com.

## License

[MIT](LICENSE) © 2026 GetPaid Skills

---

Also from us: paid skills for taking payments with Creem and Paddle (checkout, webhooks,
entitlements, license keys) at [getpaidskills.com](https://getpaidskills.com/?utm_source=github&utm_medium=readme).
