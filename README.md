# Support Email Agent

A minimal customer-support email agent that connects to Gmail, classifies incoming emails, answers questions with RAG, and handles refund requests with a small workflow + logging.

**Tech:** FastAPI (Python 3.11), SQLAlchemy 2 (async), PostgreSQL + pgvector, OpenRouter (chat via OpenAI SDK), SentenceTransformers (local embeddings), Vite + React.

---

## Features

- Connect/disconnect **multiple Gmail accounts** (OAuth 2.0; scope: `gmail.modify`, `openid`, `email`, `profile`)
- Background **poller** reads unread mail, replies, then marks handled messages read
- **Classification** → `refund` | `question` | `other`
- **Refund flow**
  - Ask for Order ID if missing
  - If provided:
    - **found** in DB → mark `refund_requested`, reply “processed in 3 business days”
    - **not found** → reply “invalid ID”
    - **same invalid ID again** → log into `refund_requests_not_found`
    - **non-ID follow-up after invalid** → also log into `refund_requests_not_found`
  - Duplicate logs de-duped per `(thread_id, provided_text)`
- **Questions (RAG)**
  - Chunk + embed docs (MiniLM 384-dim) into **pgvector**
  - Retrieve top chunks and answer via **OpenRouter** chat
  - If no good context → **escalate** and log to `unhandled_emails` with **high** importance
- **Other / Nonsense** → scored importance + stored in `unhandled_emails`
- **Admin APIs** to browse orders, email log, unhandled, refund-not-found, RAG docs

---

## Prereqs

- Docker & Docker Compose
- Google Cloud project (OAuth 2.0 **Web** client)
- OpenRouter API key → https://openrouter.ai/

---

## Configure Google OAuth

Create an OAuth client and set:

- **Authorized redirect URIs**
  `http://localhost:8000/auth/google/callback`

- **Authorized JavaScript origins**
  `http://localhost:5173`

Scopes requested:
`https://www.googleapis.com/auth/gmail.modify openid email profile`

---

## Backend environment (`backend/.env`)

```env
# DB / CORS
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres
FRONTEND_URL=http://localhost:5173

# Google OAuth
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback

# OpenRouter chat (OpenAI SDK → OpenRouter base)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_APP_NAME=Support Agent
OPENROUTER_SITE_URL=http://localhost:5173
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Poller & Embeddings
POLL_INTERVAL_SECONDS=30
EMBED_DIM=384
```
---
## Run

```
docker compose up --build
```
