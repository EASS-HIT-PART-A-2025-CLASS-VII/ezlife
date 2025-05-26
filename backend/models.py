from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

class TaskBreakdown(BaseModel):
    day: str
    date: Optional[str] = None
    hours: float
    summary: Optional[str] = None
    completed: bool = False

class Task(BaseModel):
    description: str
    estimated_minutes: int = 0
    completed: bool = False
    due_date: Optional[datetime] = None
    days_per_week: Optional[int] = None
    hours_per_day: Optional[float] = None
    breakdown: Optional[List[TaskBreakdown]] = None
    progress: Optional[float] = 0  # Percentage of completion (0-100)

class User(BaseModel):
    email: EmailStr
    password: str
    created_at: Optional[datetime] = None
