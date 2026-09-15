# Minimal Chatbot Platform

A minimal multi-tenant chatbot platform: register/login, create projects
("agents") each with their own system prompt and chat history, talk to them
via the OpenAI Responses API, and optionally attach files via the OpenAI
Files API.

Stack: **FastAPI + SQLite (SQLAlchemy) + JWT auth + vanilla HTML/JS frontend**
(no build step — the whole frontend is 3 static files served by FastAPI).

## Running locally

```bash
# 1. Create a virtualenv
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# edit .env and set SECRET_KEY + OPENAI_API_KEY

# 4. Run
uvicorn app.main:app --reload
```

Open **http://localhost:8000** — register a user, create a project, start
chatting. Interactive API docs are at **http://localhost:8000/docs**.

## Project layout

```
app/
  main.py            FastAPI app, router wiring, static file mount
  config.py          env-driven settings
  database.py        SQLAlchemy engine/session
  models.py          User, Project, Message, ProjectFile
  schemas.py         Pydantic request/response models
  auth.py            password hashing, JWT issue/verify, current-user dep
  routers/
    auth.py          POST /auth/register, /auth/login, GET /auth/me
    projects.py      CRUD for projects + GET messages
    chat.py          POST /projects/{id}/chat  -> OpenAI Responses API
    files.py         POST/GET /projects/{id}/files -> OpenAI Files API
  static/            index.html / app.js / style.css (plain JS frontend)
```

## API summary

| Method | Path                          | Description                          |
|--------|-------------------------------|---------------------------------------|
| POST   | `/auth/register`              | Create a user                         |
| POST   | `/auth/login`                 | Get a JWT (form fields: username, password) |
| GET    | `/auth/me`                    | Current user info                     |
| POST   | `/projects`                   | Create a project/agent                |
| GET    | `/projects`                   | List my projects                      |
| GET    | `/projects/{id}`              | Get one project                       |
| PUT    | `/projects/{id}`              | Update name / description / system prompt |
| DELETE | `/projects/{id}`              | Delete a project                      |
| GET    | `/projects/{id}/messages`     | Chat history                          |
| POST   | `/projects/{id}/chat`         | Send a message, get the reply         |
| POST   | `/projects/{id}/files`        | Upload a file (OpenAI Files API)      |
| GET    | `/projects/{id}/files`        | List uploaded files                   |

All `/projects/*` routes require `Authorization: Bearer <token>` and only
ever operate on projects owned by the caller.

## Deploying a public demo

Any host that runs a Python web service works (Render, Railway, Fly.io).
Example for **Render**:

1. Push this repo to GitHub.
2. New "Web Service" → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables `SECRET_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL`.
6. (Optional) attach a persistent disk if you want the SQLite file to
   survive restarts; otherwise swap `DATABASE_URL` for a managed Postgres
   instance — no code changes needed, SQLAlchemy handles both.

See `ARCHITECTURE.md` for design rationale and how to extend this.
