"""
Test the task API endpoints
"""
import requests
import json
from datetime import datetime, timedelta

# Base URL for backend API
API_URL = "http://localhost:8000"

def test_create_task():
    """Test creating a task with breakdown"""
    # Task data with breakdown parameters
    task_data = {
        "description": "Create a mobile-responsive landing page for a SaaS product",
        "completed": False,
        "days_per_week": 5,
        "hours_per_day": 2.5,
        "due_date": (datetime.now() + timedelta(days=7)).isoformat()
    }
    
    print(f"Creating task: {task_data['description']}")
    print(f"Parameters: {task_data['days_per_week']} days/week, {task_data['hours_per_day']} hours/day")
    
    # Make API request
    try:
        response = requests.post(f"{API_URL}/tasks", json=task_data)
        
        print(f"\nResponse status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Task created with ID: {result.get('id')}")
            print(f"Estimated minutes: {result.get('estimated_minutes')}")
            
            # Check if breakdown was generated
            breakdown = result.get('breakdown', [])
            print(f"Generated breakdown with {len(breakdown)} days")
            
            # Display breakdown if available
            if breakdown:
                print("\nTask Breakdown:")
                for day in breakdown:
                    print(f"- {day['day']} ({day['date']}): {day['hours']} hours")
                    print(f"  {day['summary'][:80]}..." if len(day['summary']) > 80 else f"  {day['summary']}")
            
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception during API request: {str(e)}")
        return None

if __name__ == "__main__":
    test_create_task()