from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import init_db
from backend.routes.chat import router as chat_router
from backend.routes.students import router as student_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database on startup."""
    init_db()
    yield


app = FastAPI(title="MentorMind AI Backend", lifespan=lifespan)

# CORS middleware for Streamlit ↔ FastAPI communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(student_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to MentorMind AI API"}
