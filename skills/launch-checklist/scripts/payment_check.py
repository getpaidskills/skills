#!/usr/bin/env python3
"""Payment self-check before launch. No dependencies (Python 3.9+).

Two parts, run either or both:

  --src DIR      static scan of the codebase (webhook verification, raw body, idempotency,
                 secrets in client bundles, live keys committed, access granted on the success page)
  --url ORIGIN   black-box probes against a running site (webhook rejects unsigned and
                 tampered requests, no redirect on the webhook, checkout needs a login,
                 random URL is not a 200 paywall bypass)

  --secret S     (with --url, TEST MODE / LOCAL ONLY) also send a correctly signed event for an
                 unknown product twice: the endpoint must answer 2xx both times and grant nothing.

Examples:
  python3 scripts/payment_check.py --src . --provider creem
  python3 scripts/payment_check.py --url http://localhost:3000 --provider creem
  python3 scripts/payment_check.py --url http://localhost:3000 --secret whsec_test... --json

Exit code 1 when any FAIL. Never point --secret at production with a live secret.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

PROVIDERS = {
    "creem": {"path": "/api/webhooks/creem", "header": "creem-signature"},
    "paddle": {"path": "/api/webhooks/paddle", "header": "paddle-signature"},
    "stripe": {"path": "/api/webhooks/stripe", "header": "stripe-signature"},
    "lemonsqueezy": {"path": "/api/webhooks/lemonsqueezy", "header": "x-signature"},
    "polar": {"path": "/api/webhooks/polar", "header": "webhook-signature"},
}

results: list[dict] = []


def add(level: str, check: str, detail: str, fix: str = "") -> None:
    results.append({"level": level, "check": check, "detail": detail, "fix": fix})


# ---------------------------------------------------------------- static scan
SKIP_DIRS = {"node_modules", ".next", ".git", "dist", "build", "out", ".vercel", "coverage", "__pycache__", ".turbo"}
CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".rb", ".go", ".php"}
# Test, spec, fixture and mock files exercise the webhook (they send unsigned or forged requests on
# purpose, insert rows to set up state), so judging them as handlers or success pages gives false FAILs.
# They are still scanned for committed live secrets.
TEST_DIRS = {"test", "tests", "__tests__", "__test__", "spec", "specs", "e2e", "cypress", "playwright",
             "fixtures", "__fixtures__", "__mocks__", "mocks", "testdata"}
TEST_FILE_RE = re.compile(r"(\.(test|spec|e2e|stories)\.[cm]?[jt]sx?$)|(^test_.*\.py$)|(_test\.(py|go|rb)$)|(_spec\.rb$)|(Test\.php$)")


def is_test_file(rel_path: str) -> bool:
    parts = rel_path.replace(os.sep, "/").split("/")
    return bool(TEST_FILE_RE.search(parts[-1])) or any(p.lower() in TEST_DIRS for p in parts[:-1])


def walk(root: str):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.join(d, f)


def read(p: str) -> str:
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def scan_source(root: str, provider: str) -> None:
    files = list(walk(root))
    code = {p: read(p) for p in files if os.path.splitext(p)[1] in CODE_EXT and os.path.getsize(p) < 2_000_000}
    rel = lambda p: os.path.relpath(p, root)  # noqa: E731
    tests = {p for p in code if is_test_file(rel(p))}
    app_code = {p: t for p, t in code.items() if p not in tests}

    # 1. committed secrets
    live = []
    for p in files:
        name = os.path.basename(p)
        if name.startswith(".env") and name not in (".env.example", ".env.sample", ".env.template"):
            if _tracked(root, p):
                live.append(f"{rel(p)} (tracked by git)")
        if os.path.splitext(p)[1] in CODE_EXT | {".json", ".yml", ".yaml", ".md", ".toml"} and os.path.getsize(p) < 2_000_000:
            t = code.get(p) or read(p)
            for m in re.finditer(r"\b(creem_(?!test_)[A-Za-z0-9]{16,}|sk_live_[A-Za-z0-9]{16,}|whsec_[A-Za-z0-9]{24,}|pdl_live_[A-Za-z0-9_]{16,})", t):
                live.append(f"{rel(p)}: {m.group(1)[:12]}…")
    if live:
        add("FAIL", "no secrets in the repo", "; ".join(live[:8]), "Move keys to server env, rotate every key that was committed.")
    else:
        add("PASS", "no secrets in the repo", "no live-looking keys or tracked .env files")

    # 2. payment secrets exposed to the browser
    pub = sorted({m.group(0) for t in app_code.values() for m in re.finditer(r"NEXT_PUBLIC_[A-Z0-9_]*(SECRET|API_KEY|WEBHOOK)[A-Z0-9_]*", t)})
    if pub:
        add("FAIL", "payment secrets stay on the server", ", ".join(pub), "Rename without NEXT_PUBLIC_ and read only in server code.")
    else:
        add("PASS", "payment secrets stay on the server", "no NEXT_PUBLIC_*SECRET/API_KEY/WEBHOOK")

    # 3. webhook handler
    if tests:
        add("INFO", "test files", f"{len(tests)} test/spec/fixture files skipped for the handler and success-page checks (still scanned for secrets)")
    hooks = [p for p, t in app_code.items() if re.search(r"webhook", rel(p), re.I) and re.search(r"POST|def |func |app\.post|router\.post", t)]
    if not hooks:
        add("WARN", "webhook handler found", "no file with 'webhook' in its path that handles POST", "Point --src at the app root.")
        return
    for p in hooks:
        t = code[p]
        r = rel(p)
        verifies = re.search(r"createHmac|hmac\.new|timingSafeEqual|compare_digest|constructEvent|verify[A-Za-z]*Signature|validateEvent|unmarshal\(|webhooks\.verify|verifyWebhook|Webhook\(", t)
        if not verifies:
            # helper imported from elsewhere?
            imp = re.findall(r"from\s+['\"]([^'\"]+)['\"]", t)
            verifies = any(re.search(r"core|verify|webhook|signature", i, re.I) for i in imp) and re.search(r"verif|signature", t, re.I)
        add("PASS" if verifies else "FAIL", f"{r}: verifies the signature", "signature check found" if verifies else "no HMAC / verify call found",
            "" if verifies else "Verify the provider signature over the raw body before using the payload.")
        parsed_first = re.search(r"await\s+req(uest)?\.json\(\)", t) and not re.search(r"\.text\(\)|arrayBuffer\(\)|raw", t)
        add("FAIL" if parsed_first else "PASS", f"{r}: uses the raw body", "parses JSON before verifying" if parsed_first else "reads text/raw body",
            "Read req.text() (or the raw buffer), verify, then JSON.parse." if parsed_first else "")
        idem = re.search(r"event[_ ]?id|eventId|dedupe|idempot|onConflictDoNothing|ON CONFLICT|INSERT OR IGNORE|unique", t, re.I) or \
            any(re.search(r"dedupe|idempot|onConflictDoNothing|INSERT OR IGNORE", app_code[q], re.I) for q in app_code if q != p and re.search(r"entitle|grant|billing|creem|paddle|stripe", rel(q), re.I))
        add("PASS" if idem else "FAIL", f"{r}: idempotent", "event id / unique key handling found" if idem else "no event-id dedupe found",
            "" if idem else "Store each event id with a UNIQUE constraint and skip repeats; providers retry and resend.")
        refunds = re.search(r"refund|chargeback|dispute|revoke", t, re.I) or any(re.search(r"refund|dispute|chargeback", app_code[q], re.I) for q in app_code if re.search(r"entitle|grant|core", rel(q), re.I))
        add("PASS" if refunds else "WARN", f"{r}: refunds remove access", "refund/dispute handling found" if refunds else "no refund or dispute handling found",
            "" if refunds else "Revoke access on refund.created / dispute (or the provider's equivalent).")

    # 4. access granted from the success page
    bad = []
    for p, t in app_code.items():
        if re.search(r"success|thank", rel(p), re.I) and re.search(r"insert\(|\.insert|grant\(|upsert|UPDATE\s|INSERT\s", t):
            bad.append(rel(p))
    if bad:
        add("FAIL", "success page does not grant access", ", ".join(bad), "Grant only from the verified webhook; the success page just says 'processing'.")
    else:
        add("PASS", "success page does not grant access", "no writes in success/thank-you pages")


def _tracked(root: str, path: str) -> bool:
    try:
        import subprocess
        r = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", os.path.relpath(path, root)], capture_output=True)
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------- probes
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # noqa: D401
        return None


opener = urllib.request.build_opener(NoRedirect)


def http(method: str, url: str, body: bytes | None = None, headers: dict | None = None, timeout: float = 10):
    req = urllib.request.Request(url, data=body, method=method, headers={"user-agent": "payment-check/1.0", **(headers or {})})
    t0 = time.time()
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.read(4096).decode("utf-8", "replace"), dict(r.headers), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read(4096).decode("utf-8", "replace"), dict(e.headers or {}), time.time() - t0
    except Exception as e:  # noqa: BLE001
        return 0, str(e), {}, time.time() - t0


def probe(origin: str, provider: str, path: str | None, secret: str | None) -> None:
    origin = origin.rstrip("/")
    cfg = PROVIDERS[provider]
    hook = origin + (path or cfg["path"])
    body = json.dumps({"id": f"evt_check_{uuid.uuid4().hex[:12]}", "eventType": "checkout.completed", "created_at": int(time.time() * 1000),
                       "object": {"id": "ch_check", "product": {"id": "prod_payment_check_unknown"}, "metadata": {}}}).encode()

    s, txt, h, dt = http("POST", hook, body, {"content-type": "application/json"})
    if s == 0:
        add("FAIL", "webhook reachable", f"{hook}: {txt[:120]}", "Is the server running and the path right (--webhook-path)?")
        return
    if s in (301, 302, 303, 307, 308):
        add("FAIL", "webhook does not redirect", f"{s} → {h.get('Location') or h.get('location')}", "Register the final URL (https, exact host, no trailing-slash redirect); providers don't follow redirects.")
    elif s == 404 or s == 405:
        add("FAIL", "webhook reachable", f"{hook} → {s}", "Wrong path, or the route is not deployed.")
    elif 200 <= s < 300:
        add("FAIL", "unsigned webhook rejected", f"{s} for a request with no signature", "Verify the signature and return 401 when it is missing or wrong.")
    elif s in (400, 401, 403):
        add("PASS", "unsigned webhook rejected", f"{s}")
    elif s == 503:
        add("WARN", "unsigned webhook rejected", "503: webhook secret not configured on the server", "Set the webhook secret in the server env.")
    else:
        add("WARN", "unsigned webhook rejected", f"unexpected {s}: {txt[:120]}")
    if "cf-mitigated" in {k.lower() for k in h} or re.search(r"captcha|attention required|access denied", txt, re.I):
        add("FAIL", "no WAF / bot challenge on the webhook", "response looks like a bot challenge", "Exclude the webhook path from WAF, bot protection and rate limits.")

    s2, _, _, _ = http("POST", hook, body, {"content-type": "application/json", cfg["header"]: "0" * 64 if provider != "paddle" else f"ts={int(time.time())};h1={'0'*64}"})
    if s2 in (400, 401, 403):
        add("PASS", "wrong signature rejected", f"{s2}")
    elif 200 <= s2 < 300:
        add("FAIL", "wrong signature rejected", f"{s2} for a forged signature", "Compare the HMAC with a constant-time check and return 401 on mismatch.")
    else:
        add("WARN", "wrong signature rejected", f"{s2}")

    if secret:
        if provider not in ("creem", "paddle"):
            add("WARN", "signed test event", f"--secret signing is implemented for creem and paddle only, not {provider}")
        else:
            statuses = []
            for _ in range(2):
                if provider == "creem":
                    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
                else:
                    ts = str(int(time.time()))
                    sig = f"ts={ts};h1=" + hmac.new(secret.encode(), ts.encode() + b":" + body, hashlib.sha256).hexdigest()
                st, tx, _, dt2 = http("POST", hook, body, {"content-type": "application/json", cfg["header"]: sig})
                statuses.append((st, tx[:160], dt2))
            ok = all(200 <= st < 300 for st, _, _ in statuses)
            add("PASS" if ok else "FAIL", "signed event accepted, repeat is harmless",
                " / ".join(f"{st} {tx}" for st, tx, _ in statuses),
                "" if ok else "A valid signed event must get 2xx (even an unknown product), or the provider keeps retrying.")
            slow = max(d for _, _, d in statuses)
            add("PASS" if slow < 5 else "WARN", "webhook answers fast", f"{slow:.2f}s", "" if slow < 5 else "Answer within a few seconds; queue slow work.")

    for cpath in ("/api/checkout", "/api/checkout/creem", "/api/billing/checkout"):
        cs, ctxt, _, _ = http("POST", origin + cpath, b'{"plan":"monthly"}', {"content-type": "application/json"})
        if cs in (404, 405):
            continue
        if 200 <= cs < 300 and "http" in ctxt:
            add("WARN", "checkout requires a login", f"{cpath} returned a checkout URL without a session", "Fine for guest checkout; otherwise require a session so the webhook can map the buyer.")
        else:
            add("PASS", "checkout requires a login", f"{cpath} → {cs}")
        break

    rs, _, _, _ = http("GET", origin + f"/payment-check-{uuid.uuid4().hex[:8]}")
    add("PASS" if rs == 404 else "WARN", "unknown URL is a real 404", f"{rs}")


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src")
    ap.add_argument("--url")
    ap.add_argument("--provider", default="creem", choices=sorted(PROVIDERS))
    ap.add_argument("--webhook-path")
    ap.add_argument("--secret", help="TEST MODE ONLY: webhook signing secret for signed probes")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.src and not a.url:
        ap.error("give --src, --url or both")
    if a.src:
        scan_source(a.src, a.provider)
    if a.url:
        probe(a.url, a.provider, a.webhook_path, a.secret)
    fails = sum(r["level"] == "FAIL" for r in results)
    if a.json:
        print(json.dumps({"results": results, "fail": fails}, indent=2))
    else:
        for r in results:
            print(f"{r['level']:<4}  {r['check']}: {r['detail']}" + (f"\n      fix: {r['fix']}" if r["fix"] and r["level"] != "PASS" else ""))
        print(f"\n{len(results)} checks, {fails} FAIL, {sum(r['level']=='WARN' for r in results)} WARN")
        print("Not covered by this script: a real test-card purchase, refund in the dashboard, and the "
              "decline card. See references/payment-checks.md.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
