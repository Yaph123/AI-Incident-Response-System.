# AI Incident Response System

Ingest alerts, gather operational context, run an AI-assisted triage pipeline, and keep every incident step traceable—from webhook to postmortem draft.

This is an active personal project for exploring how AI can support **structured incident response** without turning into an opaque chatbot. Built by [Yaphet Bekele](https://github.com/Yaph123) — CS & Cognitive Science at USC (B.S. / B.A., December 2027). If you try it, fork it, or have ideas, use [GitHub Issues](https://github.com/Yaph123/AI-Incident-Response-System./issues) to share feedback.

## Why I Built This

Most on-call workflows still scatter context across Slack threads, monitoring dashboards, GitHub, and runbook wikis. When something breaks at 2am, the hard part is not just *seeing* the alert—it is pulling the right context together fast enough to act.

I wanted a system where:

- **Alerts become incidents** with a durable record, not a forgotten notification.
- **Context is gathered automatically**—recent deploys, PRs, matched runbooks—before anyone writes a summary from scratch.
- **AI assists but does not replace judgment**—summaries and postmortem drafts are suggestions you can review, edit, and approve.
- **Every step is logged** as an event on the incident timeline so you can answer: what happened, when, and what did the system do?

This repo is the first slice of that vision—a full-stack MVP scaffold that proves the pipeline end-to-end before hardening for production.

## Who This Is For

AI Incident Response is an **operational triage and documentation system**—not a replacement for your on-call rotation or incident commander.

**Typical users**

- **SREs and platform engineers** who want webhook-driven incident intake with automated context gathering
- **On-call leads** who want AI-generated summaries and postmortem drafts tied to a real incident record
- **Small teams** prototyping AI-assisted incident workflows before investing in enterprise tooling

**What it is not**

- A replacement for PagerDuty, Datadog, or your existing alerting stack—it ingests from them via webhooks
- A fully autonomous incident resolver—you review AI output and control Slack posting
- Production-hardened out of the box—auth, RBAC, idempotency, and observability still need work

**How you use it (vision)**

1. Register services and runbooks in the catalog.
2. Point your monitoring tool at the alert webhook.
3. The system creates an incident, queues a Celery worker, and runs the pipeline.
4. Review the dashboard, incident detail API, AI summary, evidence, and postmortem draft.
5. Update status, re-run the pipeline, or approve Slack posts as needed.

## What It Does

When an alert webhook arrives, the system creates an **incident** and **alert** record, logs an `alert_received` event, and queues asynchronous processing. A Celery worker then moves the incident through investigation: GitHub context fetch, runbook matching, AI summary generation, Slack notification (or approval gate), and postmortem draft creation.

- Accept webhook alerts from any source (`POST /api/alerts/webhook`).
- Persist incidents, alerts, events, evidence, Slack messages, postmortem drafts, services, runbooks, and approvals in PostgreSQL.
- Fetch recent GitHub commits and PRs when a service has a configured repo.
- Match runbooks by keyword search and attach them as evidence.
- Generate AI incident summaries and postmortem drafts (OpenAI when configured; safe stubs otherwise).
- Post to Slack via webhook or bot token—or stage for approval when `REQUIRE_APPROVAL_FOR_SLACK=true`.
- Render a simple Next.js dashboard listing active incidents and AI summaries.

## Key Features

- **Webhook ingestion** — normalize alerts from Datadog, PagerDuty, Grafana, or custom sources into incidents
- **Incident timeline** — every pipeline step recorded as an `incident_event` with type, message, and payload
- **Evidence model** — GitHub commits/PRs, matched runbooks, and future manual/AI evidence in one place
- **Service catalog** — map services to owner teams, GitHub repos, and Slack channels
- **Runbook store** — create runbooks with optional pgvector embeddings for future semantic search
- **AI reasoning layer** — OpenAI-powered summaries and postmortem drafts with structured fallback stubs
- **Slack collaboration** — post incident updates to a channel or require approval first
- **Async orchestration** — Celery + Redis so webhook responses stay fast while processing runs in the background
- **Dashboard** — Next.js UI at `http://localhost:3000` for at-a-glance incident monitoring
- **Docker Compose** — one command to run Postgres, Redis, API, worker, and frontend locally

## Current Status

**Implemented**

- FastAPI backend with health, alerts, incidents, runbooks, and services routes
- SQLAlchemy models for all core entities (see table below)
- Celery worker with `process_incident` task
- Incident pipeline: status → GitHub context → AI summary → Slack → postmortem draft
- OpenAI, Slack, and GitHub integrations (all optional for local dev)
- Next.js dashboard (incident list + status badges + AI summary preview)
- Docker Compose stack (Postgres + pgvector, Redis, backend, worker, frontend)
- GitHub Actions CI (backend import smoke test + frontend build)
- Auto table creation on backend startup (pgvector extension enabled)

**Planned**

- Alembic migrations (replace startup `create_all`)
- Vector similarity search for runbooks (embeddings stored; search is keyword-only today)
- Incident detail page in the frontend (API already supports `GET /api/incidents/{id}`)
- Auth, RBAC, and multi-tenant isolation
- Webhook signature verification and idempotency keys
- Approval workflow UI (approve/reject staged Slack posts)
- PagerDuty / Datadog native integrations beyond generic webhooks
- Observability: structured metrics, tracing, and alerting on the platform itself

The repo is evolving quickly; the core pattern—alert → incident → async pipeline → traceable events—is stable, but production hardening is still early.

## Architecture

Two views: **(1) the incident response pipeline**—what happens when an alert fires—and **(2) the application stack**—how the software is built.

### Incident pipeline (alert → resolution)

Each **incident** is the central record. Each **pipeline step** writes events and evidence. Processing runs asynchronously via Celery after the webhook returns.

```mermaid
flowchart TB
  WH["Webhook Alert<br/><i>POST /api/alerts/webhook</i>"]

  WH -->|"Ingest ✅"| INC["Incident + Alert<br/><i>status: open</i>"]
  INC -->|"Celery queue ✅"| W["Worker: process_incident"]

  W -->|"Status ✅"| INV["investigating"]
  INV -->|"GitHub context ✅"| EV1["Evidence: commits, PRs"]
  EV1 -->|"Runbook match ✅"| EV2["Evidence: runbooks"]
  EV2 -->|"AI summary ✅"| AI["ai_summary + recommendations"]
  AI -->|"Slack ✅"| SL["Slack message or approval gate"]
  SL -->|"Postmortem ✅"| PM["Postmortem draft"]

  classDef done fill:#ecfdf5,stroke:#059669,stroke-width:2px
  classDef root fill:#eef2ff,stroke:#4f46e5,stroke-width:2px

  class WH root
  class INC,W,INV,EV1,EV2,AI,SL,PM done
```

> **Traceability:** Every step also creates an `incident_event` (alert received, status changed, GitHub context, AI summary, runbook match, Slack posted, postmortem draft, approval). Fetch the full timeline via `GET /api/incidents/{id}`.

| Step | Service / module | Writes | Status |
|------|------------------|--------|--------|
| **Ingest alert** | `services/ingestion` | `Incident`, `Alert`, `alert_received` event | ✅ Implemented |
| **Queue worker** | `workers/tasks` | Celery job | ✅ Implemented |
| **GitHub context** | `services/context` + `integrations/github` | `EvidenceItem` (commits, PRs) | ✅ Implemented (needs `GITHUB_TOKEN` + repo) |
| **Runbook match** | `services/context` | `EvidenceItem` (runbooks) | ✅ Keyword search |
| **AI summary** | `services/ai` + `integrations/openai_client` | `ai_summary`, `ai_recommendations` | ✅ LLM or stub |
| **Slack notify** | `services/orchestration` + `integrations/slack` | `SlackMessage`, optional `Approval` | ✅ Webhook, bot, or local log |
| **Postmortem draft** | `services/ai` | `PostmortemDraft` | ✅ LLM or stub |

**Manual / API steps**

| Action | How |
|--------|-----|
| Register a service | `POST /api/services` |
| Add a runbook | `POST /api/runbooks` |
| Update incident status | `PATCH /api/incidents/{id}` |
| Re-run pipeline | `POST /api/incidents/{id}/run` |

**Rules (pipeline)**

1. Webhook creates incident + alert synchronously and returns immediately.
2. Celery worker runs `run_incident_pipeline` asynchronously.
3. Each step logs an event and persists evidence before moving on.
4. Slack posting respects `REQUIRE_APPROVAL_FOR_SLACK`—when true, an `Approval` record is created instead of posting.

```mermaid
flowchart LR
  IG["Ingestion"]
  CX["Context"]
  AI["AI Reasoning"]
  CO["Collaboration"]
  PS["Persistence"]

  IG --> CX --> AI --> CO --> PS
```

That row is the **logical layer order**—ingestion, context retrieval, AI reasoning, collaboration (Slack), and persistence (events + evidence + drafts).

### Application stack (software)

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI Incident Response System (Docker Compose)                      │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────┐ │
│  │ Next.js frontend   │  │ FastAPI backend    │  │ Celery worker  │ │
│  │ · Incident list    │◄─┤ · REST API         │◄─┤ · process_     │ │
│  │ · Status badges    │  │ · Webhook ingest   │  │   incident     │ │
│  │ · AI summary peek  │  │ · Orchestration    │  │                │ │
│  └────────────────────┘  └─────────┬──────────┘  └───────┬────────┘ │
│                                    │                      │          │
│                          ┌─────────▼──────────┐  ┌───────▼────────┐ │
│                          │ PostgreSQL +       │  │ Redis          │ │
│                          │ pgvector           │  │ (Celery broker)│ │
│                          └────────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              OpenAI · Slack · GitHub (optional integrations)
```

| Layer | Role |
|--------|------|
| **Frontend** | Next.js dashboard; fetches incidents from the API |
| **API** | FastAPI routes for webhooks, incidents, runbooks, services |
| **Services** | Ingestion, context, AI, orchestration business logic |
| **Workers** | Celery async pipeline execution |
| **Integrations** | OpenAI, Slack webhook/bot, GitHub REST API |
| **Database** | PostgreSQL with pgvector for runbook embeddings |
| **Queue** | Redis for Celery broker and result backend |

### Data model

| Table | Purpose |
|--------|---------|
| `service_catalog` | Services with owner team, GitHub repo, Slack channel |
| `runbooks` | Runbook content, tags, optional vector embedding |
| `incidents` | Core incident record with status, severity, AI fields |
| `alerts` | Raw alert payloads linked to incidents |
| `incident_events` | Timeline of pipeline and manual actions |
| `evidence_items` | GitHub, runbook, alert, manual, or AI evidence |
| `slack_messages` | Outbound Slack messages (posted or staged) |
| `postmortem_drafts` | AI-generated postmortem with timeline and action items |
| `approvals` | Approval gates for sensitive actions (e.g. Slack post) |

**Incident statuses:** `open` → `investigating` → `mitigated` → `resolved`

## What Makes It Different

- **Pipeline, not chat** — incidents are structured records with events and evidence, not a single LLM thread
- **Context before summary** — GitHub and runbook evidence is gathered before the AI writes anything
- **Async by default** — webhooks return fast; heavy work runs in Celery
- **Approval gates** — Slack posts can require human approval before sending
- **Stub-safe local dev** — full flow works without OpenAI, Slack, or GitHub keys
- **Traceable timeline** — every automated and manual action is an `incident_event`

## What's Next

- **Alembic migrations** — versioned schema instead of startup `create_all`
- **Vector runbook search** — use stored pgvector embeddings for semantic matching
- **Frontend incident detail** — timeline, evidence panel, postmortem viewer
- **Webhook auth** — HMAC signature verification per alert source
- **Approval UI** — review and approve/reject staged Slack messages
- **Re-run and branching** — partial pipeline re-runs without duplicating evidence
- **Native integrations** — PagerDuty, Datadog, Grafana alert formatters
- **Production deploy** — Kubernetes manifests, secrets management, observability

## Feedback

If you want to try the project, report a bug, or share an idea, [open a GitHub issue](https://github.com/Yaph123/AI-Incident-Response-System./issues). This repo is public so people can inspect the work, fork it, and follow the project as it develops.

## Tech Stack

- **Next.js 14** + **TypeScript** + **Tailwind CSS** — dashboard UI
- **FastAPI** + **Python 3.12** — REST API and orchestration
- **SQLAlchemy 2** — ORM and models
- **PostgreSQL 16** + **pgvector** — persistence and runbook embeddings
- **Redis 7** — Celery broker and result backend
- **Celery 5** — async incident pipeline worker
- **OpenAI API** — summaries, postmortems, embeddings (optional)
- **Slack** — webhook or bot token for incident notifications (optional)
- **GitHub REST API** — recent commits and PRs for context (optional)
- **Docker Compose** — local multi-service development

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** — recommended for running the full stack
- **Git** — for cloning and version control
- **Node.js 20+** — only if running the frontend outside Docker
- **Python 3.12+** — only if running the backend outside Docker

### Install

```bash
git clone git@github.com:Yaph123/AI-Incident-Response-System..git
cd AI-Incident-Response
```

> **Note:** The GitHub repo name ends with a period (`AI-Incident-Response-System.`), so the SSH URL uses `..git` at the end.

Copy the environment file:

```bash
cp .env.example .env
```

### Run the stack

```bash
docker compose up --build
```

Open:

- **Dashboard:** `http://localhost:3000`
- **API docs:** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/api/healthz`

Useful commands:

```bash
docker compose up -d          # run in background
docker compose logs -f worker # watch Celery pipeline logs
docker compose down           # stop all services
docker compose down -v        # stop and remove database volume
```

### API keys (optional)

Integrations are optional. Without keys, the system uses safe stubs and local logging so you can explore the full flow.

Edit `.env` in the project root. **Never commit `.env`.**

**OpenAI (summaries, postmortems, embeddings):**

```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Slack (incident notifications):**

```env
# Option A: incoming webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Option B: bot token
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_DEFAULT_CHANNEL=#incidents
```

**GitHub (recent commits and PRs as evidence):**

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_DEFAULT_OWNER=your-org
GITHUB_DEFAULT_REPO=your-repo
```

**Approval gate for Slack:**

```env
REQUIRE_APPROVAL_FOR_SLACK=true
```

When enabled, Slack messages are staged and an `Approval` record is created instead of posting immediately.

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg://incident:incident@localhost:5433/incident_response` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model for summaries and postmortems |
| `SLACK_DEFAULT_CHANNEL` | `#incidents` | Fallback Slack channel |
| `LOG_LEVEL` | `INFO` | Structlog verbosity |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → API base URL |

### First run

1. Start the stack: `docker compose up --build`
2. Register a service (optional but recommended):

   ```bash
   curl -X POST http://localhost:8000/api/services \
     -H "Content-Type: application/json" \
     -d '{
       "name": "payments",
       "owner_team": "sre",
       "github_repo": "YOUR_ORG/YOUR_REPO",
       "slack_channel": "#incidents"
     }'
   ```

3. Add a runbook:

   ```bash
   curl -X POST http://localhost:8000/api/runbooks \
     -H "Content-Type: application/json" \
     -d '{
       "title": "High 5xx Error Rate",
       "content": "Check latest deploy, rollback if needed, verify DB latency.",
       "service_name": "payments",
       "tags": ["http", "errors"]
     }'
   ```

4. Send a test alert:

   ```bash
   curl -X POST http://localhost:8000/api/alerts/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "source": "datadog",
       "title": "Payments API 5xx spike",
       "severity": "high",
       "service_name": "payments",
       "description": "5xx above threshold for 10 minutes",
       "payload": {"monitor_id": "12345"}
     }'
   ```

5. Watch the worker process the pipeline:

   ```bash
   docker compose logs -f worker
   ```

6. View results:
   - Dashboard: `http://localhost:3000`
   - Incident list: `curl http://localhost:8000/api/incidents`
   - Incident detail (replace `{id}`): `curl http://localhost:8000/api/incidents/{id}`

### API reference (MVP)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/healthz` | Health check |
| `POST` | `/api/alerts/webhook` | Ingest alert → create incident → queue pipeline |
| `GET` | `/api/incidents` | List incidents (latest 100) |
| `GET` | `/api/incidents/{id}` | Incident detail with events, evidence, Slack, postmortems |
| `PATCH` | `/api/incidents/{id}` | Update title, description, status, severity, assignee |
| `POST` | `/api/incidents/{id}/run` | Re-run the full pipeline synchronously |
| `GET` | `/api/runbooks` | List runbooks (optional `?query=` filter) |
| `POST` | `/api/runbooks` | Create runbook and index embedding |
| `GET` | `/api/services` | List services |
| `POST` | `/api/services` | Register a service |

Interactive docs with request/response schemas: `http://localhost:8000/docs`

## Project Structure

```
AI-Incident-Response/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route handlers
│   │   ├── core/             # config, database, logging
│   │   ├── integrations/     # OpenAI, Slack, GitHub clients
│   │   ├── models/           # SQLAlchemy models and enums
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # ingestion, context, AI, orchestration
│   │   ├── workers/          # Celery app and tasks
│   │   └── main.py           # FastAPI entrypoint
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router pages
│   ├── lib/                  # API client helpers
│   ├── Dockerfile
│   └── package.json
├── infra/
│   └── docker-compose.yml    # alternate compose path
├── .github/workflows/
│   └── ci.yml                # backend + frontend CI
├── docker-compose.yml        # primary local stack
├── .env.example
└── README.md
```

## Push to GitHub (SSH)

This repo uses SSH for Git. The repository name on GitHub ends with a period:

```bash
git remote -v   # should show git@github.com:Yaph123/AI-Incident-Response-System..git
git push
```

If you need to set the remote:

```bash
git remote set-url origin git@github.com:Yaph123/AI-Incident-Response-System..git
```

## Notes

- Tables are created automatically on backend startup (`Base.metadata.create_all`). For production, migrate to Alembic.
- Runbook embeddings are stored in pgvector but search currently uses keyword `ILIKE` matching.
- This is a **separate project** from [Research OS (Mimir)](https://github.com/Yaph123/Research-OS)—they live in sibling directories and serve different domains.
