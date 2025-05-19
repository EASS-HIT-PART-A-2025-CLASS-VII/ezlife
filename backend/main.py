from fastapi import FastAPI, HTTPException, Depends, Form, Path
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId

load_dotenv()

class Task(BaseModel):
    description: str
    completed: bool = False

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["task_management"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(f"Authenticating user with token: {token}")
    user = db.users.find_one({"email": token})
    if not user:
        print(f"User not found for token: {token}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    print(f"User authenticated: {user['email']}")
    return user

# Create test user if it doesn't exist
def create_test_user():
    test_email = "test@test.com"
    test_password = "12345678"
    if not db.users.find_one({"email": test_email}):
        hashed_password = hash_password(test_password)
        db.users.insert_one({"email": test_email, "password": hashed_password})
        print(f"Created test user: {test_email}")

# Create test task function
def create_test_task():
    if db.tasks.count_documents({}) == 0:
        task = {
            "description": "Welcome to EZlife! This is a sample task.",
            "completed": False,
            "created_at": datetime.utcnow()
        }
        db.tasks.insert_one(task)
        print("Created test task")

# Create test user and task on startup
create_test_user()
create_test_task()

@app.post("/register")
def register_user(email: str = Form(...), password: str = Form(...)):
    if db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(password)
    db.users.insert_one({"email": email, "password": hashed_password})
    return {"message": "User registered successfully"}

@app.post("/token")
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt: {form_data.username}")
    user = db.users.find_one({"email": form_data.username})
    if not user:
        print(f"User not found: {form_data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(form_data.password, user["password"]):
        print(f"Invalid password for user: {form_data.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    print(f"Login successful: {form_data.username}")
    return {"access_token": user["email"], "token_type": "bearer"}

# Tasks API
@app.get("/tasks")
async def get_tasks(current_user: dict = Depends(get_current_user)):
    # You can filter by user_id if you want tasks to be user-specific
    # tasks = db.tasks.find({"user_id": current_user["_id"]})
    try:
        tasks = list(db.tasks.find())
        print(f"Found {len(tasks)} tasks")
        task_list = []
        
        for task in tasks:
            task_item = {
                "id": str(task["_id"]),
                "description": task["description"],
                "completed": task.get("completed", False),
                "estimated_minutes": task.get("estimated_minutes", 0),
                "created_at": task.get("created_at", datetime.utcnow()).isoformat() if "created_at" in task else None
            }
            
            # Include due date if available
            if "due_date" in task:
                task_item["due_date"] = task["due_date"].isoformat()
            
            task_list.append(task_item)
            
        return task_list
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

@app.post("/tasks")
async def create_task(task: Task, current_user: dict = Depends(get_current_user)):
    from task_service.ai_estimator import estimate_time
    import datetime as dt
    
    task_dict = task.dict()
    task_dict["created_at"] = datetime.utcnow()
    
    # If no estimated_minutes provided, use AI estimator
    if not task_dict.get("estimated_minutes") or task_dict["estimated_minutes"] == 0:
        print(f"🤖 No time estimate provided. Using AI to estimate time for: {task_dict['description']}")
        try:
            estimated_minutes = estimate_time(task_dict["description"])
            task_dict["estimated_minutes"] = estimated_minutes
            print(f"✅ AI successfully estimated {estimated_minutes} minutes for task: {task_dict['description'][:50]}")
            print(f"🤖 AI estimation complete - using OpenRouter")
        except Exception as e:
            print(f"❌ Error with AI estimation: {str(e)}")
            task_dict["estimated_minutes"] = 30  # Default to 30 minutes
            print("⚡ Using fallback value: 30 minutes")
    
    # Set default due_date to one day from now if not provided
    if not task_dict.get("due_date"):
        task_dict["due_date"] = datetime.utcnow() + dt.timedelta(days=1)
    
    # Optionally associate tasks with the current user
    # task_dict["user_id"] = current_user["_id"]
    
    result = db.tasks.insert_one(task_dict)
    
    # Create a response object with JSON serializable values
    response_dict = {
        "id": str(result.inserted_id),
        "description": task_dict["description"],
        "completed": task_dict["completed"],
        "estimated_minutes": task_dict["estimated_minutes"],
        "created_at": task_dict["created_at"].isoformat()
    }
    
    # Add due_date if available
    if "due_date" in task_dict:
        response_dict["due_date"] = task_dict["due_date"].isoformat()
        
    return response_dict

@app.patch("/tasks/{task_id}")
async def toggle_task(task_id: str, current_user: dict = Depends(get_current_user)):
    task = db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Optional user check
    # if "user_id" in task and str(task["user_id"]) != str(current_user["_id"]):
    #     raise HTTPException(status_code=403, detail="Not authorized to update this task")

    db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed": not task.get("completed", False)}})
    return {"message": "Task updated"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    # Optional task ownership check
    # task = db.tasks.find_one({"_id": ObjectId(task_id)})
    # if not task:
    #     raise HTTPException(status_code=404, detail="Task not found")
    # if "user_id" in task and str(task["user_id"]) != str(current_user["_id"]):
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    
    db.tasks.delete_one({"_id": ObjectId(task_id)})
    return {"message": "Task deleted"}
