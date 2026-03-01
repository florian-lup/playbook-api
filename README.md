# Playbook Server

FastAPI backend for the Playbook Electron client — AI chat powered by Perplexity Sonar API.

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- A [Perplexity API key](https://perplexity.ai/account/api)

## Setup

```bash
# Install dependencies
poetry install

# Copy env template and fill in your API key
cp .env.example .env
```

Edit `.env` and set your `PERPLEXITY_API_KEY`.

## Run

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

The server starts at `http://localhost:8000`.

## Endpoints

| Method | Path            | Description                        |
|--------|-----------------|------------------------------------|
| GET    | `/api/health`   | Health check                       |
| POST   | `/api/chat`     | Streaming AI chat via SSE          |

### POST /api/chat

Request body:

```json
{
  "messages": [
    {"role": "user", "content": "What is Rust?"},
    {"role": "assistant", "content": "Rust is a systems programming language..."},
    {"role": "user", "content": "How does it compare to Go?"}
  ],
  "search": "fast"
}
```

- `messages` — conversation history (user/assistant roles only). Latest user message is last.
- `search` — `"fast"` (default, uses Sonar) or `"pro"` (uses Sonar Pro with deeper search).

Response is an SSE stream of JSON events:

```
data: {"type": "content_delta", "content": "Go and Rust"}
data: {"type": "content_delta", "content": " are both modern"}
data: {"type": "done"}
```
