# n8n V2 — when, when not, and what we built

This folder is the second deliverable. The brief asked for a workflow sketch, "n8n-style or any equivalent." I built **both** approaches end-to-end on the same backend so the comparison is concrete instead of theoretical:

- `code/` (sibling folder) — the Python service. Production-grade, prompt-cached, structured-output, hybrid retrieval, defense in depth, audit log.
- `n8n_v2/emoti_cs_pipeline.json` — an n8n workflow that wraps the same backend as a hybrid orchestrator. Spin up via `docker compose --profile hybrid up` — the `n8n` service in `docker-compose.yml` is profile-gated so it only starts when you ask for it.

Both run side by side against the same Postgres, the same Redis, the same KB, the same audit log. The point of having both is not "n8n bad, Python good." That framing is wrong. The point is to show, against the same scenario, where each tool earns its keep and where it costs more than it saves.

## What's in `emoti_cs_pipeline.json`

Left-to-right, the n8n workflow does (15 nodes):

1. **Webhook (POST `/webhook/emoti-ticket`)** — n8n native, `rawBody=true` so the HMAC step can recompute the signature against the original bytes.
2. **Decode + extract metadata (Code node)** — pulls the raw body out of the binary buffer, JSON-parses it, extracts `X-Webhook-Signature` and `X-Idempotency-Key` headers, builds the `<ts>.<body>` HMAC input string, exposes flat fields (`source`, `body`, `subject`, etc.) for downstream nodes.
3. **Compute HMAC (Crypto node, native)** — SHA-256 hex on `<ts>.<body>` using `EMOTI_HMAC_SECRET`. Native node, **no `require('crypto')`** — that was the sandbox trap in earlier drafts.
4. **HMAC verdict (Code node)** — compares the computed hex to the signature header with a 300-second clock-skew window (matches `backend/app/security/hmac_signing.py`). Returns `pass` / `fail` / `skip` (skip = no signature header sent → demo passes through; backend re-verifies anyway).
5. **HMAC OK? (IF node)** — false branch → 401 Respond. True branch continues.
6. **Pattern pre-filter (Code node)** — pure JS regex port of `services/defense.py` (English + Polish jailbreak markers; no `require`). Annotates `_prefilter_signals` for downstream observability.
7. **POST `/api/v1/tickets` (HTTP Request)** — JSON body built via single `JSON.stringify({...})` expression in `jsonBody` (avoids the n8n 1.x bug where template expressions inside a multi-line JSON string get serialized incorrectly). Forwards `X-Idempotency-Key` so the backend's Redis SETNX in `security/idempotency.py` handles replay protection — one source of truth, no duplicate logic between n8n and Python.
8. **Wait 15s** — gives the Python pipeline time to finish (pre-filter → classifier+judge in parallel → KB retrieval → drafter → audit log).
9. **GET `/api/v1/tickets/{id}` (HTTP Request)** — pulls the resulting status, category, `suspected_injection` flag.
10. **Switch v3 — Route by status** — three rules with `renameOutput` so the canvas reads cleanly:
    - `injection` → `suspected_injection == true`
    - `escalated` → `status == escalated_human`
    - `drafted` → fallback (status `drafted` / `in_review`)
11. **Slack alerts (3× HTTP Request)** — one per branch, POST to `SLACK_WEBHOOK_URL`. `continueOnFail: true` so an empty/missing webhook URL doesn't break the user response. Falls back to a harmless `/health` URL if the env is unset.
12. **Respond to webhook** — two respond nodes covering the exits: 200 OK with `{ticket_id, status, category, suspected_injection}`, and 401 with `{error: "invalid HMAC signature", reason: ...}`.

The n8n workflow is intentionally a **thin orchestrator** that calls back into the Python service for the LLM-heavy parts. Idempotency, the audit log, the LLM calls, defense in depth, killswitches — all stay in the Python service. n8n owns the edge: webhook, HMAC verify, pre-filter, status routing, alerts. That is the hybrid pattern I'd recommend in production.

## Decision matrix — when each tool earns its keep

