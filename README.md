# MentorMind AI

An adaptive AI Tutor with **long-term memory**, powered by FastAPI, Streamlit, ChromaDB, and the Groq API (Llama 3.1).

MentorMind remembers every conversation, tracks student mastery across topics, and adapts its teaching style based on each student's strengths and weaknesses.

## Architecture

```
Student → Streamlit Chat UI (Login / Register)
  │
  ├── POST /students/register    → Create account (bcrypt + JWT)
  ├── POST /students/login       → Authenticate (JWT token)
  ├── GET  /students/me          → Full profile + mastery scores
  └── POST /chat                 → Memory-aware tutoring pipeline
        │
        ├── 1. Retrieve student profile (SQLite)
        ├── 2. Retrieve similar past conversations (ChromaDB)
        ├── 3. Build context-rich prompt → LLM call (Groq)
        ├── 4. Detect topic (hybrid: keyword + LLM fallback)
        ├── 5. Assess understanding (dedicated LLM agent)
        ├── 6. Update mastery scores (SQLite, EMA)
        ├── 7. Store conversation memory (ChromaDB)
        └── 8. Return answer + topic + mastery scores
```

## Key Features

- **Long-Term Memory**: Every conversation is stored as a vector embedding in ChromaDB and retrieved semantically for future context.
- **Student Authentication**: Email + password with bcrypt hashing and JWT tokens.
- **Mastery Tracking**: Per-topic mastery scores using exponential moving average, tracked in SQLite.
- **Adaptive Tutoring**: The LLM prompt dynamically incorporates student strengths, weaknesses, and mastery scores.
- **Hybrid Topic Detection**: Fast keyword matching with LLM fallback for ambiguous questions.
- **Assessment Agent**: Dedicated LLM call evaluates student understanding with structured JSON output.
- **Mastery Dashboard**: Visual progress bars in the Streamlit sidebar.

## Project Structure

```
backend/
├── main.py                    # FastAPI app with CORS & lifespan
├── database.py                # SQLite setup (students, mastery_scores)
├── memory/
│   ├── __init__.py
│   └── chroma_manager.py      # ChromaDB PersistentClient operations
├── services/
│   ├── __init__.py
│   ├── auth_service.py        # JWT + bcrypt authentication
│   ├── student_profile.py     # Student profile & mastery CRUD
│   ├── topic_detector.py      # Hybrid keyword/LLM topic detection
│   ├── assessment_agent.py    # LLM-based understanding assessment
│   └── memory_service.py      # Memory retrieval/storage orchestration
├── llm/
│   └── groq_client.py         # Context-aware LLM client
├── models/
│   └── schemas.py             # Pydantic request/response models
└── routes/
    ├── chat.py                # Memory pipeline chat endpoint
    └── students.py            # Auth & profile endpoints
frontend/
└── app.py                     # Streamlit UI with login & mastery dashboard
```

## Setup Instructions

1. Clone the repository and navigate to the root directory.
2. Create and activate a virtual environment (optional but recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to include your `GROQ_API_KEY` and optionally change `JWT_SECRET_KEY`.

## Running the Project

You will need two terminal windows to run both the backend and frontend simultaneously.

### 1. Start the FastAPI Backend
```bash
uvicorn backend.main:app --reload
```
The API will be available at http://127.0.0.1:8000.

> **Note**: On first run, ChromaDB will download the embedding model (~79MB). This is a one-time download.

### 2. Start the Streamlit Frontend
```bash
streamlit run frontend/app.py
```
The Streamlit app will open in your browser. Register an account and start chatting!

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/students/register` | No | Register a new student |
| POST | `/students/login` | No | Login and get JWT token |
| GET | `/students/me` | JWT | Get full student profile |
| GET | `/students/me/mastery` | JWT | Get mastery score breakdown |
| POST | `/chat` | JWT | Send a question (full memory pipeline) |

## Future Extensions

The modular architecture is designed for easy extension:

- **RAG**: Add document ingestion to ChromaDB for course material retrieval
- **Multi-Agent Systems**: Assessment agent is already a separate LLM call
- **Adaptive Quizzes**: Use mastery scores to generate targeted quiz questions
- **Teacher Reports**: Query mastery_scores table for class-wide analytics
- **Google Login / Role-Based Access**: Auth service supports extension
