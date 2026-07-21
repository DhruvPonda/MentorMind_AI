# MentorMind AI

An adaptive AI Tutor with **long-term memory** and **multi-agent architecture**, powered by LangGraph, FastAPI, Streamlit, ChromaDB, and Groq (Llama 3.1).

MentorMind uses 5 specialized LLM agents orchestrated via LangGraph to provide personalized tutoring, adaptive quizzes, learning path recommendations, and progress reports.

## Multi-Agent Architecture

```
Student → Streamlit Chat UI
  │
  POST /chat (JWT authenticated)
  │
  ┌──────────────────────────────────────────┐
  │         LangGraph StateGraph             │
  │                                          │
  │  retrieve_context (SQLite + ChromaDB)    │
  │         ↓                                │
  │  Supervisor Agent (intent routing)       │
  │         ↓                                │
  │  ┌──────┼──────────┬──────────┐          │
  │  │      │          │          │          │
  │  chat   quiz     report     plan         │
  │  │      │          │          │          │
  │  Tutor  Assessment Report   Planner      │
  │  ↓      ↓          ↓                     │
  │  Assessment                              │
  │  ↓                                       │
  │  Planner                                 │
  │  ↓                                       │
  │  store_memory (ChromaDB + SQLite)        │
  └──────────────────────────────────────────┘
  │
  Response (answer + topic + mastery + next_topics + quiz/report)
```

## Agents

| Agent | Responsibility |
|---|---|
| **Supervisor** | Classifies intent → routes to `chat`, `quiz`, `report`, or `plan` |
| **Tutor** | Generates personalized explanations using student context + memory |
| **Assessment** | Evaluates understanding (chat) or generates quizzes (quiz mode) |
| **Planner** | Recommends next topics using a prerequisite knowledge graph |
| **Report** | Generates teacher/parent-readable progress summaries |

## Key Features

- **LangGraph StateGraph**: All agents share a `MentorState` TypedDict with conditional routing
- **Long-Term Memory**: ChromaDB stores every conversation as a vector embedding
- **Mastery Tracking**: Per-topic scores using exponential moving average in SQLite
- **Prerequisite Graph**: 25-topic knowledge graph for intelligent learning path recommendations
- **Adaptive Quizzes**: Quiz difficulty adjusts based on student mastery level
- **JWT Authentication**: Email + password with bcrypt hashing
- **Hybrid Topic Detection**: Keyword matching with LLM fallback

## Project Structure

```
backend/
├── agents/                        # LangGraph multi-agent system
│   ├── mentor_state.py            # Shared MentorState TypedDict
│   ├── mentor_graph.py            # StateGraph assembly + run_mentor_graph()
│   ├── supervisor_agent.py        # Intent classification + routing
│   ├── tutor_agent.py             # Personalized teaching
│   ├── assessment_agent.py        # Understanding eval + quiz generation
│   ├── planner_agent.py           # Prerequisite-based recommendations
│   └── report_agent.py            # Progress report generation
├── services/                      # Business logic utilities
│   ├── auth_service.py            # JWT + bcrypt authentication
│   ├── student_profile.py         # Student profile & mastery CRUD
│   ├── topic_detector.py          # Hybrid keyword/LLM topic detection
│   ├── assessment_agent.py        # Legacy assessment (kept for compat)
│   └── memory_service.py          # Memory retrieval/storage
├── memory/
│   └── chroma_manager.py          # ChromaDB PersistentClient
├── llm/
│   └── groq_client.py             # Legacy LLM client (kept for compat)
├── models/
│   └── schemas.py                 # Pydantic models
├── routes/
│   ├── chat.py                    # /chat endpoint (calls LangGraph)
│   └── students.py                # Auth & profile endpoints
├── database.py                    # SQLite setup
└── main.py                        # FastAPI app
frontend/
└── app.py                         # Streamlit UI with quiz, report, planner
```

## Setup Instructions

1. Clone the repository and navigate to the root directory.
2. Create and activate a virtual environment (recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your `GROQ_API_KEY` and optionally change `JWT_SECRET_KEY`.

## Running the Project

### 1. Start the FastAPI Backend
```bash
uvicorn backend.main:app --reload
```
The API will be available at http://127.0.0.1:8000.

### 2. Start the Streamlit Frontend
```bash
streamlit run frontend/app.py
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/students/register` | No | Register a new student |
| POST | `/students/login` | No | Login and get JWT token |
| GET | `/students/me` | JWT | Get full student profile |
| GET | `/students/me/mastery` | JWT | Get mastery score breakdown |
| POST | `/chat` | JWT | Multi-agent chat (auto-routes to tutor/quiz/report/plan) |

## Example Interactions

| You say | Agent pipeline | You get |
|---|---|---|
| "What is recursion?" | Supervisor → Tutor → Assessment → Planner → Store | Explanation + mastery update + next topics |
| "Quiz me on recursion" | Supervisor → Assessment → Planner → Store | 3 quiz questions + learning path |
| "Generate my progress report" | Supervisor → Report | Markdown progress report |
| "What should I study next?" | Supervisor → Planner → Store | 3 recommended topics with reasoning |

## Future Extensions

The modular architecture supports:

- **RAG**: Add document ingestion to ChromaDB for course material
- **IndicTrans2**: Add multilingual support via translation agents
- **Voice**: Add speech-to-text/text-to-speech agent nodes
- **Teacher Dashboard**: Query the report agent for class-wide analytics
- **Bayesian Knowledge Tracing**: Replace EMA mastery with BKT in student_profile.py