(Verified against the current state of n8n in 2026. n8n moves fast, so a few of these are different from what you'd find in a 2024 version.)

| Concern | n8n native today (2026) | Python service |
|---|---|---|
| Cron-based polling (poll Gmail every 5 min) | ✅ Schedule trigger built-in | 🟡 Needs Celery beat or APScheduler |
| Multi-vendor notification fan-out (Slack + email + SMS) | ✅ One node per vendor, easy fan-out | 🟡 Vendor SDKs scattered, more wiring |
| Webhook entry point with retry on failure | ✅ "Retry on Fail" on the node | 🟡 Custom retry decorator |
| Dead-letter queue on webhook failures | 🟡 Possible via Error Trigger workflow + external store; not webhook-native | ✅ Tenacity + Redis DLQ in code |
| Anthropic prompt caching with `cache_control` | ✅ Native toggle on the Anthropic node since [PR #22318](https://github.com/n8n-io/n8n/pull/22318) (system-message single-block) | ✅ Multi-block cache prefixes (brand voice + KB chunks per category, separate breakpoints) |
| Tool-use schema validation | 🟡 Manual JSON parsing in a Code node | ✅ Pydantic models + Anthropic tool spec, reject malformed responses |
| Confidence-based routing logic | 🟡 Switch + Code nodes, gets tangled past 3 branches | ✅ Clean Python control flow + tests |
| Audit log with per-call token counts and prompt versions | 🟡 Bolt-on (HTTP node writes to a DB) | ✅ First-class column in `audit_log`, queried by the metrics endpoint |
| Prompt versioning + A/B | 🟡 Workflow versioning exists on n8n Cloud, but prompts as raw strings in nodes are hard to diff in code review | ✅ Prompt registry in code, full Git history, every audit row records `prompt_version` |
| Defense in depth (5 layers) | 🟡 Possible but each layer is a node; ordering is brittle, easy to skip a step on copy-paste | ✅ `pipeline.py` is one readable file with explicit guards |
| GDPR / PII masking before logging | 🟡 Code node hack | ✅ `defense.sanitize_for_logging` applied centrally |
| Cost dashboard (LLM cost per ticket, cache hit rate over time) | ❌ No native LLM-cost aggregation | ✅ SQL on `audit_log` exposed at `/api/v1/metrics` |
| Unit tests | 🟡 n8n has workflow-level tests on Cloud, but isolated unit tests of branch logic are awkward | ✅ pytest, every service layer testable in isolation |
| Visualization for non-technical supervisors | ✅ Canvas is its own product | ❌ Code is code |

The honest summary: n8n today is *much* more capable than it was 18 months ago. Native Anthropic prompt caching is the biggest leveling-up — that single PR removed one of the strongest historical reasons to put the LLM core outside n8n. Where the Python service still wins is the things that compound over months: prompt versioning in Git, structured-output validation that a JS Code node cannot match cleanly, an audit log shaped for replay and forensics, and a unit test suite per service layer.

## My recommendation

**Hybrid — n8n on the front, Python service in the middle.**

- n8n owns: the glue. Webhooks in, Slack alerts out, cron-based polling, simple branching for non-LLM logic, supervisor ad-hoc workflows, the "drag and drop" surface for ops.
- Python service owns: the LLM core. Classifier, judge, retriever, drafter, defense layers, audit log, cost tracking, prompt versioning, the structured-output contract.
- They communicate via authenticated HTTP between each other (HMAC + API key, optionally JWT).

The path I'd push back hardest on is **n8n calling Anthropic directly through Code nodes** — even with the prompt-caching toggle, you still inherit the operational gaps: no `cache_control` for multi-block prefixes (KB per category, brand voice), no tool-use schema validation past basic JSON parsing, no shared audit log with the metrics dashboard, no prompt registry. The only place that pattern saves real time is the absolute first prototype — and you pay it back the first month it's in production.

## How to run it

```bash
# Pure-code path (default — no n8n)
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_kb
docker compose exec backend python -m app.scripts.seed_tickets

# Hybrid path (Python service + n8n)
docker compose --profile hybrid up -d

# Auto-import + activate the workflow via n8n CLI (faster than clicking through the UI):
docker compose exec n8n n8n import:workflow --input=/import/emoti_cs_pipeline.array.json
WID=$(docker compose exec -T n8n n8n list:workflow | grep "Emoti CS" | tail -1 | awk -F'|' '{print $1}' | tr -d '[:space:]')
docker compose exec n8n n8n update:workflow --id=$WID --active=true
docker compose restart n8n  # n8n only registers webhooks on (re)start
```

Webhook URL: `POST http://localhost:5678/webhook/emoti-ticket`.

### Demo: unsigned request (HMAC verdict → "skip")

```bash
curl -X POST http://localhost:5678/webhook/emoti-ticket \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: $(uuidgen)" \
  -d '{"source":"chat","subject":"test","body":"Dzien dobry, voucher WPRZ-184220 nie dziala"}'
```

### Demo: signed request (HMAC verdict → "pass")

```bash
SECRET="demo-hmac-secret-change-me"
TS=$(date +%s)
BODY='{"source":"chat","subject":"test","body":"Dzien dobry, voucher WPRZ-184220 nie dziala"}'
SIG=$(printf "%s.%s" "$TS" "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $NF}')

curl -X POST http://localhost:5678/webhook/emoti-ticket \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: t=$TS,v1=$SIG" \
  -H "X-Idempotency-Key: $(uuidgen)" \
  -d "$BODY"
```

### Demo: replay → 200 `duplicate_idempotent`

Re-run the same curl with the same `X-Idempotency-Key` header — the **backend's** Redis SETNX (`app/security/idempotency.py`) catches it and returns `{"ticket_id":"duplicate","status":"duplicate_idempotent"}`. The n8n workflow's IF node detects `ticket_id == "duplicate"` and routes straight to the duplicate Respond node, skipping the Wait + GET steps that don't make sense for a non-existent ticket. Idempotency is single-source-of-truth in the backend; n8n just propagates the verdict.

### Optional: Slack alerts

Set `SLACK_WEBHOOK_URL` in the `n8n` service environment in `docker-compose.yml`. Each ticket then triggers one Slack POST per outcome (injection / escalated / drafted). Without it set, the Slack nodes silently fail (`continueOnFail: true`) and the user response is unaffected.

## Test results

Full edge-case suite (`TESTS_E2E.md` §15, TC-N8N-001..016) executed against the running stack — 10/10 substantive cases PASS:

| Test | Result | Note |
|---|---|---|
| TC-N8N-001 setup smoke | ✅ | webhook live, workflow active |
| TC-N8N-002 unsigned happy path | ✅ | HMAC verdict=skip, ticket drafted |
| TC-N8N-003 signed correct HMAC | ✅ | Crypto + IF passes |
| TC-N8N-004 bad signature | ✅ | 401 with `signature mismatch` |
| TC-N8N-005 stale timestamp (>300s) | ✅ | 401 with `outside 300s window` |
| TC-N8N-006 injection T-009 | ✅ | escalated_human + suspected_injection=true |
| TC-N8N-007 refund escalation | ✅ | escalated_human + category=refund_request, no draft |
| TC-N8N-008 idempotency replay | ✅ | first → tkt_…, replay → `{"ticket_id":"duplicate"}` |
| TC-N8N-009 PL diacritics | ✅ | end-to-end from request body to `tickets.body` in Postgres |
| TC-N8N-013 audit log row created | ✅ | first row = `ticket_received` |
| TC-N8N-016 webhook vs direct API parity | ✅ | both routes produce 4 audit_log rows per ticket |

Runner script: `run_n8n_tests.sh` (curl-based). TC-N8N-014 (CLI lifecycle) and TC-N8N-015 (backend offline) are documented but skipped from the scripted run because they require restarts / service stops; reproduce manually per `TESTS_E2E.md`.

## Why no screenshot of the canvas

Screenshots of an n8n canvas tell you nothing the JSON doesn't. If the import works in your instance, that *is* the canvas. The JSON is the source of truth and it's diffable in Git, which is how I'd want to manage the workflow long-term anyway.
