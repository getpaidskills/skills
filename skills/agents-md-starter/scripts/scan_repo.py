#!/usr/bin/env python3
"""Scan a repository and report facts useful for writing AGENTS.md. Never executes repo code.

Usage:
  python3 scan_repo.py [REPO_DIR] [--json | --draft]

--json   machine-readable facts
--draft  print a filled AGENTS.md draft (commands still need to be verified by running them)
Standard library only (Python 3.11+ for tomllib; falls back to regex on older versions).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

IGNORE_DIRS = {".git", "node_modules", ".next", "dist", "build", "out", ".venv", "venv", "env",
               "__pycache__", ".turbo", ".cache", "target", "vendor", ".idea", ".vscode", "coverage",
               ".pytest_cache", ".mypy_cache", ".ruff_cache", ".svelte-kit", ".astro", ".output", ".nuxt"}
EXT_LANG = {".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
            ".mjs": "JavaScript", ".cjs": "JavaScript", ".py": "Python", ".go": "Go", ".rs": "Rust",
            ".java": "Java", ".kt": "Kotlin", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
            ".cs": "C#", ".cpp": "C++", ".c": "C", ".vue": "Vue", ".svelte": "Svelte",
            ".astro": "Astro", ".dart": "Dart", ".ex": "Elixir", ".sql": "SQL"}
RULE_FILES = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules", ".windsurfrules",
              ".github/copilot-instructions.md", "CONTRIBUTING.md", ".clinerules"]
LOCKS = [("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"), ("bun.lock", "bun"),
         ("package-lock.json", "npm"), ("uv.lock", "uv"), ("poetry.lock", "poetry"),
         ("Pipfile.lock", "pipenv"), ("requirements.txt", "pip"), ("Cargo.lock", "cargo"),
         ("go.sum", "go"), ("Gemfile.lock", "bundler"), ("composer.lock", "composer")]
JS_FRAMEWORKS = [("next", "Next.js"), ("astro", "Astro"), ("@remix-run/react", "Remix"),
                 ("@sveltejs/kit", "SvelteKit"), ("nuxt", "Nuxt"), ("vite", "Vite"), ("react", "React"),
                 ("vue", "Vue"), ("svelte", "Svelte"), ("express", "Express"), ("hono", "Hono"),
                 ("fastify", "Fastify"), ("@nestjs/core", "NestJS"), ("electron", "Electron"),
                 ("expo", "Expo"), ("react-native", "React Native"), ("tailwindcss", "Tailwind CSS"),
                 ("drizzle-orm", "Drizzle ORM"), ("prisma", "Prisma"), ("@prisma/client", "Prisma"),
                 ("vitest", "Vitest"), ("jest", "Jest"), ("@playwright/test", "Playwright"),
                 ("cypress", "Cypress"), ("eslint", "ESLint"), ("@biomejs/biome", "Biome"),
                 ("prettier", "Prettier"), ("typescript", "TypeScript")]
PY_FRAMEWORKS = ["django", "fastapi", "flask", "pytest", "ruff", "mypy", "black", "sqlalchemy",
                 "pydantic", "celery", "streamlit"]


def read(path, limit=200_000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return None


def walk(root, max_files=50_000):
    langs, n = Counter(), 0
    top_dirs = Counter()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")
                       or d in (".github", ".cursor", ".claude", ".agents", ".gemini")]
        rel = os.path.relpath(dirpath, root)
        for fn in filenames:
            n += 1
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXT_LANG:
                langs[EXT_LANG[ext]] += 1
                top = rel.split(os.sep)[0] if rel != "." else "."
                top_dirs[top] += 1
            if n >= max_files:
                return langs, top_dirs, True
    return langs, top_dirs, False


def pm_run(pm, script):
    if pm == "npm":
        return "npm test" if script == "test" else f"npm run {script}"
    if pm in ("pnpm", "yarn", "bun"):
        return f"{pm} {script}" if pm != "bun" else f"bun run {script}"
    return f"npm run {script}"


def scan(root):
    root = os.path.abspath(root)
    facts = {"root": root, "name": os.path.basename(root)}
    langs, top_dirs, truncated = walk(root)
    facts["languages"] = dict(langs.most_common(8))
    facts["source_dirs"] = dict(top_dirs.most_common(10))
    facts["walk_truncated"] = truncated
    facts["package_managers"] = [pm for f, pm in LOCKS if os.path.exists(os.path.join(root, f))]
    facts["existing_rule_files"] = [f for f in RULE_FILES if os.path.exists(os.path.join(root, f))]
    cursor_rules = os.path.join(root, ".cursor", "rules")
    if os.path.isdir(cursor_rules):
        facts["existing_rule_files"] += [f".cursor/rules/{f}" for f in sorted(os.listdir(cursor_rules))]
    facts["env_examples"] = [f for f in (".env.example", ".env.sample", ".env.local.example", ".env.template")
                             if os.path.exists(os.path.join(root, f))]
    wf = os.path.join(root, ".github", "workflows")
    facts["ci"] = []
    ci_cmds = []
    if os.path.isdir(wf):
        for f in sorted(os.listdir(wf)):
            facts["ci"].append(f".github/workflows/{f}")
            txt = read(os.path.join(wf, f)) or ""
            ci_cmds += [m.strip() for m in re.findall(r"^\s*-?\s*run:\s*(.+)$", txt, re.M) if not m.strip().startswith("|")]
    facts["ci_run_commands"] = ci_cmds[:20]
    for f in ("Dockerfile", "docker-compose.yml", "compose.yaml", "docker-compose.yaml", "Procfile",
              "vercel.json", "wrangler.toml", "wrangler.jsonc", "netlify.toml", "fly.toml"):
        if os.path.exists(os.path.join(root, f)):
            facts.setdefault("deploy_files", []).append(f)

    # --- JS ---
    pkg_txt = read(os.path.join(root, "package.json"))
    if pkg_txt:
        try:
            pkg = json.loads(pkg_txt)
        except json.JSONDecodeError:
            pkg = {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        facts["node"] = {
            "scripts": pkg.get("scripts", {}),
            "frameworks": sorted({label for dep, label in JS_FRAMEWORKS if dep in deps}),
            "workspaces": pkg.get("workspaces") or (["(pnpm-workspace.yaml)"] if os.path.exists(os.path.join(root, "pnpm-workspace.yaml")) else None),
            "engines": pkg.get("engines"),
            "type": pkg.get("type"),
            "package_manager_field": pkg.get("packageManager"),
        }
    # --- Python ---
    pyproject = read(os.path.join(root, "pyproject.toml"))
    if pyproject is not None:
        py = {"tools": []}
        data = {}
        if tomllib:
            try:
                data = tomllib.loads(pyproject)
            except Exception:  # noqa: BLE001
                data = {}
        tool = data.get("tool", {}) if data else {}
        py["tools"] = sorted(tool.keys()) if tool else sorted(set(re.findall(r"^\[tool\.([\w-]+)", pyproject, re.M)))
        text = pyproject.lower()
        py["libraries"] = [f for f in PY_FRAMEWORKS if re.search(rf"\b{f}\b", text)]
        py["requires_python"] = (data.get("project", {}) or {}).get("requires-python") if data else None
        facts["python"] = py
    elif os.path.exists(os.path.join(root, "requirements.txt")):
        req = (read(os.path.join(root, "requirements.txt")) or "").lower()
        facts["python"] = {"tools": [], "libraries": [f for f in PY_FRAMEWORKS if re.search(rf"^{f}\b", req, re.M)]}
    if os.path.exists(os.path.join(root, "manage.py")):
        facts.setdefault("python", {"tools": [], "libraries": []})["django_manage"] = True
    # --- Make ---
    mk = read(os.path.join(root, "Makefile"))
    if mk:
        facts["make_targets"] = [t for t in re.findall(r"^([A-Za-z][\w.-]*):(?!=)", mk, re.M) if t != "PHONY"][:30]
    # --- Others ---
    if os.path.exists(os.path.join(root, "go.mod")):
        m = re.search(r"^module\s+(\S+)", read(os.path.join(root, "go.mod")) or "", re.M)
        facts["go"] = {"module": m.group(1) if m else None}
    if os.path.exists(os.path.join(root, "Cargo.toml")):
        facts["rust"] = {"workspace": "[workspace]" in (read(os.path.join(root, "Cargo.toml")) or "")}
    facts["commands"] = guess_commands(facts)
    return facts


def guess_commands(f):
    c = {}
    pms = f["package_managers"]
    node = f.get("node")
    if node:
        pm = next((p for p in pms if p in ("pnpm", "yarn", "bun", "npm")), "npm")
        if node.get("package_manager_field"):
            pm = node["package_manager_field"].split("@")[0]
        c["install"] = {"npm": "npm ci" if "npm" in pms else "npm install", "pnpm": "pnpm install",
                        "yarn": "yarn install", "bun": "bun install"}.get(pm, "npm install")
        s = node["scripts"]
        for key, names in {"dev": ["dev", "start:dev", "serve"], "build": ["build"],
                           "test": ["test", "test:unit"], "lint": ["lint", "check"],
                           "typecheck": ["typecheck", "type-check", "tsc", "check-types"],
                           "format": ["format", "fmt"], "e2e": ["test:e2e", "e2e"]}.items():
            n = next((x for x in names if x in s), None)
            if n:
                c[key] = pm_run(pm, n)
        if "typecheck" not in c and "TypeScript" in node["frameworks"]:
            c["typecheck"] = "npx tsc --noEmit"
        fw = node["frameworks"]
        if "Vitest" in fw:
            c["test_one"] = (c.get("test", "npx vitest run") + " -- path/to/file.test.ts").replace("npm test --", "npx vitest run")
        elif "Jest" in fw:
            c["test_one"] = "npx jest path/to/file.test.ts"
    py = f.get("python")
    if py:
        pm = "uv" if "uv" in pms else "poetry" if "poetry" in pms else "pip"
        pre = {"uv": "uv run ", "poetry": "poetry run ", "pip": ""}[pm]
        c.setdefault("install", {"uv": "uv sync", "poetry": "poetry install", "pip": "pip install -r requirements.txt"}[pm])
        if "pytest" in py.get("libraries", []) or "pytest" in py.get("tools", []):
            c.setdefault("test", f"{pre}pytest")
            c.setdefault("test_one", f"{pre}pytest path/to/test_file.py -q")
        elif py.get("django_manage"):
            c.setdefault("test", f"{pre}python manage.py test")
        if "ruff" in py.get("tools", []) or "ruff" in py.get("libraries", []):
            c.setdefault("lint", f"{pre}ruff check . && {pre}ruff format --check .")
        if "mypy" in py.get("tools", []) or "mypy" in py.get("libraries", []):
            c.setdefault("typecheck", f"{pre}mypy .")
        if py.get("django_manage"):
            c.setdefault("dev", f"{pre}python manage.py runserver")
    if "go" in f:
        c.setdefault("build", "go build ./...")
        c.setdefault("test", "go test ./...")
        c.setdefault("lint", "go vet ./...")
    if "rust" in f:
        c.setdefault("build", "cargo build")
        c.setdefault("test", "cargo test")
        c.setdefault("lint", "cargo clippy -- -D warnings && cargo fmt --check")
    for t in f.get("make_targets", []):
        if t in ("test", "lint", "build", "dev", "run", "fmt", "check") and t not in c:
            c[{"run": "dev", "fmt": "format", "check": "lint"}.get(t, t)] = f"make {t}"
    return c


def stack_line(f):
    parts = [", ".join(list(f["languages"])[:3]) or "unknown"]
    if f.get("node"):
        parts.append(", ".join(f["node"]["frameworks"]))
    if f.get("python"):
        parts.append(", ".join(f["python"].get("libraries", [])))
    return "; ".join(p for p in parts if p)


def draft(f):
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "AGENTS.template.md")
    tpl = read(tpl_path) or ""
    c = f["commands"]
    todo = "(unverified - find the right command)"
    layout = "\n".join(f"- `{d}/` — {n} source files" for d, n in f["source_dirs"].items() if d != ".") or "- (flat repository)"
    repl = {
        "SUMMARY": f"<!-- TODO: describe {f['name']} in 2-3 sentences. -->",
        "DATE": dt.date.today().isoformat() + " <!-- update after running each command -->",
        "INSTALL": c.get("install", todo), "DEV": c.get("dev", todo), "BUILD": c.get("build", todo),
        "TEST": c.get("test", todo), "TEST_ONE": c.get("test_one", todo), "LINT": c.get("lint", todo),
        "TYPECHECK": c.get("typecheck", "n/a"), "LAYOUT": layout, "STACK": stack_line(f),
        "ENV_EXAMPLE": (f["env_examples"] or [".env.example (create one)"])[0],
    }
    for k, v in repl.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def human(f):
    out = [f"Repository: {f['root']}"]
    out.append("Languages: " + (", ".join(f"{k} ({v})" for k, v in f["languages"].items()) or "none detected"))
    out.append("Package managers: " + (", ".join(f["package_managers"]) or "none detected"))
    if f.get("node"):
        out.append("JS frameworks/tools: " + (", ".join(f["node"]["frameworks"]) or "-"))
        out.append("package.json scripts: " + (", ".join(f["node"]["scripts"]) or "-"))
        if f["node"].get("workspaces"):
            out.append(f"Workspaces: {f['node']['workspaces']}")
    if f.get("python"):
        out.append(f"Python: tools={f['python'].get('tools')} libs={f['python'].get('libraries')}")
    if f.get("make_targets"):
        out.append("Make targets: " + ", ".join(f["make_targets"]))
    out.append("Existing rule files: " + (", ".join(f["existing_rule_files"]) or "none"))
    out.append("CI workflows: " + (", ".join(f["ci"]) or "none"))
    if f["ci_run_commands"]:
        out.append("CI run steps: " + " | ".join(f["ci_run_commands"][:8]))
    out.append("Env examples: " + (", ".join(f["env_examples"]) or "none"))
    out.append("\nSuggested commands (verify by running them):")
    for k, v in f["commands"].items():
        out.append(f"  {k:10} {v}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", nargs="?", default=".")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--json", action="store_true")
    g.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(a.repo):
        print(f"not a directory: {a.repo}", file=sys.stderr)
        return 2
    f = scan(a.repo)
    if a.json:
        print(json.dumps(f, indent=2, ensure_ascii=False))
    elif a.draft:
        print(draft(f))
    else:
        print(human(f))
    return 0


if __name__ == "__main__":
    sys.exit(main())
