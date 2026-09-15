# Architecture

## Overview

A single FastAPI service exposes a REST API and also serves a small static
frontend, so there's one deployable unit for the whole demo. Data model:

```
User 1---* Project 1---* Message
              1---* ProjectFile
```

A "project" doubles as the agent: it holds the system prompt, and its
`Message` rows are the conversation history sent back to the model on every
turn, scoped by `project_id`.

## Request flow (chat)

1. Client sends `POST /projects/{id}/chat` with a bearer JWT and a message.
2. `get_current_user` decodes the JWT and loads the `User`.
3. `get_owned_project` checks the project exists **and** belongs to that
   user — this single check is reused by the chat and files routers so
   authorization logic lives in one place.
4. The user's message is persisted immediately (so it's never lost even if
   the LLM call fails), then the full message history for that project is
   sent to OpenAI's Responses API with the project's `system_prompt` as
   `instructions`.
5. The assistant's reply is persisted and returned.

## Design decisions, mapped to the non-functional requirements

**Security**
- Passwords are hashed with bcrypt (`passlib`), never stored in plaintext.
- Auth is stateless JWT (HS256, signed with a server-side `SECRET_KEY`,
  24h expiry) — no server-side session store needed.
- Every project-scoped route re-checks `project.user_id == user.id`, so one
  user can never read or chat with another user's agent, even by guessing
  an ID.
- CORS is wide open in this demo (`allow_origins=["*"]`) purely for local
  convenience; the one-line fix for production is scoping it to the actual
  frontend origin.

**Scalability**
- The API is stateless (JWT, no in-memory session), so it can be run behind
  a load balancer with multiple replicas without any sticky-session tricks.
- Chat calls are `async` end-to-end (`AsyncOpenAI`), so one worker can hold
  many concurrent in-flight LLM calls without blocking on I/O.
- SQLite is used here purely for zero-setup local/demo simplicity.
  `DATABASE_URL` is the only thing that changes to move to Postgres — the
  ORM layer (SQLAlchemy) doesn't care.

**Extensibility**
- Routers are split by concern (`auth`, `projects`, `chat`, `files`) and
  wired in `main.py`; adding a new capability (e.g. an `/analytics` router,
  or a `/projects/{id}/share` endpoint) is a new file plus one `include_router`
  line, with no changes to existing modules.
- `Project.system_prompt` is a plain field today; multi-prompt-per-project
  or prompt versioning is a natural extension (a `Prompt` table with a
  foreign key to `Project`) without touching the auth or chat call path.
- The chat route talks to the LLM through a single function
  (`client.responses.create(...)`); swapping providers (e.g. OpenRouter) or
  adding retries/fallback means editing this one call site.

**Performance**
- Message history is loaded once per chat turn and passed directly as
  `input` to the Responses API — no redundant round trips.
- Static frontend files are served directly by FastAPI's `StaticFiles`, so
  there's no separate frontend server/build pipeline adding latency or
  deploy complexity for a project this size.

**Reliability**
- The user's message is committed to the DB *before* the LLM call, so a
  transient OpenAI outage never loses what the user typed.
- OpenAI errors are caught explicitly (`OpenAIError`) and surfaced as a
  clean `502` with a message, instead of a raw 500 stack trace.
- SQLAlchemy sessions are request-scoped via a `Depends(get_db)` generator
  that always closes the connection, even on error.

## Known simplifications (intentional, given "minimal")

- No refresh tokens — a single long-lived access token. Adding refresh
  tokens would mean a `RefreshToken` table and a `/auth/refresh` route.
- No rate limiting on `/auth/login` or `/chat` — would add a simple
  in-memory or Redis-backed limiter per user/IP.
- No streaming responses — the chat call awaits the full completion before
  replying. Swapping to SSE/streaming is a change to `chat.py` and the
  `fetch` call in `app.js` only; nothing else moves.
- Frontend is plain HTML/JS with no framework, to keep the deployable
  surface area to "one Python service, no build step" — trivial to demo
  and to modify live.
