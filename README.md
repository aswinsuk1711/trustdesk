# TrustDesk — AI Support Operations Agent

A capstone implementation of the Airtribe TrustDesk case study.

- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Pydantic
- **Retrieval:** Local TF-IDF lexical retrieval (no hosted vector DB required)
- **AI:** Provider adapter — OpenAI-compatible (OpenRouter) or Gemini SDK, with deterministic mock fallback
- **Frontend:** React + Vite
- **Persistence:** PostgreSQL (SQLite-compatible via `DATABASE_URL`)
- **Auth:** JWT login + OTP email verification
- **Evaluation:** CLI and API endpoint for eval cases

## What is implemented

Maps directly to the Airtribe case-study requirements:

1. Knowledge base seeded on startup (KB-REFUND-001, KB-SHIPPING-001, KB-WARRANTY-001, KB-SECURITY-001, KB-ADVERSARIAL-001).
2. CRM APIs to create customers and orders; ticket APIs with customer/order linkage.
3. Support-agent React UI: create CRM data, open tickets, run triage, generate cited drafts, approve actions, run eval.
4. Ticket triage: category, priority, escalation — evaluated against `ticket.created_at`, never current date.
5. Knowledge retrieval with TF-IDF; cited draft replies grounded in policy.
6. Refusal/escalation when policy evidence is insufficient.
7. Three approval-gated tools: `start_refund_review` (30-day window), `create_replacement_order` (365-day warranty), `create_coupon` (shipping).
8. Idempotency key on every tool approval — retries return the existing result.
9. Guardrails: identity-check bypass, hidden-coupon injection, secret/prompt disclosure, PII patterns.
10. KB-ADVERSARIAL-001 filtered from retrieval — never surfaced as a citation.
11. Trace per AI run: ticket ID, run type, retrieved doc IDs, tool actions, guardrail result, final status.
12. Evaluation endpoint and CLI: triage accuracy, citation coverage, unsafe-action blocking, escalation behavior.

## Project structure

```text
trustdesk/
├── backend/
│   ├── app/
│   │   ├── api.py           # All REST endpoints
│   │   ├── config.py        # Settings from .env
│   │   ├── database.py      # SQLAlchemy engine + session
│   │   ├── main.py          # FastAPI app + lifespan
│   │   ├── models.py        # ORM models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── seed.py          # Seeds knowledge base on startup
│   │   └── services/
│   │       ├── ai.py        # AIProvider adapter (Mock / OpenAI-compatible / Gemini)
│   │       ├── auth.py      # JWT, password hashing, user/customer management
│   │       ├── email.py     # OTP generation and SMTP delivery
│   │       ├── guardrails.py# Prompt injection / PII / secret detection
│   │       ├── retrieval.py # TF-IDF retrieval, filters unsafe docs
│   │       ├── support.py   # Triage, draft, tool action orchestration
│   │       └── tools.py     # ToolCall creation with idempotency
│   ├── data/
│   │   ├── knowledge_base.json
│   │   └── eval_cases.jsonl
│   ├── .env                 # Local secrets (not committed)
│   ├── requirements.txt
│   └── run_eval.py          # CLI eval runner
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main UI: CRM, tickets, triage, draft, eval
│   │   ├── Login.jsx        # Login / signup / OTP verification
│   │   ├── api.js           # Fetch wrapper with JWT auth
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
```

Copy `.env` template and fill in values:

```bash
DATABASE_URL=postgresql://user@localhost:5432/trustdesk

AI_PROVIDER=openai
OPENAI_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4.1-mini

# OR use Gemini
# AI_PROVIDER=gemini
# GEMINI_API_KEY=AIza...
# GEMINI_MODEL=gemini-2.5-flash

JWT_SECRET=your-secret-here

MAIL_USERNAME=you@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=you@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Available at:
- `http://localhost:8000` — API
- `http://localhost:8000/docs` — Swagger UI

On first startup the knowledge base is seeded automatically.

## 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

## 3. Main workflow

1. **Sign up** → verify OTP from email → log in.
2. Open **CRM** → add a customer → add an order for that customer.
3. Click **+ New Ticket** → select customer and order → describe the issue.
4. Click **Run triage** → see category, priority, escalation.
5. Click **Generate cited draft** → see AI reply grounded in policy with citation IDs.
6. If a sensitive action is recommended, it appears in **Pending approvals** → click **Approve**.
7. Approving with the same idempotency key a second time returns the existing result — no duplicate action.
8. Click **Run Evaluation** → see triage accuracy, citation coverage, unsafe-action blocking, escalation behavior.

## API reference

### Auth
- `POST /api/auth/signup` — create account, sends OTP
- `POST /api/auth/verify-otp` — verify OTP, returns JWT
- `POST /api/auth/resend-otp` — resend OTP
- `POST /api/auth/login` — login with username/password, returns JWT

### CRM
- `GET /api/crm/customers`
- `POST /api/crm/customers`
- `GET /api/crm/orders`
- `POST /api/crm/orders`

### Tickets
- `GET /api/tickets`
- `POST /api/tickets`
- `GET /api/tickets/{ticket_id}`
- `GET /api/tickets/{ticket_id}/context`
- `POST /api/tickets/{ticket_id}/triage`
- `POST /api/tickets/{ticket_id}/draft`
- `GET /api/tickets/{ticket_id}/trace`

### Actions
- `GET /api/actions/pending`
- `POST /api/actions/{action_id}/approve`

### Evaluation
- `POST /api/evaluations/run`
- `GET /api/evaluations/latest`

## Evaluation

CLI:

```bash
cd backend
python run_eval.py
```

The script authenticates automatically using `EVAL_USER` / `EVAL_PASS` env vars (defaults: `testuser` / `Test@1234`).

API:

```bash
curl -X POST http://localhost:8000/api/evaluations/run \
  -H "Authorization: Bearer <token>"
```

Report metrics:
- `triage_accuracy` — category + priority match
- `citation_coverage` — policy docs retrieved when required
- `unsafe_action_blocking` — guardrail triggered on adversarial cases
- `escalation_behavior` — escalation decision matches expected

## Design decisions

### Retrieval
TF-IDF with bigrams (`ngram_range=(1,2)`) is used intentionally — the brief allows any documented local substitute. `RetrievalService` is isolated and can be swapped for pgvector, Qdrant, or Elasticsearch without touching the rest of the codebase. `KB-ADVERSARIAL-001` is flagged `unsafe=True` and filtered before results are returned.

### AI adapter
`AIProvider` is an abstract base class. Three implementations exist: `MockAIProvider` (returns empty string, triggers template fallback), `OpenAICompatibleProvider` (works with OpenRouter or any OpenAI-compatible endpoint), and `GeminiProvider` (uses the `google-genai` SDK). Selected via `AI_PROVIDER` env var.

### Safety
Customer messages and retrieved documents are treated as untrusted input. Guardrails run before the AI call. The AI system prompt explicitly instructs the model not to treat policy documents as executable instructions. Sensitive tool actions (`start_refund_review`, `create_replacement_order`, `create_coupon`) are created as `pending` and require explicit human approval.

### Date handling
Return/warranty windows are evaluated using `ticket.created_at - order.ordered_at`, never the current date.

### Idempotency
Every tool call stores an idempotency key. The approval endpoint checks for an existing key before executing — reusing the same key returns the existing result.

### Non-blocking eval
The evaluation runner executes in a `ThreadPoolExecutor` so it does not block the FastAPI event loop during long runs.

### Auth
JWT with 8-hour expiry. Passwords hashed with `sha256_crypt` (bcrypt incompatible with Python 3.13). New accounts require OTP email verification before login is allowed.
