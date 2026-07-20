import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

from backend.database import get_db

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mentormind-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(student_id: str, email: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": student_id,
        "email": email,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def register_student(name: str, email: str, password: str) -> dict:
    """Register a new student and return an access token."""
    student_id = str(uuid.uuid4())
    password_hash = hash_password(password)

    with get_db() as conn:
        cursor = conn.cursor()
        # Check if email already exists
        cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        cursor.execute(
            "INSERT INTO students (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (student_id, name, email, password_hash)
        )

    token = create_access_token(student_id, email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "student_id": student_id,
        "name": name
    }


def login_student(email: str, password: str) -> dict:
    """Authenticate a student and return an access token."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
        student = cursor.fetchone()

    if not student or not verify_password(password, student["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last_active
    with get_db() as conn:
        conn.execute(
            "UPDATE students SET last_active = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), student["id"])
        )

    token = create_access_token(student["id"], email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "student_id": student["id"],
        "name": student["name"]
    }


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """FastAPI dependency: extract and validate the current student from JWT."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get("sub")
        if student_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no subject"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email FROM students WHERE id = ?", (student_id,)
        )
        student = cursor.fetchone()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    return {
        "student_id": student["id"],
        "name": student["name"],
        "email": student["email"]
    }
