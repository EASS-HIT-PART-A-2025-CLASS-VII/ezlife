from fastapi import FastAPI, HTTPException, Depends, Form, Path
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from models import Task, TaskBreakdown, User
from db import get_db
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to get database connection
try:
    db = get_db()
    logger.info("✅ Database connection established successfully via db module.")
except ConnectionFailure as e:
    logger.error(f"❌ CRITICAL: Failed to connect to any MongoDB instance (Atlas or local). Application cannot start.")
    logger.error(f"Error details: {str(e)}")
    raise
except Exception as e:
    logger.error(f"❌ CRITICAL: An unexpected error occurred during database initialization: {str(e)}")
    raise

if db is None:
    logger.error("❌ CRITICAL: Database object is None after setup. Application cannot start.")
    raise ConnectionFailure("Database object is None after setup.")

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
    try:
        test_email = "test@test.com"
        test_password = "12345678"
        if not db.users.find_one({"email": test_email}):
            hashed_password = hash_password(test_password)
            db.users.insert_one({"email": test_email, "password": hashed_password})
            print(f"✅ Created test user: {test_email}")
    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")

# Create test task function
def create_test_task():
    try:
        if db.tasks.count_documents({}) == 0:
            task = {
                "description": "Welcome to EZlife! This is a sample task.",
                "completed": False,
                "created_at": datetime.utcnow()
            }
            db.tasks.insert_one(task)
            print("✅ Created test task")
    except Exception as e:
        print(f"❌ Error creating test task: {str(e)}")

# Create test user and task on startup
create_test_user()
create_test_task()

# Define the URL for the new task estimation service
TASK_ESTIMATION_SERVICE_URL = os.getenv("TASK_ESTIMATION_SERVICE_URL", "http://localhost:8001")

async def get_ai_estimation_with_breakdown(description: str, days_per_week: int, hours_per_day: float):
    """Calls the task-estimation-service to get an AI-based estimate and breakdown."""
    endpoint = f"{TASK_ESTIMATION_SERVICE_URL}/estimate_time"
    payload = {
        "description": description,
        "days_per_week": days_per_week,
        "hours_per_day": hours_per_day
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout
            logging.info(f"Calling task-estimation-service: {endpoint} with payload: {description[:30]}...")
            response = await client.post(endpoint, json=payload)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            data = response.json()
            logging.info(f"Received response from task-estimation-service: {data}")
            return data.get("estimated_minutes"), data.get("breakdown")
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error calling task-estimation-service: {e.response.status_code} - {e.response.text}")
        detail = "Service request failed."
        try:
            error_data = e.response.json()
            detail = error_data.get("detail", detail)
        except Exception:
            pass
        if 400 <= e.response.status_code < 500:
            logging.warning(f"Client error from estimation service: {detail}")
        else:
            logging.error(f"Server error from estimation service: {detail}")
        return None, None
    except httpx.RequestError as e:
        logging.error(f"Request error calling task-estimation-service: {str(e)}")
        return None, None
    except Exception as e:
        logging.error(f"Unexpected error calling task-estimation-service: {str(e)}", exc_info=True)
        return None, None

async def health_check_external():
    """Checks the health of the task-estimation-service."""
    endpoint = f"{TASK_ESTIMATION_SERVICE_URL}/health"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logging.info(f"Checking health of task-estimation-service: {endpoint}")
            response = await client.get(endpoint)
            response.raise_for_status()
            service_status = response.json()
            logging.info(f"Task-estimation-service health: {service_status}")
            return service_status
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error during task-estimation-service health check: {e.response.status_code} - {e.response.text}")
        return {"status": "unhealthy", "reason": "HTTP error", "detail": e.response.text, "service_url": endpoint}
    except httpx.RequestError as e:
        logging.error(f"Request error during task-estimation-service health check: {str(e)}")
        return {"status": "unhealthy", "reason": "Request error", "detail": str(e), "service_url": endpoint}
    except Exception as e:
        logging.error(f"Unexpected error during task-estimation-service health check: {str(e)}", exc_info=True)
        return {"status": "unhealthy", "reason": "Unexpected error", "detail": str(e), "service_url": endpoint}

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
                "created_at": task.get("created_at", datetime.utcnow()).isoformat() if "created_at" in task else None,
                "days_per_week": task.get("days_per_week", 5),
                "hours_per_day": task.get("hours_per_day", 4),
                "progress": task.get("progress", 0)
            }
            
            if "due_date" in task:
                task_item["due_date"] = task["due_date"].isoformat()
            if "breakdown" in task and task["breakdown"]:
                for item in task["breakdown"]:
                    if "completed" not in item:
                        item["completed"] = False
                task_item["breakdown"] = task["breakdown"]
            
            task_list.append(task_item)
            
        return task_list
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

