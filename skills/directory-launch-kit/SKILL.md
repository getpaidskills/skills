---
name: directory-launch-kit
description: Prepares a product for submission to launch platforms and directories (Product Hunt, Show HN, BetaList, Uneed, Fazier, SaaSHub, TinyLaunch, AI tool directories, agent-skill marketplaces, Reddit, V2EX and more) without submitting anything itself. Picks only the directories the product fits, writes the copy for each form within its field limits from one product.json, resizes screenshots to each platform's sizes (Product Hunt 1270x760 gallery and 240x240 thumbnail, 1200x630 OG), builds a tracker CSV, re-checks prices and rules on the live pages, and later verifies which listings went live and whether their backlinks are follow or nofollow. Use when the user asks where to launch, how to submit to Product Hunt or AI directories, wants launch copy, a directory list, backlinks, or a launch tracker.
license: MIT
metadata:
  version: "0.1.0"
  author: GetPaid Skills
---

# directory-launch-kit

Goal: the user gets a short, honest list of directories that fit their product, ready-to-paste copy
for each form, correctly sized images, and a tracker, and **they** do every submission and payment.
This skill never creates accounts, submits forms, pays, upvotes or posts on the user's behalf.

## Step 1 — Read the product, don't invent it

Collect, from the repo and the live site (ask only for what is missing):

| Field | Where to find it |
|---|---|
| name, url (live `https://`, own domain) | site metadata, `package.json`, README |
| tagline (≤ 60 chars) and description (≤ 500) | the home page hero and meta description |
| pricing | the pricing page, exactly as written |
| ai / open_source / developer_tool / agent_skills | what the product actually is |
| competitors | ask the user (SaaSHub needs them) |
| maker_comment | **the user's own words**: draft it with them, never post it for them |
| logo + 2–5 real screenshots | `public/`, or capture the live site (Step 3) |

Write it to `product.json` using `assets/product.example.json` as the shape. Copy rules are in
`references/copy-guide.md`. Never add numbers, testimonials, user counts or "#1" claims the user can't
prove; directories reject them and readers stop trusting the page.

## Step 2 — Re-check the directory data

```bash
python3 scripts/check_directories.py            # OK / CHANGED / BLOCKED / DOWN per directory
```
`references/directories.json` records each directory's submit URL, observed cost, rules and the date
it was read. Before you quote any price, open that directory's page (browser if BLOCKED or CHANGED)
and say the date you read it. Update the JSON when something changed.

## Step 3 — Real screenshots

Use screenshots of the real product, not mockups. If the site is live, capture it:
```bash
npx playwright screenshot --viewport-size=1440,900 https://example.com shot-1.png
npx playwright screenshot --viewport-size=1440,900 https://example.com/pricing shot-2.png
```
(or any browser at 1440×900). Show the product doing its job: the main screen, a result, pricing.
Sizes per platform: `references/assets.md`.

## Step 4 — Build the kit

```bash
python3 scripts/make_kit.py --product product.json --out launch-kit
```
Writes:
- `launch-kit/copy.md`: one section per directory: submit URL, observed cost and date, rules, each
  form field with `n/limit`, the maker comment. Fields over a limit are flagged `OVER LIMIT` and the
  script exits 1: shorten the text in `product.json` with the user and re-run. It never truncates.
- `launch-kit/tracker.csv`: id, directory, submit_url, cost_observed, checked, backlink_required,
  status, submitted_on, listing_url, link_rel, notes. Re-running keeps statuses already recorded.
- `launch-kit/images/`: `ph-thumbnail-240.png`, `logo-512.png`, `og-1200x630.png`,
  `gallery-N-1270x760.png`, `screenshot-N-1920x1080.png`, letterboxed (never cropped), each < 3 MB.

Directories the product doesn't fit are skipped with the reason (AI-only directories for non-AI
products, OpenAlternative for closed source, DevHunt for non-dev tools, agent-skill marketplaces
unless `agent_skills: true`). Show HN gets a warning if trying the product needs a signup.

## Step 5 — Order the submissions (no dates, just order)

1. Free directories with long review queues first (Fazier free, Dang.ai free, SaaSHub, Launching
   Next, Uneed free): their queues run while you finish the rest.
2. Communities where the user must be present to answer (Show HN, Indie Hackers, Reddit, V2EX): one
   at a time, only when the user can reply to comments for the next hours.
3. Product Hunt: a draft first, launch when the user can stay on it all day.
4. Paid upgrades only if the user decides the price is worth it; list them with the observed price
   and date and let the user choose. Never pay or enter a card.

Directories that require a backlink (marked in `copy.md`): tell the user exactly which badge/link
the directory wants and where it will appear on their site, and add it only if they agree.

## Step 6 — Track what went live

After the user submits, they paste each listing URL into `tracker.csv`. Then:
```bash
python3 scripts/check_listing.py --tracker launch-kit/tracker.csv --domain example.com --write
```
marks rows `live` (with `follow` / `nofollow`), `no-link` or `error`.

## Rules

- Never submit, sign up, pay, upvote, comment or post for the user. Draft; they act.
- BetaList offers an official agent API that only drafts (betalist.com/agent): you may create the
  draft **only if the user asks**, then hand them the claim link; they review, pay and publish.
- SaaSHub explicitly asks AI agents to let the human submit: don't automate it.
- No vote rings, no "please upvote" messages, no fake accounts. Product Hunt and HN penalise them.
- Quote prices only as "observed on <date> at <url>".

## Files

- `scripts/make_kit.py`: product.json → copy.md, tracker.csv, images/
- `scripts/check_directories.py`: live re-check of every directory page and recorded price
- `scripts/check_listing.py`: confirm listings link to you, follow vs nofollow
- `scripts/test_kit.py`: self-test (offline)
- `references/directories.json`: the data (26 directories, checked 2026-11-03)
- `references/directories.md`: the same as a readable table
- `references/copy-guide.md`: taglines, descriptions, Show HN titles, the maker comment
- `references/assets.md`: image sizes per platform and how to capture them

## Done when

- [ ] `product.json` contains only facts from the product and the user's own words
- [ ] `check_directories.py` was run and CHANGED/BLOCKED rows were read by hand
- [ ] `make_kit.py` exits 0 (no OVER LIMIT fields) and the images were opened and look right
- [ ] The user has `copy.md`, `tracker.csv` and `images/`, and knows the order to submit in
