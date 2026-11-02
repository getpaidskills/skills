# AGENTS.md

<!-- One-paragraph orientation: what this repo is, who uses it, what matters most. -->
{{SUMMARY}}

## Commands

Run from the repo root unless noted. All verified on {{DATE}}.

| Task | Command |
|---|---|
| Install | `{{INSTALL}}` |
| Dev server | `{{DEV}}` |
| Build | `{{BUILD}}` |
| Test (all) | `{{TEST}}` |
| Test (one file) | `{{TEST_ONE}}` |
| Lint / format | `{{LINT}}` |
| Type check | `{{TYPECHECK}}` |

Before finishing a task: run lint, type check and the tests related to what you changed.

## Project layout

{{LAYOUT}}

## Conventions

- Language/framework: {{STACK}}
- <!-- naming, file placement, error handling, logging, i18n — only what the code actually does -->
- Prefer small, focused changes; match the style of surrounding code.
- Add or update tests for behaviour changes.

## Environment

- Copy `{{ENV_EXAMPLE}}` to `.env` (or `.env.local`) for local development. Never commit real secrets.
- <!-- services needed locally (DB, Redis), how to start them -->

## Do not

- Do not edit generated files: <!-- e.g. src/gen/, migrations already applied, lockfiles by hand -->
- Do not run deploy, publish or production migration commands.
- Do not add new dependencies without saying why in the summary.

## Gotchas

- <!-- the things a new contributor trips over -->
