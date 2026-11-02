---
name: agents-md-starter
description: Creates or upgrades a repository's AGENTS.md (read by Codex, Cursor, and other agents) and a CLAUDE.md that imports it, so Claude Code, Codex, Cursor and Gemini CLI share one set of project rules. Scans the repo to detect languages, package manager, real build/test/lint commands, framework, directory layout and existing rule files (.cursorrules, .cursor/rules, CLAUDE.md, copilot-instructions), then writes a concise, verified rules file. Use when the user asks to set up AGENTS.md or CLAUDE.md, "project rules", "make Claude Code and Codex follow the same conventions", onboard an agent to a repo, or migrate .cursorrules.
license: MIT
metadata:
  version: "0.1.0"
  author: GetPaid Skills
---

# agents-md-starter

Output: `AGENTS.md` at the repo root as the single source of truth, plus `CLAUDE.md` containing
`@AGENTS.md` (Claude Code reads CLAUDE.md and supports `@path` imports). Every command in the file
must have been **run successfully** or be clearly marked as unverified.

## Step 1 — Scan

```bash
python3 scripts/scan_repo.py /path/to/repo            # human summary
python3 scripts/scan_repo.py /path/to/repo --json     # facts as JSON
python3 scripts/scan_repo.py /path/to/repo --draft > AGENTS.draft.md   # filled template
```
It detects: languages by file count, package manager from lockfiles, scripts in `package.json`,
`Makefile` targets, `pyproject.toml` tools (pytest, ruff, mypy, uv/poetry), Go/Rust/Java build files,
frameworks (Next.js, Astro, Vite, Django, FastAPI, Rails…), monorepo workspaces, CI workflows, env
example files, and existing agent rule files. It never executes repo code.

## Step 2 — Read before writing

- Read every existing rule file it found (`CLAUDE.md`, `.cursorrules`, `.cursor/rules/*.mdc`,
  `.github/copilot-instructions.md`, `GEMINI.md`, `CONTRIBUTING.md`). Keep their real rules;
  merge, de-duplicate, drop the generic ones ("write clean code").
- Read the CI workflow: the commands CI runs are the most reliable definition of "tests pass".
- Skim 2–3 representative source files to capture actual conventions (naming, error handling,
  import style) — do not invent conventions the code does not follow.

## Step 3 — Verify commands

Run install/build/test/lint commands from the draft (in a safe way: no deploy, no migrations against
real databases, no publishing). For each: keep it if it works; fix it if the right variant is obvious;
otherwise mark `(unverified)` and tell the user. Note how long the test suite takes if slow.

## Step 4 — Write AGENTS.md

Start from `assets/AGENTS.template.md`. Rules for good content:
- **Short.** Aim for under ~150 lines. Agents read this on every task; every line costs context.
- **Specific and checkable**: "Run `pnpm test --filter web` before committing" beats "test your code".
- Put the commands first. Then layout, conventions, gotchas, and "do not" rules.
- Record the non-obvious: generated files not to edit, env vars needed for tests, the one slow
  test to skip locally, where secrets must never go.
- Monorepos: root AGENTS.md for shared rules + nested `packages/x/AGENTS.md` for package-specific
  commands (agents that support it read the nearest file).

## Step 5 — Wire up the other tools

- **Claude Code**: create `CLAUDE.md` from `assets/CLAUDE.template.md` (it contains `@AGENTS.md`).
  If a CLAUDE.md already exists, move its rules into AGENTS.md and leave Claude-only notes below the import.
- **Codex**: reads `AGENTS.md` natively — nothing else needed.
- **Cursor**: reads `AGENTS.md` at the root; migrate `.cursorrules` content into AGENTS.md and,
  after the user agrees, delete `.cursorrules` (deprecated). Keep `.cursor/rules/*.mdc` only for
  glob-scoped rules.
- **Gemini CLI**: reads `GEMINI.md` by default; set `"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}`
  in `.gemini/settings.json` or create a one-line GEMINI.md pointing to AGENTS.md. Check the
  installed version's docs if this key has moved.
- Symlinks (`ln -s AGENTS.md CLAUDE.md`) also work but break on Windows checkouts without
  `core.symlinks`; the import approach is safer.

See `references/tool-support.md` for the file each tool reads.

## Step 6 — Report

List: files created/changed, commands verified (with result), commands marked unverified, rules
dropped as duplicates or generic, and anything you need the user to decide (e.g. delete `.cursorrules`?).
Do not commit unless the user asked.
