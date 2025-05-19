from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class Task(BaseModel):
    description: str
    estimated_minutes: int = 0
    completed: bool = False
    due_date: datetime

class User(BaseModel):
    email: EmailStr
    password: str
    created_at: Optional[datetime] = None
