# Support Agent — HTTP API

FastAPI base URL: `http://localhost:8000`

## Auth / OAuth
### GET `/auth/google/start`
Starts Google OAuth. Redirects to Google.

### GET `/auth/google/callback`
Handles Google callback, persists tokens, then redirects to the frontend (`FRONTEND_URL`).

## Accounts
### GET `/accounts/`
List connected accounts (brief).
- 200 → `[{ id, gmail_address, is_active, connected_at, disconnected_at, token_expiry, history_id }]`

### GET `/accounts/{id}`
Account details.
- 200 → `{ id, gmail_address, is_active, connected_at, disconnected_at, token_expiry, history_id, google_user_id, scopes }`
- 404 → `{"detail":"Account not found"}`

### DELETE `/accounts/{id}`
Disconnect an account (sets `is_active=false`, `disconnected_at=now()`).

## Admin / Data
> All endpoints are read-only with pagination. Response shape:
> ```json
> { "items": [...], "meta": { "total": 123, "limit": 50, "offset": 0 } }
> ```

### GET `/admin/accounts`
Params:
- `limit` (1..500, default 50), `offset` (default 0), `is_active` (bool)

### GET `/admin/orders`
Params: `status`, `user_email`, `q` (search in id/email), `limit`, `offset`

### GET `/admin/email-logs`
Params:
- `category` (`refund|question|other`), `thread_id`, `order_id`
- `handled` (bool)
- `since` / `until` (ISO timestamp)
- `q` (search in subject/snippet)
- `limit`, `offset`

### GET `/admin/refund-not-found`
Params: `thread_id`, `q` (search in provided_text), `limit`, `offset`

### GET `/admin/unhandled-emails`
Params: `reason`, `importance`, `limit`, `offset`

### GET `/admin/rag/documents`
Params: `tag`, `q` (search in title/content), `limit`, `offset`

### GET `/admin/rag/chunks`
Params: `doc_id`, `tag`, `q` (search in content), `limit`, `offset`
