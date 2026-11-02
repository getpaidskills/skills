# Which file each agent reads

Behaviour as documented by each vendor at the time of writing; vendors change this — check docs
if something does not load.

| Tool | Project rules file | Notes |
|---|---|---|
| OpenAI Codex (CLI/IDE) | `AGENTS.md` (repo root and nested dirs; also `~/.codex/AGENTS.md` global) | Nearest file to the edited path wins for conflicts. |
| Claude Code | `CLAUDE.md` (repo root, nested dirs, `~/.claude/CLAUDE.md`) | Supports `@path/to/file` imports, so `@AGENTS.md` pulls in the shared file. `/memory` shows what loaded. |
| Cursor | `AGENTS.md` at root, `.cursor/rules/*.mdc` | `.cursorrules` is legacy. `.mdc` rules support globs and "always apply". |
| Gemini CLI | `GEMINI.md` by default | Configurable context file name in `.gemini/settings.json`. |
| GitHub Copilot | `.github/copilot-instructions.md`; recent versions also read `AGENTS.md` | Verify for your Copilot surface (VS Code, coding agent). |
| Windsurf / others | various (`.windsurfrules`, `AGENTS.md`) | Many tools now read AGENTS.md — see https://agents.md |

Spec/home page for the AGENTS.md convention: https://agents.md