@app.post("/tasks")
async def create_task(task: Task, current_user: dict = Depends(get_current_user)):
    task_dict = task.dict()
    task_dict["created_at"] = datetime.utcnow()
    
    days_per_week = task_dict.get("days_per_week")
    hours_per_day = task_dict.get("hours_per_day")

    try:
        estimated_minutes, breakdown = await get_ai_estimation_with_breakdown(
            task_dict["description"],
            days_per_week,
            hours_per_day
        )
        
        task_dict["estimated_minutes"] = estimated_minutes if estimated_minutes is not None else 60
        task_dict["breakdown"] = breakdown if breakdown is not None else None

        if estimated_minutes is not None:
            print(f"✅ Estimation successful: {estimated_minutes} minutes for task: {task_dict['description'][:50]}")
            if breakdown:
                print(f"✅ Breakdown received with {len(breakdown)} days.")
        else:
            print(f"⚠️ Estimation service did not return minutes. Check service logs.")

    except Exception as e:
        print(f"❌ Unexpected error during task estimation: {e}. Using default estimate.")
        task_dict["estimated_minutes"] = 60
        task_dict["breakdown"] = None

    if not task_dict.get("due_date"):
        task_dict["due_date"] = datetime.utcnow() + timedelta(days=1)
    
    result = db.tasks.insert_one(task_dict)
    response_dict = {
        "id": str(result.inserted_id),
        "description": task_dict["description"],
        "completed": task_dict["completed"],
        "estimated_minutes": task_dict["estimated_minutes"],
        "created_at": task_dict["created_at"].isoformat(),
        "days_per_week": task_dict.get("days_per_week", 5),
        "hours_per_day": task_dict.get("hours_per_day", 4),
        "progress": task_dict.get("progress", 0)
    }
    
    if "breakdown" in task_dict and task_dict["breakdown"]:
        response_dict["breakdown"] = task_dict["breakdown"]
    
    if "due_date" in task_dict:
        response_dict["due_date"] = task_dict["due_date"].isoformat()
        
    return response_dict

@app.patch("/tasks/{task_id}")
async def toggle_task(task_id: str, current_user: dict = Depends(get_current_user)):
    task = db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed": not task.get("completed", False)}})
    return {"message": "Task updated"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    db.tasks.delete_one({"_id": ObjectId(task_id)})
    return {"message": "Task deleted"}

@app.patch("/tasks/{task_id}/breakdown")
async def update_task_breakdown(task_id: str, breakdown_data: dict, current_user: dict = Depends(get_current_user)):
    try:
        tasks_collection = db.tasks
        
        print(f"Updating task {task_id} with breakdown data: {breakdown_data}")
        
        task = tasks_collection.find_one({"_id": ObjectId(task_id)})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        breakdown = breakdown_data.get("breakdown")
        progress = breakdown_data.get("progress")
        
        print(f"✅ Received breakdown with {len(breakdown) if breakdown else 0} days and progress {progress}%")
        
        update_data = {}
        if breakdown is not None:
            update_data["breakdown"] = breakdown
        if progress is not None:
            update_data["progress"] = progress
            
        print(f"✅ Updating task with data: {update_data}")
        
        tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )
        
        updated_task = tasks_collection.find_one({"_id": ObjectId(task_id)})
        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found after update")
        
        updated_task["_id"] = str(updated_task["_id"])
        
        return updated_task
        
    except Exception as e:
        print(f"Error updating task breakdown: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating task breakdown: {str(e)}")
