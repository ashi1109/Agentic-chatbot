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

Open the link in the output ,register a user, create a project, start
chatting.

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

All `/projects/*` routes require `Authorization: Bearer <token>` and only
ever operate on projects owned by the caller.

## Deploying a public demo

1. Push this repo to GitHub.
2. New "Web Service" → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables `SECRET_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL`.
   

