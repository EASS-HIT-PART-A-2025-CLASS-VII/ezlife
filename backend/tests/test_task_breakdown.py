"""
Test script for task breakdown functionality
This script tests the task creation and breakdown updating functionality
"""
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "12345678"

def login():
    """Get auth token for testing"""
    print("\n📝 Logging in to get auth token...")
    try:
        response = requests.post(
            f"http://localhost:8001/token",
            data={
                "username": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ Login successful, token: {token[:10]}...")
            return token
        else:
            print(f"❌ Login failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None

def test_create_task_with_breakdown(token):
    """Test creating a task with days_per_week and hours_per_day"""
    print("\n📝 Creating a test task with breakdown parameters...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a task with days_per_week and hours_per_day but without estimated_minutes
    task_data = {
        "description": "Test task with breakdown " + datetime.now().strftime("%H:%M:%S"),
        "completed": False,
        "days_per_week": 5,
        "hours_per_day": 2.5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tasks",
            json=task_data,
            headers=headers
        )
        
        if response.status_code == 200:
            task = response.json()
            print(f"✅ Task created successfully with ID: {task.get('id')}")
            print(f"🔍 Estimated minutes: {task.get('estimated_minutes')}")
            
            # Check if breakdown was generated
            breakdown = task.get('breakdown', [])
            if breakdown:
                print(f"✅ Task breakdown generated with {len(breakdown)} days")
                print(f"📅 First day: {breakdown[0].get('day')} - {breakdown[0].get('date')}")
                print(f"📝 Summary: {breakdown[0].get('summary')[:50]}...")
                return task
            else:
                print("❌ Task breakdown was not generated")
                return task
        else:
            print(f"❌ Failed to create task: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating task: {str(e)}")
        return None

def test_update_task_breakdown(token, task):
    """Test updating a task's breakdown completion status"""
    if not task or 'id' not in task or 'breakdown' not in task or not task['breakdown']:
        print("❌ Cannot test update: Missing task ID or breakdown")
        return False
    
    task_id = task['id']
    breakdown = task['breakdown']
    print(f"\n📝 Updating breakdown for task {task_id}...")
    
    # Mark the first day as completed
    breakdown[0]['completed'] = True
    
    # Calculate progress
    total_days = len(breakdown)
    completed_days = sum(1 for day in breakdown if day.get('completed'))
    progress = (completed_days / total_days) * 100 if total_days > 0 else 0
    
    update_data = {
        "breakdown": breakdown,
        "progress": progress
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.patch(
            f"{BASE_URL}/tasks/{task_id}/breakdown",
            json=update_data,
            headers=headers
        )
        
        if response.status_code == 200:
            updated_task = response.json()
            print(f"✅ Task breakdown updated successfully")
            print(f"📊 New progress: {updated_task.get('progress')}%")
            return True
        else:
            print(f"❌ Failed to update task breakdown: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating task breakdown: {str(e)}")
        return False

def test_get_tasks(token):
    """Test retrieving all tasks"""
    print("\n📝 Retrieving all tasks...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/tasks",
            headers=headers
        )
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Retrieved {len(tasks)} tasks")
            
            # Print details of tasks with breakdown
            tasks_with_breakdown = [t for t in tasks if t.get('breakdown')]
            print(f"📊 Found {len(tasks_with_breakdown)} tasks with breakdown")
            
            for i, task in enumerate(tasks_with_breakdown[:3]):  # Show details for up to 3 tasks
                print(f"\n🔍 Task {i+1}: {task.get('description')}")
                print(f"⏱️ Estimated time: {task.get('estimated_minutes')} minutes")
                print(f"📅 Days per week: {task.get('days_per_week')}")
                print(f"⏰ Hours per day: {task.get('hours_per_day')}")
                print(f"📊 Progress: {task.get('progress')}%")
                
                breakdown = task.get('breakdown', [])
                print(f"📑 Breakdown: {len(breakdown)} days")
                
            return tasks
        else:
            print(f"❌ Failed to retrieve tasks: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error retrieving tasks: {str(e)}")
        return []

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TASK BREAKDOWN TEST SCRIPT")
    print("=" * 50)
    
    # Login to get token
    token = login()
    if not token:
        print("❌ Cannot proceed without authentication token")
        exit(1)
    
    # Create a task with breakdown
    created_task = test_create_task_with_breakdown(token)
    
    # Update the task breakdown
    if created_task:
        updated = test_update_task_breakdown(token, created_task)
    
    # Get all tasks to verify
    tasks = test_get_tasks(token)
    
    print("\n" + "=" * 50)
    print("🏁 TEST COMPLETED")
    print("=" * 50)
