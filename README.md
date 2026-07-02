# AI Incident Response System (MVP)

Full-stack scaffold for AI-assisted incident triage and response.

## Stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Celery
- Data: PostgreSQL + pgvector, Redis
- Integrations: OpenAI, Slack, GitHub (all optional for local development)
- Runtime: Docker Compose

## Features in this MVP

- Ingest webhook alerts (`POST /api/alerts/webhook`)
- Persist incidents, alerts, events, evidence, slack messages, postmortem drafts, service catalog, runbooks, approvals
- Fetch recent GitHub context (commits/PRs) when repo is configured
- Match runbooks and generate AI incident summaries
- Send or stage Slack updates
- Draft postmortems
- Render a simple dashboard at `http://localhost:3000`

## Quick Start

1. Copy env file if needed:

   ```bash
   cp .env.example .env
   ```

2. Start all services:

   ```bash
   docker compose up --build
   ```

3. Open:
   - Frontend: `http://localhost:3000`
   - Backend docs: `http://localhost:8000/docs`

## Example flow

1. Create a service (optional):

   ```bash
   curl -X POST http://localhost:8000/api/services \
     -H "Content-Type: application/json" \
     -d '{
       "name":"payments",
       "owner_team":"sre",
       "github_repo":"YOUR_ORG/YOUR_REPO",
       "slack_channel":"#incidents"
     }'
   ```

2. Add a runbook:

   ```bash
   curl -X POST http://localhost:8000/api/runbooks \
     -H "Content-Type: application/json" \
     -d '{
       "title":"High 5xx Error Rate",
       "content":"Check latest deploy, rollback if needed, verify DB latency.",
       "service_name":"payments",
       "tags":["http","errors"]
     }'
   ```

3. Send an alert webhook:

   ```bash
   curl -X POST http://localhost:8000/api/alerts/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "source":"datadog",
       "title":"Payments API 5xx spike",
       "severity":"high",
       "service_name":"payments",
       "description":"5xx above threshold for 10 minutes",
       "payload":{"monitor_id":"12345"}
     }'
   ```

4. View incidents:

   ```bash
   curl http://localhost:8000/api/incidents
   ```

## Environment variables

See `.env.example`. For local development, OpenAI/Slack/GitHub are optional; the app falls back to safe stubs and local logging.

## Project structure

- `backend/app/api`: FastAPI routes
- `backend/app/services`: orchestration, ingestion, AI, context
- `backend/app/models`: SQLAlchemy models
- `backend/app/workers`: Celery worker/tasks
- `frontend`: Next.js dashboard
- `infra`: additional docker compose copy

## Notes

- This MVP creates tables automatically on backend startup.
- For production use, add robust Alembic migrations, auth, RBAC, retries, idempotency, and observability hardening.
