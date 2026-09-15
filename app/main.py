from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, chat, files, projects

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Minimal Chatbot Platform")

# CORS is wide open here for demo convenience; scope this to your frontend's
# origin before shipping anything real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(chat.router)
app.include_router(files.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve the minimal static frontend last so API routes above take precedence.
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
