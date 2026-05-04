# n8n V2 — when, when not, and what we built

This folder is the second deliverable. The brief asked for a workflow sketch, "n8n-style or any equivalent." I built **both** approaches end-to-end on the same backend so the comparison is concrete instead of theoretical:

- `code/` (sibling folder) — the Python service. Production-grade, prompt-cached, structured-output, hybrid retrieval, defense in depth, audit log.
- `n8n_v2/emoti_cs_pipeline.json` — an n8n workflow that wraps the same backend as a hybrid orchestrator. Spin up via `docker compose --profile hybrid up` — the `n8n` service in `docker-compose.yml` is profile-gated so it only starts when you ask for it.

Both run side by side against the same Postgres, the same Redis, the same KB, the same audit log. The point of having both is not "n8n bad, Python good." That framing is wrong. The point is to show, against the same scenario, where each tool earns its keep and where it costs more than it saves.

## What's in `emoti_cs_pipeline.json`

Left-to-right, the n8n workflow does:

1. **Webhook (POST `/webhook/emoti-ticket`)** — n8n's native webhook node, with retry on failure enabled.
2. **HMAC verify (Function node)** — recomputes the signature and rejects on mismatch (300-second clock skew window, same as the Python service).
3. **Idempotency check (Redis node)** — `SETNX` on the `X-Idempotency-Key` header with a 24h TTL.
4. **Pattern pre-filter (Function node)** — JS port of the Python regex set (English + Polish jailbreak markers, base64 strings of 40+ chars with attempted decode, suspicious URLs, invisible Unicode).
5. **HTTP Request → backend `POST /api/v1/tickets`** — hands the ticket to the Python service with HMAC + idempotency headers. Backend runs classifier + judge + drafter (or escalation).
6. **Wait + HTTP Request → backend `GET /api/v1/tickets/{id}`** — polls until the pipeline finishes, gets the resulting status.
7. **Switch node** — branches on the result:
   - `escalated_human` → Slack alert (refund/supplier/killswitch path).
   - `suspected_injection: true` → Slack injection alert (quarantined, no draft).
   - `drafted` / `in_review` → Slack draft-ready notification with deep link to the operator console.
8. **Respond to webhook** — returns `{ticket_id, status}` to whoever POSTed the ticket.

The n8n workflow is intentionally a **thin orchestrator** that calls back into the Python service for the LLM-heavy parts. That is the hybrid pattern I'd recommend in production.

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
# Open http://localhost:5678
# Create a workflow, click "Import from file" → /import/emoti_cs_pipeline.json
# Set workflow variables: EMOTI_API_BASE = http://backend:8000, EMOTI_API_KEY, EMOTI_HMAC_SECRET
# (Optionally set SLACK_WEBHOOK_URL in the n8n environment for alert nodes.)
# Activate the workflow. Hit POST http://localhost:5678/webhook/emoti-ticket with the same
# JSON payload the Python backend accepts at /api/v1/tickets — n8n will orchestrate the rest.
```

## Why no screenshot of the canvas

Screenshots of an n8n canvas tell you nothing the JSON doesn't. If the import works in your instance, that *is* the canvas. The JSON is the source of truth and it's diffable in Git, which is how I'd want to manage the workflow long-term anyway.
