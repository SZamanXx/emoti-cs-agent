# Emoti AI Customer Service Agent

Demo systemu semi-autonomicznego agenta AI dla obsługi klienta Emoti Group: drafts replies, klasyfikuje ticketów, pulluje CMS context, eskaluje do human review. Built as deliverable for AI Automation Specialist assignment.

**Two backends in one repo:**
- **V1 — full code** (FastAPI + Postgres + pgvector + Redis + React frontend) — production-grade end-to-end working system, this directory.
- **V2 — n8n sketch** — workflow JSON + screenshot + decision matrix (kiedy n8n yes / kiedy n8n no), folder `n8n_v2/`.

**Read first:**
- [`JOURNEY.md`](./JOURNEY.md) — moje notatki z budowy, decyzje architektoniczne, tradeoffy, czego nie wiem. Brain on paper.
- [`deliverable/Brief.pdf`](./deliverable/Brief.pdf) — 7-sekcyjny brief odpowiadający na zadanie (workflow mapping, architecture, sketch, cost economics, security, 90-day plan, pushback).
- [`n8n_v2/README.md`](./n8n_v2/README.md) — n8n V2 + decision matrix.

## Quick start

```bash
# 1. Env (Anthropic key already filled; OpenAI key NOT needed — embeddings are local)
cp backend/.env.example backend/.env  # if you don't have .env yet

# 2. Up the stack
docker compose up -d --build           # first build ~5–10 min (downloads sentence-transformers model)

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Seed KB + sample tickets
docker compose exec backend python -m app.scripts.seed_kb
docker compose exec backend python -m app.scripts.seed_tickets

# 5. Open frontend
# http://localhost:5173 → /login → operator / operator-demo-pwd → /inbox
```

**Ports** (chosen to avoid clashes with sibling Docker projects):

| Service   | Host port | Container port |
| ---       | ---       | ---            |
| Frontend  | 5173      | 5173           |
| Backend   | 8010      | 8000           |
| Adminer   | 8082      | 8080           |
| Postgres  | 5434      | 5432           |
| Redis     | 6380      | 6379           |
| n8n (hybrid only) | 5678 | 5678 |

API docs: `http://localhost:8010/docs` · Adminer: `http://localhost:8082`

## Architecture

See `JOURNEY.md` for full reasoning. TL;DR:

```
Inbound API (HMAC + idempotency)
  → Pattern pre-filter
  → Classifier (Haiku 4.5, cached)
    → refund_request → escalate (NO draft, jailbreaking risk)
    → suspected_injection → escalate
    → else continue
  → KB retrieval (pgvector hybrid: cosine + tsvector PL)
  → Drafter (Sonnet 4.6, cached, structured)
  → Output validation
  → Frontend review (Accept / Edit / Reject)
  → Send via reverse-adapter (email stub / chat stub)
  → Audit log immutable
```

## Cost economics (forecast)

- 100 tix/day, all PL
- Haiku classifier + judge: ~$0.10/day
- Sonnet drafter: ~$0.79/day (95%+ cache hit)
- Embeddings: $0/day (local sentence-transformers, no API)
- **Total: ~$0.89/day = ~98 PLN/mies (@3.62 PLN/USD)**
- vs Sonnet-everything-no-cache: $8/day, ~9× drożej

Cost per ticket: ~3.2 grosza. Human cost: ~20 PLN/ticket. AI = 0.16% kosztu human. Bottleneck = accept-without-edit rate, nie token cost.

## Author

Wojciech Szymański — built for Emoti Group AI Automation Specialist round 2.
