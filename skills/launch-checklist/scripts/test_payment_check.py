#!/usr/bin/env python3
"""Self-test for payment_check.py's static scan: a bad app must FAIL, a good one must PASS.
   python3 scripts/test_payment_check.py"""
import os, subprocess, sys, tempfile, json

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "payment_check.py")

BAD = {
    "app/api/webhooks/stripe/route.ts": "export async function POST(req: Request) { const b = await req.json(); await db.insert(grants).values({ u: b.x }); return Response.json({}) }",
    "app/checkout/success/page.tsx": "export default async function P() { await db.insert(grants).values({}); return null }",
    "app/x.ts": 'const k = process.env.NEXT_PUBLIC_STRIPE_SECRET_KEY; const s = "sk_live_' + "a" * 24 + '";',
}
GOOD = {
    "app/api/webhooks/creem/route.ts": (
        "import crypto from 'node:crypto';\n"
        "export async function POST(req: Request) {\n"
        "  const raw = await req.text();\n"
        "  const sig = crypto.createHmac('sha256', process.env.CREEM_WEBHOOK_SECRET!).update(raw).digest('hex');\n"
        "  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(req.headers.get('creem-signature') ?? ''))) return new Response('', { status: 401 });\n"
        "  const ev = JSON.parse(raw);\n"
        "  db.insert(events).values({ id: ev.id }).onConflictDoNothing();\n"
        "  if (ev.eventType === 'refund.created') revoke(ev);\n"
        "  return Response.json({ ok: true });\n}\n"
    ),
    "app/checkout/success/page.tsx": "export default function P() { return <p>Processing your payment…</p> }",
}


def run(files, provider):
    with tempfile.TemporaryDirectory() as d:
        for p, t in files.items():
            os.makedirs(os.path.join(d, os.path.dirname(p)), exist_ok=True)
            open(os.path.join(d, p), "w").write(t)
        r = subprocess.run([sys.executable, SCRIPT, "--src", d, "--provider", provider, "--json"], capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)


failed = 0
def check(cond, msg):
    global failed
    print(("ok   " if cond else "FAIL ") + msg)
    failed += 0 if cond else 1

code, out = run(BAD, "stripe")
levels = {r["check"].split(": ")[-1]: r["level"] for r in out["results"]}
check(code == 1, "bad app exits 1")
for name in ["no secrets in the repo", "payment secrets stay on the server", "verifies the signature", "uses the raw body", "idempotent", "success page does not grant access"]:
    check(levels.get(name) == "FAIL", f"bad app: {name} → FAIL")
code, out = run(GOOD, "creem")
check(code == 0 and out["fail"] == 0, f"good app passes ({[r['check'] for r in out['results'] if r['level'] != 'PASS']})")

# Test files next to a good handler must not turn into false FAILs: they post unsigned/forged
# bodies on purpose and insert rows to set up state.
WITH_TESTS = dict(GOOD)
WITH_TESTS.update({
    "app/api/webhooks/creem/route.test.ts": "import { POST } from './route';\nit('rejects', async () => { const r = await POST(new Request('http://x', { method: 'POST', body: JSON.stringify({}) })); expect(r.status).toBe(401) })",
    "app/checkout/success/page.spec.tsx": "beforeEach(() => db.insert(users).values({ id: 'u1' }))",
    "tests/e2e/webhook-flow.ts": "export async function POST() { await fetch('/api/webhooks/creem', { method: 'POST', body: '{}' }) }",
    "test_webhook.py": "def test_post(client):\n    client.post('/api/webhooks/creem', json={})",
})
code, out = run(WITH_TESTS, "creem")
bad = [f"{r['check']} ({r['level']})" for r in out["results"] if r["level"] == "FAIL"]
check(code == 0 and not bad, f"good app + test files passes (FAILs: {bad})")
check(any(r["check"] == "test files" and r["level"] == "INFO" for r in out["results"]), "skipped test files are reported as INFO")
check(not any("route.test.ts" in r["check"] for r in out["results"]), "route.test.ts is not judged as a webhook handler")

# ...but a live key committed in a test file is still a FAIL.
LEAK = dict(GOOD)
LEAK["app/api/webhooks/creem/route.test.ts"] = 'const key = "sk_live_' + "b" * 24 + '";'
code, out = run(LEAK, "creem")
levels = {r["check"]: r["level"] for r in out["results"]}
check(code == 1 and levels.get("no secrets in the repo") == "FAIL", "live key inside a test file still FAILs")
print(f"\n{'all passed' if not failed else f'{failed} failed'}")
sys.exit(1 if failed else 0)
