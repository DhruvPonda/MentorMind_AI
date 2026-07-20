from fastapi import APIRouter, Depends, HTTPException, status

from backend.models.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    StudentProfileResponse,
    MasteryScoreResponse,
)
from backend.services.auth_service import (
    register_student,
    login_student,
    get_current_student,
)
from backend.services.student_profile import get_student_profile

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new student account."""
    result = register_student(request.name, request.email, request.password)
    return TokenResponse(**result)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate and receive a JWT token."""
    result = login_student(request.email, request.password)
    return TokenResponse(**result)


@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_student: dict = Depends(get_current_student),
):
    """Get the authenticated student's full profile."""
    profile = get_student_profile(current_student["student_id"])
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    mastery_list = [
        MasteryScoreResponse(
            topic=topic,
            score=info["score"],
            question_count=info["question_count"],
            correct_count=info["correct_count"],
        )
        for topic, info in profile["mastery_scores"].items()
    ]

    return StudentProfileResponse(
        student_id=profile["student_id"],
        name=profile["name"],
        email=profile["email"],
        created_at=profile["created_at"] or "",
        last_active=profile["last_active"] or "",
        mastery_scores=mastery_list,
        strengths=profile["strengths"],
        weaknesses=profile["weaknesses"],
    )


@router.get("/me/mastery")
async def get_my_mastery(
    current_student: dict = Depends(get_current_student),
):
    """Get the authenticated student's mastery score breakdown."""
    profile = get_student_profile(current_student["student_id"])
    if not profile:
        return {"mastery_scores": {}}
    return {"mastery_scores": profile["mastery_scores"]}
