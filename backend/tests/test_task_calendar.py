# Test task breakdown and calendar functionality
import os
import requests
import json
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

load_dotenv()

# Config
BASE_URL = "http://localhost:8000"  # Backend API URL
AUTH_URL = "http://localhost:8001"  # Auth service URL

print("🧪 Testing task breakdown and calendar functionality...")

# Step 1: Login to get an auth token
print("\nStep 1: Logging in to get auth token...")
try:
    login_response = requests.post(
        f"{BASE_URL}/token",
        data={"username": "test@test.com", "password": "12345678"}
    )
    login_response.raise_for_status()
    token = login_response.json()["access_token"]
    print(f"✅ Authentication successful, received token: {token[:10]}...")
except Exception as e:
    print(f"❌ Login failed: {str(e)}")
    if hasattr(login_response, 'text'):
        print(f"Response: {login_response.text}")
    exit(1)

# Set auth header for all subsequent requests
headers = {"Authorization": f"Bearer {token}"}

# Step 2: Create a task with breakdown
print("\nStep 2: Creating a task with breakdown...")

task_data = {
    "description": "Build a REST API for a mobile app",
    "completed": False,
    "days_per_week": 3,  # Work 3 days per week
    "hours_per_day": 4,  # 4 hours per day
    "due_date": (datetime.now() + timedelta(days=10)).isoformat()
}

try:
    create_response = requests.post(
        f"{BASE_URL}/tasks",
        headers=headers,
        json=task_data
    )
    create_response.raise_for_status()
    task = create_response.json()
    task_id = task["id"]
    print(f"✅ Task created with ID: {task_id}")
    
    # Check if breakdown was generated
    if "breakdown" in task and task["breakdown"]:
        print(f"✅ Task breakdown generated with {len(task['breakdown'])} days")
        
        # Print breakdown details
        print("\nBreakdown details:")
        for day in task["breakdown"]:
            print(f"- {day['day']} ({day['date']}): {day['hours']} hours - {day['summary'][:50]}...")
    else:
        print("❌ Task breakdown was not generated")
except Exception as e:
    print(f"❌ Task creation failed: {str(e)}")
    if hasattr(create_response, 'text'):
        print(f"Response: {create_response.text}")
    exit(1)

# Step 3: Update task breakdown (mark a day as completed)
print("\nStep 3: Marking a day as completed...")

if "breakdown" in task and task["breakdown"]:
    # Mark the first day as completed
    updated_breakdown = task["breakdown"]
    updated_breakdown[0]["completed"] = True
    
    # Calculate new progress
    total_days = len(updated_breakdown)
    completed_days = sum(1 for day in updated_breakdown if day.get("completed"))
    progress = (completed_days / total_days) * 100
    
    update_data = {
        "breakdown": updated_breakdown,
        "progress": progress
    }
    
    try:
        update_response = requests.patch(
            f"{BASE_URL}/tasks/{task_id}/breakdown",
            headers=headers,
            json=update_data
        )
        update_response.raise_for_status()
        updated_task = update_response.json()
        print(f"✅ Task updated successfully")
        print(f"✅ New progress: {progress:.1f}%")
    except Exception as e:
        print(f"❌ Task update failed: {str(e)}")
        if hasattr(update_response, 'text'):
            print(f"Response: {update_response.text}")
            
# Step 4: Verify the updated task
print("\nStep 4: Verifying updated task...")
try:
    get_response = requests.get(
        f"{BASE_URL}/tasks",
        headers=headers
    )
    get_response.raise_for_status()
    tasks = get_response.json()
    
    found_task = None
    for t in tasks:
        if t["id"] == task_id:
            found_task = t
            break
            
    if found_task:
        print(f"✅ Found task: {found_task['description']}")
        if "breakdown" in found_task:
            completed_days = sum(1 for day in found_task['breakdown'] if day.get("completed"))
            print(f"✅ Progress: {found_task.get('progress', 0):.1f}% ({completed_days}/{len(found_task['breakdown'])} days completed)")
    else:
        print("❌ Task not found")
except Exception as e:
    print(f"❌ Error retrieving tasks: {str(e)}")

print("\n🎉 Test complete!")
