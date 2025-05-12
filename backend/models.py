from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class Task(BaseModel):
    description: str
    estimated_minutes: Optional[int] = None
    completed: bool = False  # ✅ new field
    due_date: Optional[datetime] = None  # 🆕 New field

class User(BaseModel):
    email: EmailStr
    password: str
    created_at: Optional[datetime] = None
