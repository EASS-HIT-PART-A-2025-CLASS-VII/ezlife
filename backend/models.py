from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

class TaskBreakdown(BaseModel):
    day: Optional[str] = None
    date: Optional[str] = None
    hours: Optional[float] = None
    step: Optional[str] = None
    summary: Optional[str] = None
    percentage: Optional[int] = None
    completed: bool = False

class Task(BaseModel):
    description: str
    estimated_minutes: int = 0
    completed: bool = False
    due_date: Optional[datetime] = None
    days_per_week: Optional[int] = None
    hours_per_day: Optional[float] = None
    breakdown: Optional[List[Dict]] = None  
    progress: Optional[float] = 0  

class User(BaseModel):
    email: EmailStr
    password: str
    created_at: Optional[datetime] = None
    
class Activity(BaseModel):
    id: Optional[str] = None
    name: str
    time: str
    date: str
    user_id: Optional[str] = None
