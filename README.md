# Playbook API

FastAPI backend for the Playbook Tauri client — AI chat powered by the Perplexity Sonar API, with Supabase JWT auth.

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- A [Perplexity API key](https://perplexity.ai/account/api)
- A Supabase project (for JWT verification), unless auth is disabled for local development

## Setup

```bash
# Install dependencies
poetry install

# Copy env template and fill in your values
cp .env.example .env
```

### Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `PERPLEXITY_API_KEY` | yes | — | Perplexity API key |
| `SUPABASE_URL` | when auth is on | `""` | Project URL, used to load JWKS from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` |
| `AUTH_DISABLED` | no | `false` | Skip JWT checks and treat every caller as `dev-user`. Do not enable in production. |
| `CORS_ORIGINS` | no | `["*"]` | JSON list of allowed origins, e.g. `["http://localhost:1420"]` |
| `RATE_LIMIT` | no | `5/minute` | SlowAPI limit for `POST /api/chat`, keyed by user id (or client IP when no user is set) |

With auth enabled, `SUPABASE_URL` must be set. The server loads signing keys at startup and will fail to start if that URL is empty or unreachable.

## Run

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

The server starts at `http://localhost:8000`.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/api/health` | no | Health check. Returns `{"status": "ok"}`. |
| POST | `/api/chat` | yes | Streaming AI chat via SSE. Rate limited (default `5/minute`). |

### Authentication

`POST /api/chat` expects a Supabase access token:

```
Authorization: Bearer <supabase-jwt>
```

The token is verified against the project's JWKS (`ES256`, `RS256`, or `HS256`) with audience `authenticated`. The user id is the JWT `sub` claim.

| Status | When |
| --- | --- |
| 403 | Missing token |
| 401 | Invalid or expired token |
| 429 | Rate limit exceeded |

Set `AUTH_DISABLED=true` to skip verification during local development. Requests are then attributed to `dev-user`.

### POST /api/chat

Request body:

```json
{
  "messages": [
    { "role": "user", "content": "What is Rust?" },
    {
      "role": "assistant",
      "content": "Rust is a systems programming language..."
    },
    { "role": "user", "content": "How does it compare to Go?" }
  ],
  "search": "fast"
}
```

- `messages` — conversation history. Only `user` and `assistant` roles are accepted, and the list must contain at least one message. The latest user message is last. A server-side system prompt is added before the request is sent to Perplexity.
- `search` — `"fast"` (default, Sonar with a small search context) or `"pro"` (Sonar Pro with a larger search context).

Response is an SSE stream of JSON events:

```
data: {"type": "content_delta", "content": "Go and Rust"}
data: {"type": "content_delta", "content": " are both modern"}
data: {"type": "done"}
```

On a streaming failure the stream emits an error event and then ends:

```
data: {"type": "error", "content": "An internal error occurred."}
```

Inline citation markers such as `[1]` are stripped from `content_delta` text before it is sent.
