from fastapi import FastAPI, HTTPException, Path, Depends
from pydantic import BaseModel
from db import get_db
from models import Task, User
from datetime import datetime
from bson.objectid import ObjectId
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
from dotenv import load_dotenv
from task_service.ai_estimator import estimate_time
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

load_dotenv()

app = FastAPI()

# Allow frontend on localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # ✅ your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

@app.post("/register")
def register_user(user: User):
    db = get_db()
    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["created_at"] = datetime.utcnow()
    db.users.insert_one(user_dict)
    return {"message": "User registered successfully"}

@app.post("/token")
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": user["email"], "token_type": "bearer"}

@app.get("/tasks")
def get_tasks():
    db = get_db()
    tasks = db.tasks.find()
    return [
        {
            "id": str(task["_id"]),
            "description": task["description"],
            "estimated_minutes": task["estimated_minutes"],
            "created_at": task["created_at"],
            "completed": task.get("completed", False),
            "due_date": task.get("due_date"),  # 🆕 Include due_date
        } for task in tasks
    ]

@app.post("/tasks")
def create_task(task: Task):
    print("Received task from frontend:", task)
    db = get_db()
    task_dict = task.dict()

    if not task_dict.get("estimated_minutes"):
        task_dict["estimated_minutes"] = estimate_time(task_dict["description"])

    task_dict["created_at"] = datetime.utcnow()
    result = db.tasks.insert_one(task_dict)
    return {
        "id": str(result.inserted_id),
        "description": task.description,
        "estimated_minutes": task_dict["estimated_minutes"],
        "due_date": task_dict["due_date"],
        "completed": task_dict.get("completed", False),
        "created_at": task_dict["created_at"]
    }

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str = Path(..., description="The ID of the task to delete")):
    db = get_db()
    result = db.tasks.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

@app.patch("/tasks/{task_id}")
def toggle_task(task_id: str = Path(..., description="The ID of the task to toggle")):
    db = get_db()
    print("Toggling task ID:", task_id)  # Log the task ID for debugging

    try:
        object_id = ObjectId(task_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    task = db.tasks.find_one({"_id": object_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updated = db.tasks.find_one_and_update(
        {"_id": object_id},
        {"$set": {"completed": not task.get("completed", False)}},
        return_document=True
    )
    updated["id"] = str(updated["_id"])
    return updated
