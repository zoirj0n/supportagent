from __future__ import annotations
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .db import SessionLocal
from .router_accounts import router as accounts_router
from .router_admin import router as admin_router
from .services.oauth import router as oauth_router
from .services.poller import poll_once

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

tags_metadata = [
    {"name": "auth", "description": "Google OAuth connect/disconnect."},
    {"name": "accounts", "description": "Connected Gmail accounts."},
    {
        "name": "Admin / Data",
        "description": "Browse data tables for debugging/admin UI.",
    },
]

app = FastAPI(
    title="Support Email Agent API",
    version="1.0.0",
    description="Backend for the support email agent. Includes admin list endpoints.",
    openapi_tags=tags_metadata,
)

# CORS
frontend = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(accounts_router)
app.include_router(oauth_router)
app.include_router(admin_router)

DDL_STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS vector;",
    """
    CREATE TABLE IF NOT EXISTS app_user (
      id UUID PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS gmail_account (
      id TEXT PRIMARY KEY,
      user_id UUID REFERENCES app_user(id) ON DELETE CASCADE,
      gmail_address TEXT NOT NULL,
      access_token TEXT NOT NULL,
      refresh_token TEXT NOT NULL,
      token_expiry TIMESTAMPTZ NOT NULL,
      history_id TEXT,
      is_active BOOLEAN DEFAULT TRUE,
      scopes TEXT[],
      google_user_id TEXT,
      created_at TIMESTAMPTZ DEFAULT now(),
      disconnected_at TIMESTAMPTZ,
      UNIQUE (user_id, gmail_address)
    );
    """,
    # Patching existing DBs
    "ALTER TABLE gmail_account ADD COLUMN IF NOT EXISTS scopes TEXT[];",
    "ALTER TABLE gmail_account ADD COLUMN IF NOT EXISTS google_user_id TEXT;",
    "ALTER TABLE gmail_account ADD COLUMN IF NOT EXISTS disconnected_at TIMESTAMPTZ;",
    """
    CREATE TABLE IF NOT EXISTS orders (
      id TEXT PRIMARY KEY,
      user_email TEXT,
      status TEXT DEFAULT 'placed',
      created_at TIMESTAMPTZ DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS email_log (
      id BIGSERIAL PRIMARY KEY,
      gmail_account_id TEXT REFERENCES gmail_account(id) ON DELETE CASCADE,
      gmail_msg_id TEXT NOT NULL,
      thread_id TEXT,
      from_email TEXT,
      to_email TEXT,
      subject TEXT,
      snippet TEXT,
      received_at TIMESTAMPTZ,
      category TEXT,
      order_id TEXT,
      is_handled BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT now(),
      UNIQUE (gmail_msg_id)
    );
    """,
    "ALTER TABLE email_log ADD COLUMN IF NOT EXISTS is_handled BOOLEAN DEFAULT FALSE;",
    """
    CREATE TABLE IF NOT EXISTS refund_requests_not_found (
      id BIGSERIAL PRIMARY KEY,
      gmail_account_id TEXT REFERENCES gmail_account(id) ON DELETE CASCADE,
      thread_id TEXT,
      email_msg_id TEXT,
      provided_text TEXT,
      created_at TIMESTAMPTZ DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS unhandled_emails (
      id BIGSERIAL PRIMARY KEY,
      gmail_account_id TEXT REFERENCES gmail_account(id) ON DELETE CASCADE,
      email_msg_id TEXT,
      thread_id TEXT,
      reason TEXT,
      importance TEXT,
      created_at TIMESTAMPTZ DEFAULT now()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS rag_documents (
      id BIGSERIAL PRIMARY KEY,
      title TEXT,
      content TEXT NOT NULL,
      tags TEXT[],
      created_at TIMESTAMPTZ DEFAULT now()
    );
    """,
    """
CREATE TABLE IF NOT EXISTS rag_chunks (
  id BIGSERIAL PRIMARY KEY,
  doc_id BIGINT REFERENCES rag_documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(384),
  tags TEXT[],
  chunk_index INT,
  created_at TIMESTAMPTZ DEFAULT now()
);
""",
    "ALTER TABLE rag_chunks ALTER COLUMN embedding TYPE vector(384);",
    # Helpful indexes for common queries
    "CREATE INDEX IF NOT EXISTS idx_email_log_thread_cat_order ON email_log(thread_id, category, order_id);",
    "CREATE INDEX IF NOT EXISTS idx_refund_nf_thread_text ON refund_requests_not_found(thread_id, provided_text);",
    #  Initial admin user
    """
    INSERT INTO app_user (id, email)
      VALUES ('00000000-0000-0000-0000-000000000001', 'owner@example.com')
      ON CONFLICT DO NOTHING;
    """,
    # Order
    """
    INSERT INTO orders (id, user_email, status)
    VALUES ('ORD-12345','customer@example.com','placed')
    ON CONFLICT DO NOTHING;
    """,
    # RAG doc + chunk for refund policy
    """
    INSERT INTO rag_documents (title, content, tags)
    SELECT
      'Refund policy',
      'Refunds are processed within 3 business days after approval. Include your ORDER ID (e.g., ORD-34565).',
      ARRAY['policy','refund']
    WHERE NOT EXISTS (SELECT 1 FROM rag_documents WHERE title = 'Refund policy');
    """,
    """
    INSERT INTO rag_chunks (doc_id, content, embedding, tags, chunk_index)
    SELECT d.id, d.content, NULL, d.tags, 0
    FROM rag_documents d
    WHERE d.title = 'Refund policy'
      AND NOT EXISTS (
        SELECT 1 FROM rag_chunks c WHERE c.doc_id = d.id AND c.chunk_index = 0
      );
    """,
]


async def init_db():
    # Wait for DB to be ready; then run DDLs
    for attempt in range(30):
        try:
            async with SessionLocal() as session:
                for stmt in DDL_STATEMENTS:
                    await session.execute(text(stmt))
                await session.commit()
            log.info("DB initialized (DDL + seeds).")
            return
        except Exception as e:
            if attempt == 0:
                log.warning("Waiting for DB to be ready…")
            log.debug("init_db attempt %s failed: %r", attempt + 1, e)
            await asyncio.sleep(2)
    log.error("DB initialization failed after retries.")


async def _poll_loop():
    await asyncio.sleep(3)
    log.info("Starting Gmail poller loop.")
    while True:
        try:
            async with SessionLocal() as session:
                await poll_once(session)
        except Exception as e:
            log.exception("Poller iteration failed: %r", e)
            await asyncio.sleep(5)
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)


@app.on_event("startup")
async def on_startup():
    await init_db()
    asyncio.create_task(_poll_loop())


@app.get("/")
async def root():
    return {"status": "ok", "poll_every_sec": settings.POLL_INTERVAL_SECONDS}
