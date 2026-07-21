from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List


# ─── Authentication ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student_id: str
    name: str


# ─── Chat ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    topic: str
    mastery_scores: Dict[str, float]
    next_topics: List[str] = []
    quiz: Optional[List[Dict]] = None
    report: Optional[str] = None
    learning_path: List[Dict] = []


# ─── Quiz ────────────────────────────────────────────────────────────

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str


# ─── Student Profile ────────────────────────────────────────────────

class MasteryScoreResponse(BaseModel):
    topic: str
    score: float
    question_count: int
    correct_count: int


class StudentProfileResponse(BaseModel):
    student_id: str
    name: str
    email: str
    created_at: str
    last_active: str
    mastery_scores: List[MasteryScoreResponse]
    strengths: List[str]
    weaknesses: List[str]


# ─── Assessment ──────────────────────────────────────────────────────

class AssessmentResult(BaseModel):
    understanding_score: float
    confidence: float
    misconceptions: List[str]
    recommendation: str
