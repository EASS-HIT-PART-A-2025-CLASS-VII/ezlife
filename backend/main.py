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
from models import Task, TaskBreakdown, User, Activity
from db import get_db
import httpx
from typing import List, Optional

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

logger.info("✅ Database connection will be established per request via dependency injection.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def decode_token(token: str) -> dict:
    """
    Simple token decoder that treats the token as the user's email
    and returns a dict with 'sub' key containing the email
    """
    return {"sub": token}

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    print(f"Authenticating user with token: {token}")
    user = db.users.find_one({"email": token})
    if not user:
        print(f"User not found for token: {token}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    print(f"User authenticated: {user['email']}")
    return user

TASK_ESTIMATION_SERVICE_URL = os.getenv("TASK_ESTIMATION_SERVICE_URL", "http://localhost:8002")

async def get_ai_estimation_with_breakdown(description: str, days_per_week: int, hours_per_day: float):
    """Calls the task-estimation-service to get an AI-based estimate and breakdown."""
    endpoint = f"{TASK_ESTIMATION_SERVICE_URL}/estimate_time"
    payload = {
        "description": description,
        "days_per_week": days_per_week,
        "hours_per_day": hours_per_day
    }
    try:
        print(f"🔄 Calling task estimation service at: {endpoint}")
        print(f"📤 Payload: {payload}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            logging.info(f"Calling task-estimation-service: {endpoint} with payload: {description[:30]}...")
            response = await client.post(endpoint, json=payload)
            
            print(f"📥 Response status: {response.status_code}")
            
            response.raise_for_status() 
            data = response.json()
            logging.info(f"Received response from task-estimation-service: {data}")
            
            print(f"✅ Estimation successful: {data.get('estimated_minutes')} minutes")
            
            return data.get("estimated_minutes"), data.get("breakdown")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
        logging.error(f"HTTP error calling task-estimation-service: {e.response.status_code} - {e.response.text}")
        return None, None
    except httpx.RequestError as e:
        print(f"❌ Request error: {str(e)}")
        logging.error(f"Request error calling task-estimation-service: {str(e)}")
        return None, None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
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
def register_user(email: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    if db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(password)
    db.users.insert_one({"email": email, "password": hashed_password})
    return {"message": "User registered successfully"}

@app.post("/token")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
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
async def get_tasks(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
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
                "created_at": task.get("created_at", datetime.utcnow()).isoformat() if task.get("created_at") is not None else datetime.utcnow().isoformat(),
                "days_per_week": task.get("days_per_week", 5),
                "hours_per_day": task.get("hours_per_day", 4),
                "progress": task.get("progress", 0)
            }
            
            if "due_date" in task and task["due_date"] is not None:
                task_item["due_date"] = task["due_date"].isoformat()
            if "breakdown" in task and task["breakdown"]:
                if isinstance(task["breakdown"], list) and len(task["breakdown"]) > 0:
                    first_item = task["breakdown"][0]
                    if isinstance(first_item, dict) and "day" in first_item and "step" not in first_item:
                        task_item["breakdown"] = transform_breakdown_for_frontend(
                            task["breakdown"], 
                            task.get("estimated_minutes", 60)
                        )
                    else:
                        for item in task["breakdown"]:
                            if isinstance(item, dict) and "completed" not in item:
                                item["completed"] = False
                        task_item["breakdown"] = task["breakdown"]
                else:
                    task_item["breakdown"] = task["breakdown"]
            
            task_list.append(task_item)
            
        return task_list
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

@app.post("/tasks")
async def create_task(task: Task, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    print(f"🚀 Starting task creation for: {task.description}")
    print(f"📝 Received task data: {task.dict()}")
    
    task_dict = task.dict()
    task_dict["created_at"] = datetime.utcnow()
    
    days_per_week = task_dict.get("days_per_week") or 5  # Default to 5 days per week
    hours_per_day = task_dict.get("hours_per_day") or 2.0  # Default to 2 hours per day

    print(f"📊 Task details: days_per_week={days_per_week}, hours_per_day={hours_per_day}")

    try:
        print(f"🔮 About to call AI estimation...")
        estimated_minutes, breakdown = await get_ai_estimation_with_breakdown(
            task_dict["description"],
            days_per_week,
            hours_per_day
        )
        print(f"🔮 AI estimation returned: minutes={estimated_minutes}, breakdown={'Yes' if breakdown else 'No'}")
        
        task_dict["estimated_minutes"] = estimated_minutes if estimated_minutes is not None else 60
        
        if breakdown:
            task_dict["breakdown"] = transform_breakdown_for_frontend(breakdown, estimated_minutes or 60)
        else:
            task_dict["breakdown"] = None

        if estimated_minutes is not None:
            print(f"✅ Estimation successful: {estimated_minutes} minutes for task: {task_dict['description'][:50]}")
            if breakdown:
                print(f"✅ Breakdown received with {len(breakdown)} days.")
                print(f"✅ Breakdown transformed for frontend: {len(task_dict['breakdown'])} steps.")
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
        "created_at": task_dict["created_at"].isoformat() if task_dict["created_at"] is not None else datetime.utcnow().isoformat(),
        "days_per_week": task_dict.get("days_per_week", 5),
        "hours_per_day": task_dict.get("hours_per_day", 4),
        "progress": task_dict.get("progress", 0)
    }
    
    if "breakdown" in task_dict and task_dict["breakdown"]:
        response_dict["breakdown"] = task_dict["breakdown"]
    
    if "due_date" in task_dict and task_dict["due_date"] is not None:
        response_dict["due_date"] = task_dict["due_date"].isoformat()
        
    return response_dict

@app.patch("/tasks/{task_id}")
async def toggle_task(task_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    task = db.tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed": not task.get("completed", False)}})
    return {"message": "Task updated"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    db.tasks.delete_one({"_id": ObjectId(task_id)})
    return {"message": "Task deleted"}

@app.patch("/tasks/{task_id}/breakdown")
async def update_task_breakdown(task_id: str, breakdown_data: dict, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
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

# Activity endpoints
@app.post("/activities/")
async def create_activity(activity: Activity, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        user_id = decode_token(token)["sub"]
        activity_dict = activity.dict()
        activity_dict["user_id"] = user_id
        
        if "id" in activity_dict and activity_dict["id"]:
            activity_dict["_id"] = ObjectId(activity_dict["id"])
            del activity_dict["id"]
        else:
            del activity_dict["id"]
            
        result = db.activities.insert_one(activity_dict)
        return {"id": str(result.inserted_id), **activity.dict()}
    except Exception as e:
        logger.error(f"Error creating activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating activity: {str(e)}")

@app.get("/activities/")
async def get_activities(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        user_id = decode_token(token)["sub"]
        activities = list(db.activities.find({"user_id": user_id}))
        
        for activity in activities:
            activity["id"] = str(activity["_id"])
            del activity["_id"]
            
        return activities
    except Exception as e:
        logger.error(f"Error fetching activities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")

@app.put("/activities/{activity_id}")
async def update_activity(activity_id: str, activity: Activity, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        user_id = decode_token(token)["sub"]
        activity_dict = activity.dict(exclude={'id'})
        activity_dict["user_id"] = user_id
        
        result = db.activities.update_one(
            {"_id": ObjectId(activity_id), "user_id": user_id},
            {"$set": activity_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        updated_activity = db.activities.find_one({"_id": ObjectId(activity_id), "user_id": user_id})
        if updated_activity:
            updated_activity["id"] = str(updated_activity["_id"])
            del updated_activity["_id"]
            return updated_activity
        else:
            raise HTTPException(status_code=404, detail="Activity not found after update")
    except Exception as e:
        logger.error(f"Error updating activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating activity: {str(e)}")

@app.delete("/activities/{activity_id}")
async def delete_activity(activity_id: str, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        user_id = decode_token(token)["sub"]
        result = db.activities.delete_one({"_id": ObjectId(activity_id), "user_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        return {"message": "Activity deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting activity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting activity: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "EZlife Backend is running"}

def transform_breakdown_for_frontend(breakdown_data, total_minutes):
    """
    Transform breakdown data from AI service format to frontend format.
    
    AI service format: 
    - [{"step": "...", "percentage": ..., "summary": "..."}] (new step-based format with percentages)
    - [{"day": "...", "hours": ..., "summary": "..."}] (old day-based format with hours)
    Frontend format: [{"step": "...", "summary": "...", "percentage": "..."}]
    """
    if not breakdown_data or not isinstance(breakdown_data, list):
        return []
    
    # Handle nested array format: [[{...}]] -> [{...}]
    if len(breakdown_data) == 1 and isinstance(breakdown_data[0], list):
        breakdown_data = breakdown_data[0]
    
    if not breakdown_data:
        return []
    
    transformed = []
    total_hours = total_minutes / 60 if total_minutes > 0 else 1
    
    print(f"🔧 Transforming breakdown: {len(breakdown_data)} items, total_hours: {total_hours}")
    
    for i, item in enumerate(breakdown_data, 1):
        if isinstance(item, dict):
            step_name = item.get("step", f"Step {i}")
            if "day" in item and step_name == f"Step {i}":
                step_name = item["day"]
            
            summary = item.get("summary", "Task work")
            
            if "percentage" in item:
                percentage = item.get("percentage", 0)
                print(f"🔧 Item {i}: step={step_name}, percentage={percentage}% (from AI), summary={summary[:50]}...")
            else:
                hours = item.get("hours", 0)
                percentage = round((hours / total_hours) * 100) if total_hours > 0 else 0
                print(f"🔧 Item {i}: step={step_name}, hours={hours}, calculated percentage={percentage}%, summary={summary[:50]}...")
            
            transformed.append({
                "step": step_name,
                "summary": summary,
                "percentage": percentage
            })
    
    print(f"🔧 Transformed result: {transformed}")
    return transformed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
