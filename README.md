# TrustDesk — AI Support Operations Agent

A capstone implementation of the Airtribe TrustDesk case study using:

- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Retrieval:** local TF-IDF hybrid-style lexical retrieval (no hosted vector DB required)
- **AI:** provider adapter with deterministic mock fallback and optional OpenAI-compatible implementation
- **Frontend:** React + Vite
- **Persistence:** SQLite by default; PostgreSQL-compatible through `DATABASE_URL`
- **Testing:** pytest
- **Evaluation:** one API endpoint / CLI flow for eval cases
- **Security:** deterministic prompt-injection / secret / PII guardrails, approval-gated sensitive action, idempotency

## What is implemented

The project maps directly to the case-study requirements:

1. Seed/load customers, orders, tickets, knowledge documents, tool catalog and eval cases.
2. Ticket APIs and a support-agent React UI.
3. Ticket triage: category, priority, escalation.
4. Knowledge retrieval and cited draft replies.
5. Refusal/escalation when policy evidence is insufficient.
6. Approval-gated `start_refund_review` action.
7. Idempotency protection for tool execution.
8. Guardrails for identity-check bypass, hidden-coupon injection and secret/prompt disclosure.
9. Minimal AI traces.
10. Evaluation endpoint and CLI summary.

The Airtribe brief explicitly asks for REST APIs, persistent storage, a retrieval layer, an AI adapter, idempotency, tests, non-blocking AI/eval operations, and an evaluation flow. The implementation follows those requirements.

## Project structure

```text
trustdesk/
├── backend/
│   ├── app/
│   │   ├── api.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   └── services/
│   │       ├── ai.py
│   │       ├── guardrails.py
│   │       ├── retrieval.py
│   │       ├── support.py
│   │       └── tools.py
│   ├── data/
│   │   ├── customers.json
│   │   ├── orders.json
│   │   ├── tickets.json
│   │   ├── knowledge_base.json
│   │   └── eval_cases.jsonl
│   ├── tests/
│   │   └── test_core.py
│   ├── requirements.txt
│   └── run_eval.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

## 1. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://localhost:8000
http://localhost:8000/docs
```

On first startup, the database is created and the demo data is seeded.

### Optional AI provider

The AI layer is behind an adapter. Without an API key, TrustDesk uses a deterministic mock provider so the project remains runnable and testable.

For an OpenAI-compatible provider:

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4.1-mini"
```

The provider can be replaced by implementing `AIProvider` in `backend/app/services/ai.py`.

## 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## 3. Main workflow

1. Open a ticket.
2. Click **Run triage**.
3. Review category, priority and escalation.
4. Click **Generate cited draft**.
5. Review the retrieved policy citations.
6. If a sensitive action is recommended, review it in the approval panel.
7. Approve once. Repeating the same idempotency key does not duplicate the action.
8. Open **Evaluation** to see triage accuracy, citation coverage, unsafe-action blocking and escalation behavior.

## API

- `GET /api/health`
- `GET /api/tickets`
- `GET /api/tickets/{ticket_id}`
- `POST /api/tickets/{ticket_id}/triage`
- `POST /api/tickets/{ticket_id}/draft`
- `GET /api/tickets/{ticket_id}/trace`
- `GET /api/actions/pending`
- `POST /api/actions/{action_id}/approve`
- `POST /api/evaluations/run`
- `GET /api/evaluations/latest`

## Evaluation

CLI:

```bash
cd backend
python run_eval.py
```

API:

```bash
curl -X POST http://localhost:8000/api/evaluations/run
```

The report contains:

- triage accuracy
- citation coverage
- unsafe-action blocking
- escalation behavior

## Design decisions

### Retrieval

A local TF-IDF index is used intentionally. The case study allows full-text search, vector DB, hybrid retrieval, or a documented local substitute. This keeps the capstone easy to run locally. The `RetrievalService` is isolated, so it can later be replaced with pgvector, Qdrant, Chroma, Elasticsearch or another retrieval implementation.

### AI adapter

`AIProvider` isolates the model provider. The deterministic provider is useful for tests and demos; the OpenAI-compatible provider is optional.

### Safety

Customer messages and retrieved documents are treated as untrusted. A knowledge document containing instructions to ignore policy or reveal secrets is never treated as an executable instruction. Sensitive tool actions require explicit human approval.

### Date handling

Return/warranty checks are performed against the ticket's `created_at`, not the current date.

### Idempotency

The approval endpoint accepts an idempotency key and stores it with the tool call. Reusing the same key returns the existing result instead of creating a duplicate action.

## Known limitations

- Demo authentication is intentionally simple.
- TF-IDF retrieval is suitable for the capstone demo but not semantic retrieval at production scale.
- The demo seed data is synthetic because the case-study PDF describes "provided data" but the PDF itself does not contain those datasets.
- The OpenAI-compatible adapter expects the configured endpoint/model to support chat-completions style JSON.
